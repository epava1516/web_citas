"""Actual PostgreSQL semantics for JSON proof and generated bilingual search."""
import itertools

import pytest
from django.contrib.postgres.search import SearchVector
from django.db import connection
from django.db.models import Case, CharField, JSONField, Value, When
from django.utils import timezone
from django.utils.translation import override
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from apps.listings.sql_publication import JSONChoicesProof
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_json_strict_path_preserves_shape_and_exact_string_membership():
    assert connection.vendor == 'postgresql'
    atoms = ['es', 'en', 'invalid', '', 1, True, None, [], ['es'], {'es': True}]
    values = atoms + [[]] + [[a] for a in atoms] + [list(v) for v in itertools.product(atoms, repeat=2)]
    query = Revision.objects.all().query
    compiler = query.get_compiler(connection=connection)
    for choices in [[], ['es', 'en']]:
        for value in values:
            expected = isinstance(value, list) and all(type(v) is str and v in choices for v in value)
            results = []
            for json_path in [False, True]:
                expression = JSONChoicesProof(Value(value, output_field=JSONField()), choices, json_path=json_path)
                sql, params = compiler.compile(expression.resolve_expression(query))
                with connection.cursor() as cursor:
                    cursor.execute('SELECT ' + sql, params)
                    results.append(cursor.fetchone()[0] is True)
            assert results == [expected, expected], (value, choices, results)


def original_vector():
    # Frozen pre-change expression, independently of the new shared builder.
    primary = Case(When(content_language='en', then=Value('english')),
                   default=Value('spanish'), output_field=CharField())
    alternative = Case(When(content_language='en', then=Value('spanish')),
                       default=Value('english'), output_field=CharField())
    return (SearchVector('title', weight='A', config=primary)
            + SearchVector('description', weight='B', config=primary)
            + SearchVector('description_alternative', weight='B', config=alternative))


def test_generated_search_tracks_mutations_and_preserves_population_pages(request, monkeypatch, record_property):
    client = request.getfixturevalue('directory')
    populate(50)
    assert projection.supported()
    ordered = native_ids(discovery.candidates({}))
    target = discovery.candidates({}).get(pk=ordered[25])
    assert target.pk not in ordered[:24]
    revision = target.approved_revision
    # QuerySet.update, model.save and bulk_update must all update generated data.
    Revision.objects.filter(pk=revision.pk).update(
        title='Azafata jardín walking', description='Garden running bailar evento.',
        description_alternative='Walking jardín singular.', content_language='es')
    revision.refresh_from_db()
    revision.content_language = 'en'
    revision.save(update_fields=['content_language'])
    revision.description_alternative = 'Bailando jardín único.'
    Revision.objects.bulk_update([revision], ['description_alternative'])
    values = list(Revision.objects.annotate(original=original_vector()).values_list('search_document', 'original'))
    assert all(stored == computed for stored, computed in values)
    observations = []
    for term in ['photography', 'synthetic', 'jardín', 'walk', 'bailar', '"garden running"', 'garden OR fotografía', '-garden photography', '']:
        data = {'q': term} if term else {}
        old_query = discovery.candidates(data, stored_search=False)
        query = discovery.candidates(data)
        assert list(query.values_list('pk', 'relevance') if term else query.values_list('pk')) == list(
            old_query.values_list('pk', 'relevance') if term else old_query.values_list('pk'))
        expected = native_ids(old_query)
        actual = projection.ProjectedPublication(query, sql=True).visible_ids(query)
        assert actual == expected
        pages = sorted({1, max(1, (len(expected)+23)//24)})
        for lang in ['es', 'en']:
            with override(lang):
                for number in pages:
                    page = projection.projected_page(query, number)
                    assert page.paginator.count == len(expected)
                    assert [row.pk for row in page] == expected[(number-1)*24:number*24]
        observations.append({'query_case': len(observations), 'eligible': len(expected), 'pages': pages})
    # Same HTTP body, count, ranking and route under the independently calculated path.
    current = client.get('/es/', {'q': 'photography'})
    original = discovery.candidates
    with monkeypatch.context() as patch:
        patch.setattr(discovery, 'candidates', lambda data: original(data, stored_search=False))
        computed = client.get('/es/', {'q': 'photography'})
    assert current.content == computed.content
    assert current.wsgi_request._publication_route == computed.wsgi_request._publication_route
    # A stored text match never certifies authority. Revoke outside the first page.
    target.person.consent_revoked_at = timezone.now()
    target.person.save(update_fields=['consent_revoked_at'])
    for term in ['', 'garden']:
        data = {'q': term} if term else {}
        query = discovery.candidates(data)
        expected = native_ids(discovery.candidates(data, stored_search=False))
        assert target.pk not in expected
        assert projection.ProjectedPublication(query, sql=True).visible_ids(query) == expected
    record_property('search_document_equivalence', {'candidates': 50, 'negative_outside_first_page': True,
        'postgres_generated_matches_original_expression_all_rows': True,
        'write_paths': ['QuerySet.update', 'Model.save(update_fields)', 'bulk_update'], 'cases': observations})
