"""PostgreSQL equivalence of sufficient text predicates, including unknowns."""
import random

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models.expressions import RawSQL

from apps.listings.forms import validate_listing_text
from apps.listings.models import Revision
from apps.listings.sql_publication import PlainTextProof

pytestmark = pytest.mark.django_db(transaction=True)


def test_combined_negative_text_predicate_preserves_legacy_proof_and_native_positive_domain(record_property):
    assert connection.vendor == 'postgresql'
    samples = [None, '', ' ', '\t\r\n', 'hello', 'www.example.invalid', 'WwW.example.invalid',
               'https://example.invalid', 'http://example.invalid', '@user', '+12345678',
               '1234567', '12345678', '1       ', '12 (34)-56', '1234\n5678',
               'Descripción sintética; texto válido.', 'Texto válido 😀', '漢字', '١٢٣٤٥٦٧٨',
               '１２３４５６７８', '\u00a0', '\u2003', 'K', '\u2028', '\u2029',
               '\\', '[', ']', '^', '$', 'foo\nwww.example', 'a'*80, 'a'*81,
               'a'*120, 'a'*121, 'a'*6000, 'a'*6001, ' a ', "()'\";!?.,-\r\n\t"]
    # Explicitly cover every ASCII non-NUL character, combinations of boundary
    # tokens, and deterministic varied strings. NUL cannot be stored as PG text.
    for code in range(1, 128):
        samples.extend([chr(code), 'hello'+chr(code)+'world'])
    tokens = ['a', 'www.', 'WwW.', '@a', ':', '+', '1', '1234567', '12345678', '\n', ' ', '😀']
    samples.extend(a+b for a in tokens for b in tokens)
    rng = random.Random(110)
    alphabet = "abcwW019 éñÜ().!?;,-\n\t@:+\\😀١\u2003"
    samples.extend(''.join(rng.choices(alphabet, k=rng.randrange(0, 100))) for _ in range(512))
    compiler = Revision.objects.all().query.get_compiler(connection=connection)
    positives, unknowns = 0, 0
    for maximum, required in [(80, True), (120, True), (6000, True), (6000, False)]:
        legacy, lp = PlainTextProof(RawSQL('sample', []), maximum, required, legacy=True).as_sql(compiler, connection)
        current, cp = PlainTextProof(RawSQL('sample', []), maximum, required, legacy=False).as_sql(compiler, connection)
        field = forms.CharField(max_length=maximum, required=required)
        for offset in range(0, len(samples), 200):
            chunk = samples[offset:offset+200]
            tuples = ', '.join(['(%s::integer, %s::text)']*len(chunk))
            params = [*lp, *cp]
            for index, value in enumerate(chunk):
                params.extend([index, value])
            with connection.cursor() as cursor:
                cursor.execute(f'SELECT sample_id, {legacy}, {current} FROM (VALUES {tuples}) AS inputs(sample_id, sample)', params)
                rows = cursor.fetchall()
            assert len(rows) == len(chunk)
            for index, old, new in rows:
                assert new is old, (offset+index, maximum, required)
                if new is True:
                    positives += 1
                    # A SQL positive must also pass actual native field cleaning
                    # and contact exclusion. Unknown is never a native rejection.
                    try:
                        validate_listing_text(field.clean(chunk[index]))
                    except ValidationError:
                        pytest.fail('SQL positive failed the native text/field rule')
                else:
                    unknowns += 1
    record_property('text_proof_equivalence', {'samples': len(samples), 'field_variants': 4,
        'positive_evaluations': positives, 'unknown_evaluations': unknowns,
        'legacy_boolean_outputs_exact': True, 'native_positive_domain_checked': True,
        'scope': 'Actual PostgreSQL, independent legacy expression branch, all ASCII non-NUL characters, boundary tokens, Unicode, length/required boundaries and deterministic random strings. Finite adversarial sample, not exhaustive proof over all Unicode strings; unknown still native. No request performance claim or sensitive values exported.'})
