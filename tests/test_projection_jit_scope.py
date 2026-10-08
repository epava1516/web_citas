"""Scoped read policy must preserve results, outer transactions and error recovery."""
import pytest
from django.db import DatabaseError, connection, transaction
from django.db.models.expressions import RawSQL
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import projected_publication as projection
from apps.listings import public_validation
from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


def jit():
    with connection.cursor() as cursor:
        cursor.execute('SHOW jit')
        return cursor.fetchone()[0]


def test_projection_read_policy_restores_nested_state_and_preserves_writes(request):
    request.getfixturevalue('directory')
    query = Listing.objects.order_by('pk').values_list('pk', 'status')
    expected = list(query)
    original = jit()
    for initial in ['on', 'off']:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SELECT set_config('jit', %s, true)", [initial])
            assert public_validation.read_publication_values(query.all()) == expected
            assert jit() == initial
            with connection.cursor() as cursor:
                cursor.execute('SHOW transaction_read_only')
                assert cursor.fetchone()[0] == 'off'
            # The policy does not turn an existing writable transaction read-only.
            assert Listing.objects.filter(pk=expected[0][0]).update(status=expected[0][1]) == 1
    assert jit() == original
    observed = []

    def observe(execute, sql, params, many, context):
        kind = ("population" if 'AS "_sql_publication_positive"' in sql else
                "page" if 'AS "_pv_check_status"' in sql and '"listings_listing"' in sql else None)
        if kind:
            # Read the setting without replacing any native rule or recursing
            # through Django's execute_wrapper. Only this functional test observes.
            with connection.connection.cursor() as cursor:
                cursor.execute('SHOW jit')
                observed.append((kind, cursor.fetchone()[0]))
        return execute(sql, params, many, context)

    client = request.getfixturevalue('directory')
    with connection.execute_wrapper(observe):
        response = client.get('/es/')
    assert response.status_code == 200 and observed == [('population', 'off'), ('page', 'off')]
    assert response.wsgi_request._publication_route['route'] == 'projection'
    assert jit() == original


def test_projection_read_failure_recovers_outer_transaction_setting(request):
    request.getfixturevalue('directory')
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET LOCAL jit=on')
        bad = Listing.objects.annotate(probe=RawSQL('owned_jit_scope_missing_function()', [])).values('probe')
        with pytest.raises(DatabaseError):
            public_validation.read_publication_values(bad)
        assert jit() == 'on'
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            assert cursor.fetchone()[0] == 1
        assert not connection.needs_rollback


def test_read_policy_helper_change_invalidates_the_rule_footprint(monkeypatch):
    assert projection.supported()
    previous = projection.definitions_digest()
    monkeypatch.setattr(public_validation, 'read_publication_values', lambda query: [])
    assert projection.definitions_digest() != previous
    assert not projection.supported()


def test_page_hydration_scoped_read_is_equivalent_and_restores_nested_state(request):
    from apps.listings.discovery import candidates
    from apps.listings.public_validation import PublicationContext

    request.getfixturevalue("directory")
    query = candidates({})
    before = jit()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL jit=on")
        native = PublicationContext(query)
        scoped = PublicationContext(query, page_read=True)
        assert jit() == "on"
        assert [row.pk for row in native.rows] == [row.pk for row in scoped.rows]
        assert [(row._pv_check_status, row._pv_grant, row.approved_revision_id) for row in native.rows] == [
            (row._pv_check_status, row._pv_grant, row.approved_revision_id) for row in scoped.rows]
    assert jit() == before
