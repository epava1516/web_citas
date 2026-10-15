"""Scoped preparation restores options and never caches eligibility/results."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation


def test_disabled_binding_does_not_touch_connection(monkeypatch):
    monkeypatch.setattr(public_validation, 'connection', None)
    with public_validation._prepared_page_binding(enabled=False):
        pass


def test_binding_restores_attributes_on_error_and_nested_scope(monkeypatch):
    factory = object()
    raw = SimpleNamespace(cursor_factory=factory, prepare_threshold=None)
    calls = []
    fake = SimpleNamespace(connection=raw, validate_thread_sharing=lambda: calls.append(True))
    monkeypatch.setattr(public_validation, 'connection', fake)
    with pytest.raises(RuntimeError, match='probe'):
        with public_validation._prepared_page_binding(enabled=True):
            assert raw.prepare_threshold == 5
            assert raw.cursor_factory is public_validation._PageReadCursor
            with public_validation._prepared_page_binding(enabled=True):
                assert raw.prepare_threshold == 5
            assert raw.cursor_factory is public_validation._PageReadCursor
            raise RuntimeError('probe')
    assert raw.cursor_factory is factory and raw.prepare_threshold is None
    assert calls == [True, True]


def test_existing_prepare_threshold_is_preserved(monkeypatch):
    raw = SimpleNamespace(cursor_factory=object(), prepare_threshold=2)
    monkeypatch.setattr(public_validation, 'connection', SimpleNamespace(
        connection=raw, validate_thread_sharing=lambda: None))
    with public_validation._prepared_page_binding(enabled=True):
        assert raw.prepare_threshold == 2
    assert raw.prepare_threshold == 2


@pytest.mark.django_db(transaction=True)
def test_prepared_pages_match_native_binding_and_observe_revoked_catalog(request, monkeypatch):
    from django.db import connection

    from apps.core.models import Person
    from apps.listings.publication_state import refresh_all
    from scripts.synthetic_load_dataset import populate

    client = request.getfixturevalue('directory')
    populate(50)
    refresh_all()
    connection.close()
    connection.ensure_connection()
    raw = connection.connection
    factory, threshold = raw.cursor_factory, raw.prepare_threshold
    for index in range(14):
        response = client.get('/es/' if index % 2 else '/en/', {'page': index % 2 + 1})
        assert response.status_code == 200
        assert response.wsgi_request._publication_route['route'] == 'state'
    assert connection.connection is raw
    with connection.cursor() as cursor:
        cursor.execute('SELECT count(*), COALESCE(sum(generic_plans),0) FROM pg_prepared_statements')
        count, generic = cursor.fetchone()
        assert count > 0 and generic > 0
    before_count = response.context['page'].paginator.count

    def compare():
        for language in ('es', 'en'):
            bindings = []

            def observe_binding(execute, sql, values, many, context):
                if '"_pv_history"' in sql:
                    bindings.append(isinstance(context['cursor'].cursor,
                                               public_validation._PageReadCursor))
                return execute(sql, values, many, context)

            with connection.execute_wrapper(observe_binding):
                prepared = client.get('/' + language + '/')
            state_route = prepared.wsgi_request._publication_route['route'] == 'state'
            expected_bindings = [] if state_route and not prepared.context['page'].object_list else [state_route]
            assert bindings == expected_bindings
            with monkeypatch.context() as patch:
                patch.setattr(public_validation, '_prepared_page_binding',
                              lambda **kwargs: nullcontext())
                native = client.get('/' + language + '/')
            assert prepared.status_code == native.status_code == 200
            assert prepared.content == native.content
            assert prepared.context['page'].paginator.count == native.context['page'].paginator.count
            assert raw.cursor_factory is factory and raw.prepare_threshold == threshold
        return prepared.context['page'].paginator.count

    assert compare() == before_count
    person = Person.objects.get(individual__username='fixture-v1-individual')
    category = person.listing.approved_revision.categories.first()
    type(category).objects.filter(pk=category.pk).update(active=False)
    assert compare() < before_count
    refresh_all()
    assert compare() < before_count


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('prepared_page', [False, True])
def test_full_population_read_keeps_client_binding_for_wide_parameters(record_property, prepared_page):
    from django.db import connection

    from apps.listings.public_validation import read_publication_values

    count = 65536
    record_property('wide_parameter_count', count)

    class WideRead:
        def __iter__(self):
            query = 'SELECT 1 WHERE 1 IN (' + ','.join(['%s'] * count) + ')'
            with connection.cursor() as cursor:
                cursor.execute(query, [1] * count)
                yield cursor.fetchone()[0]

    assert read_publication_values(
        WideRead(), bounded_joins=True, prepared_page=prepared_page,
    ) == [1]
