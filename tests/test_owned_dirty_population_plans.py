"""Explicit plan diagnosis of the current dirty population; no candidate policy."""
import json

import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_dirty_population_plans(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_dirty_population_plans.py'
               for x in request.config.args):
        pytest.skip('Explicit owned plan diagnosis only')
    client = request.getfixturevalue('directory')
    populate(10000)
    publication_state.refresh_all()
    target = Listing.objects.filter(status='published', person__agency__isnull=False).first()
    Revision.objects.bulk_create([
        Revision(listing=target, manager_version=target.person.manager_version),
    ])
    assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {target.pk}
    results = []
    for path in ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic']:
        connection.close()
        captured = []

        def capture(execute, sql, params, many, context):
            text = str(sql)
            relevant = (text.startswith('SELECT') and '"listings_listing"' in text
                        and '"listings_publicationstate"' in text
                        and (text.startswith('SELECT COUNT') or 'AS "pk"' in text))
            if relevant:
                with connection.cursor() as cursor:
                    cursor.execute("SHOW jit")
                    jit = cursor.fetchone()[0]
                    cursor.execute("SHOW join_collapse_limit")
                    joins = cursor.fetchone()[0]
                captured.append((text, params, jit, joins))
            return execute(sql, params, many, context)

        with connection.execute_wrapper(capture):
            response = client.get(path)
        assert response.status_code == 200
        assert response.wsgi_request._publication_route['native_unknown'] == 1
        assert captured, 'Current dirty population SQL must be observed'
        plans = []
        for sql, params, jit, joins in captured:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')
                    cursor.execute("SET LOCAL statement_timeout='5s'")
                    cursor.execute("SELECT set_config('jit', %s, true), "
                                   "set_config('join_collapse_limit', %s, true)", [jit, joins])
                    cursor.execute('EXPLAIN (ANALYZE, BUFFERS, SETTINGS, FORMAT JSON) ' + sql, params)
                    plan = cursor.fetchone()[0]
            plans.append({'sql': sql, 'parameter_count': len(params or ()),
                          'jit': jit, 'join_collapse_limit': joins, 'plan': plan})
        results.append({'path': path, 'plans': plans})
    record_property('dirty_population_plans', json.dumps(results))
    record_property('scope', 'Own synthetic10k/one dirty, four actual route reads; fresh connection '
                    'per route, no timing comparison or candidate. EXPLAIN after request in readonly '
                    'transaction, five-second limit and captured planner settings. Shared buffers '
                    'remain warm. EXPLAIN execution is not the original cold request or PG CPU. '
                    'Synthetic SQL retained only in owned artifacts. No load/p95/N3 acceptance.')
