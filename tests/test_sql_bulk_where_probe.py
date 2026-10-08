"""Isolated access-shape experiment; never bypasses the public authority guard."""
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection, transaction
from django.db.models import BooleanField, Case, Q, Value, When
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.core.models import Person
from apps.listings import discovery, projected_publication as projection, sql_publication as proof
from apps.listings.models import Listing, Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('BULK_WHERE_PROBE_OUTPUT'), reason='Explicit isolated SQL prototype only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_bulk_positive_membership_shape(request, monkeypatch, record_property, variant):
    request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        revisions = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, revision in enumerate(revisions):
            suffix = alpha(index)
            revision.description += ' ' + suffix
            if revision.description_alternative:
                revision.description_alternative += ' ' + suffix
            revision.telegram = 'bench' + suffix
        Revision.objects.bulk_update(revisions, ['description', 'description_alternative', 'telegram'], batch_size=250)
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert projection.supported()
    digest = projection.definitions_digest()
    document = proof.submissions.current_publishing_document()
    condition = proof.authority_proof(document, bulk=True) & proof.content_proof(bulk=True)
    compiled = {}
    for family, data in [('listing', {}), ('search', {'q': 'photography'})]:
        query = discovery.candidates(data)
        ordering = proof.compact_order(query, 1)
        positive = query.filter(condition).order_by().values('pk')
        for mode, predicate in [('case', condition), ('membership', Q(pk__in=positive))]:
            selected = query.annotate(_sql_publication_positive=Case(
                When(predicate, then=Value(True)), default=Value(False), output_field=BooleanField()))
            captured = []
            with monkeypatch.context() as patch:
                patch.setattr(proof, 'read_publication_values', lambda read: captured.append(read) or [])
                proof.read_ordered_scalar_population(selected, ordering)
            assert len(captured) == 1
            compiled[family, mode] = captured[0].sql, captured[0].params

    def read(family, mode, *, read_only=True):
        sql, params = compiled[family, mode]
        with transaction.atomic(), connection.cursor() as cursor:
            if read_only:
                cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('SET LOCAL jit=off')
            start = time.perf_counter()
            cursor.execute(sql, params)
            executed = time.perf_counter() - start
            start = time.perf_counter()
            rows = cursor.fetchall()
            fetched = time.perf_counter() - start
        return rows, {'execute_seconds': executed, 'fetch_seconds': fetched,
                      'read_seconds': executed + fetched, 'rows_returned': len(rows)}

    expected = {f: read(f, 'case')[0] for f in ['listing', 'search']}
    for family, data in [('listing', {}), ('search', {'q': 'photography'})]:
        current = proof.SQLPublication(discovery.candidates(data))
        assert [tuple(row[k] for k in ['pk', 'approved_revision_id', '_sql_publication_positive'])
                for row in current.rows] == expected[family]
        assert len(expected[family]) == 10000 and all(row[2] for row in expected[family])
        assert read(family, 'membership')[0] == expected[family]
    target = Listing.objects.get(pk=expected['listing'][25][0])
    assert str(target.pk) not in [row[0] for row in expected['listing'][:24]]
    mutations = [(Revision, target.approved_revision_id, {'description': 'www.example.invalid'}),
                 (Revision, target.approved_revision_id, {'description': 'Texto válido 😀'}),
                 (Person, target.person_id, {'consent_revoked_at': timezone.now()})]
    for model, pk, values in mutations:
        with transaction.atomic():
            model.objects.filter(pk=pk).update(**values)
            for family in ['listing', 'search']:
                old = read(family, 'case', read_only=False)[0]
                new = read(family, 'membership', read_only=False)[0]
                assert old == new and len(new) == 10000
                assert sum(row[2] for row in new) == 9999
            transaction.set_rollback(True)
        assert read('listing', 'membership')[0] == expected['listing']
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    for family in ['listing', 'search']:
        for mode in ['case', 'membership']:
            assert read(family, mode)[0] == expected[family]
    before = stats_snapshot()
    samples = []
    for pair in range(8):
        for family in ['listing', 'search']:
            for mode in (['case', 'membership'] if pair % 2 == 0 else ['membership', 'case']):
                rows, sample = read(family, mode)
                assert rows == expected[family]
                samples.append({'pair': pair, 'family': family, 'mode': mode, **sample})
    after = stats_snapshot()
    plans = []
    for (family, mode), (sql, params) in compiled.items():
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('SET LOCAL jit=off')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, params)
            plans.append({'family': family, 'mode': mode, 'query_pattern': query_pattern(sql),
                          'plan': redact_plan(cursor.fetchone()[0])})
    medians = {f: {m: statistics.median(s['read_seconds'] for s in samples
                                       if s['family'] == f and s['mode'] == m)
                   for m in ['case', 'membership']} for f in ['listing', 'search']}
    deltas = [sum(next(s['read_seconds'] for s in samples if s['pair'] == pair and s['family'] == f and s['mode'] == 'case')
                  - next(s['read_seconds'] for s in samples if s['pair'] == pair and s['family'] == f and s['mode'] == 'membership')
                  for f in ['listing', 'search']) / 2 for pair in range(8)]
    reference = statistics.mean(v['case'] for v in medians.values())
    effect = (statistics.median(deltas) >= max(.05, .20 * reference) and sum(d > 0 for d in deltas) >= 6
              and all(v['membership'] - v['case'] <= max(.025, .10 * v['case']) for v in medians.values()))
    assert projection.definitions_digest() == digest and projection.supported()
    report = {'variant': variant, 'stage': 'complete', 'source_fingerprint': digest,
              'samples': samples, 'medians': medians, 'paired_mean_family_deltas': deltas,
              'material_sql_effect': effect, 'plans': plans, 'statistics_before': before,
              'statistics_after': after, 'statistics_endpoints_equal': before == after,
              'current_complete_vectors_equal': True, 'offpage_writes_and_rollback_equal': True,
              'scope': 'SQL-only access-shape prototype using CURRENT bulk proof and scalar capture/index. Same full candidate query, condition object and snapshot per SELECT; current CASE vs membership in positives evaluated in WHERE. Captures every candidate, unknowns kept, no early paging or public path change. Historical rejected WHERE used nonbulk correlated authority, not this predicate. Eight counterbalanced pairs per listing/search, warmup/ANALYZE outside controls, top four read-only plans after controls. Same schema/params within mode, no forced caches/GC; timers include driver, server, buffering and fetch, not CPU PG. Node rows/times have multiplicity and overlap; not global rows_scanned. Explicit fetch rows_returned per statement only.',
              'not_measured': ['whole HTTP effect/equivalence of prototype', 'validation per rule', 'ORM materialization',
                               'render', 'CPU PostgreSQL', 'rows_affected/scanned', 'common matrix/N2', 'capacity']}
    Path(os.environ['BULK_WHERE_PROBE_OUTPUT'], variant + '.json').write_text(json.dumps(report, indent=2) + '\n')
    record_property('bulk_where_probe', report)
