"""Captured population equivalence and paired PostgreSQL preparation/execute/fetch."""
import time
from collections import Counter
from uuid import UUID, uuid4

import pytest
from django.core.exceptions import EmptyResultSet
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Rate, Revision
from apps.listings.uuid_batches import CapturedUUIDBatch
from apps.mediafiles.models import Photo
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def shapes():
    for name in ['categories', 'services', 'travel_areas']:
        field = Revision._meta.get_field(name)
        yield name, field.remote_field.through.objects.all(), [
            'revision_id', field.m2m_reverse_field_name() + '_id']
    yield 'rates', Rate.objects.all(), ['revision_id', 'concept', 'mode', 'amount']
    yield 'photos', Photo.objects.filter(removed_at__isnull=True), [
        'revision_id', 'blob__status', 'comparison_complete']


@pytest.mark.parametrize('count', [100, 1000, 10000])
def test_captured_uuid_batch_pair(request, record_property, count):
    request.getfixturevalue('directory')
    populate(count)
    captured = list(candidates({}).values_list('approved_revision_id', flat=True))
    assert len(captured) == count
    reports = []
    for variant, identifiers in [('population', captured), ('duplicate_and_foreign',
                                  captured + captured[:3] + [uuid4()]), ('empty', [])]:
        expected = {}
        for mode in ['in', 'array']:
            started = time.perf_counter()
            batch = CapturedUUIDBatch(identifiers, mode=mode)
            preparation = time.perf_counter() - started
            for name, base, columns in shapes():
                started = time.perf_counter()
                query = batch.filter(base, 'revision_id').values_list(*columns)
                try:
                    sql, params = query.query.sql_with_params()
                except EmptyResultSet:
                    rows = []
                    compile_seconds = time.perf_counter() - started
                    execute_seconds = fetch_seconds = None
                    parameter_count = 0
                    sql_pattern = 'not_executed_empty_population'
                else:
                    compile_seconds = time.perf_counter() - started
                    parameter_count = len(params)
                    with connection.cursor() as cursor:
                        started = time.perf_counter()
                        cursor.execute(sql, params)
                        execute_seconds = time.perf_counter() - started
                        started = time.perf_counter()
                        rows = cursor.fetchall()
                        fetch_seconds = time.perf_counter() - started
                    sql_pattern = query_pattern(sql)
                key = name
                if mode == 'in':
                    expected[key] = Counter(rows)
                else:
                    assert Counter(rows) == expected[key]
                    assert parameter_count <= 1
                reports.append({'variant': variant, 'mode': mode, 'relation': name,
                    'population': count, 'captured_ids': len(identifiers),
                    'batch_preparation_seconds': preparation,
                    'query_preparation_compile_seconds': compile_seconds,
                    'cursor_execute_seconds': execute_seconds, 'fetchall_seconds': fetch_seconds,
                    'parameter_count': parameter_count, 'query_pattern': sql_pattern,
                    'rows_returned': len(rows) if execute_seconds is not None else 'not_measured',
                    'rows_affected': 'not_measured', 'rows_scanned': 'not_measured'})
    record_property('uuid_batches', reports)
    record_property('scope', 'Paired IN then array, same captured IDs/PG/columns/fixture; raw cursor fetchall fully drained, rows_returned is fetched SQL result rows for each executed SELECT only. Counter equality checks multiplicity, not implicit DB row order. Canonical UUIDs bind in one text parameter cast uuid[]; never interpolate values or persist params. Compilation includes query/field conversion, cursor execute includes client adapter/server/buffering, fetchall excludes ORM construction. Batch preparation is once per mode/variant, repeated in rows for context: do not sum it five times. One sample; caches warmed by IN before array, not causal overhead or 20RPS capacity. No SQL plan/DB CPU/RSS/waits/locks/IO measured. Empty population compiler short circuit has no SQL rows_returned measurement.')


def test_array_request_preserves_native_count_order_body_and_captured_ids(request, monkeypatch):
    client = request.getfixturevalue('directory')
    populate(50)
    assert projection.supported()
    before = projection.definitions_digest()
    native = client.get('/es/')
    captured = list(candidates({}).values_list('approved_revision_id', flat=True))
    # A later live candidate query loses this row; both captured predicates keep
    # the same related records. This probe restores status before HTTP parity.
    listing = candidates({}).last()
    status = listing.status
    listing.status = 'withdrawn'
    listing.save(update_fields=['status'])
    assert len(list(candidates({}))) == 49
    for name, base, columns in shapes():
        left = list(CapturedUUIDBatch(captured).filter(base, 'revision_id').values_list(*columns))
        right = list(CapturedUUIDBatch(captured, mode='array').filter(base, 'revision_id').values_list(*columns))
        assert Counter(left) == Counter(right), name
    listing.status = status
    listing.save(update_fields=['status'])
    monkeypatch.setattr(projection, 'CapturedUUIDBatch', lambda identifiers, **kwargs: CapturedUUIDBatch(identifiers, mode='array'))
    assert projection.definitions_digest() == before and projection.supported()
    for language in ['es', 'en']:
        for params in [{}, {'page': 2}, {'page': 3}, {'q': 'photography'}]:
            with monkeypatch.context() as patch:
                patch.setattr(projection, 'CapturedUUIDBatch',
                              lambda identifiers, **kwargs: CapturedUUIDBatch(identifiers, mode='in'))
                original = client.get(f'/{language}/', params)
            array = client.get(f'/{language}/', params)
            assert array.content == original.content
            assert array.context['page'].paginator.count == original.context['page'].paginator.count
            assert [row.pk for row in array.context['page']] == [row.pk for row in original.context['page']]
            assert array.wsgi_request._publication_route == original.wsgi_request._publication_route
    assert native.status_code == 200
    with pytest.raises(TypeError):
        CapturedUUIDBatch([str(UUID(int=1))], mode='array')
