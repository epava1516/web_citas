"""Finite statement ranking in a label-verified, disposable PostgreSQL only."""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.benchmark_owned_cpu_observer import group_path, owned_pg_pid, read_group
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

# Classification stays inside PostgreSQL. Neither SQL text nor parameters leave
# the database through this observer, even when normalization retains literals.
STATISTICS = """
SELECT queryid::text,
 CASE
 WHEN query LIKE '%%pg_stat_statements%%' OR query LIKE '%%pg_backend_pid%%' THEN 'observer'
 WHEN query LIKE '%%"_pv_history"%%' THEN 'hydration'
 WHEN query LIKE '%%"search_document"%%' AND query LIKE '%%COUNT(%%' THEN 'search_count'
 WHEN query LIKE '%%"search_document"%%' AND query LIKE '%%@@%%' THEN 'search_page'
 WHEN query LIKE '%%"listings_publicationstate"%%' AND query LIKE '%%"eligible"%%'
      AND query LIKE '%%COUNT(%%' THEN 'listing_count'
 WHEN query LIKE '%%"listings_publicationstate"%%' AND query LIKE '%%"eligible"%%' THEN 'listing_page'
 WHEN query LIKE '%%"listings_publicationdirty"%%' THEN 'dirty'
 WHEN query LIKE '%%listings_publicationstate%%' THEN 'state_current'
 ELSE 'other' END AS family,
 plans, calls, total_plan_time, total_exec_time, rows,
 shared_blks_hit, shared_blks_read, temp_blks_read, temp_blks_written,
 jit_functions, jit_generation_time, jit_emission_time
FROM pg_stat_statements
WHERE dbid=(SELECT oid FROM pg_database WHERE datname=current_database())
  AND userid=(SELECT usesysid FROM pg_user WHERE usename=current_user)
ORDER BY total_plan_time + total_exec_time DESC
"""


def test_owned_statement_ranking(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_pg_statement_diagnostic.py'
               for x in request.config.args):
        pytest.skip('Explicit owned PostgreSQL statement diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    inspection = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    pg_group = group_path(owned_pg_pid(run, inspection))
    assert inspection['Id'] in str(pg_group)
    assert connection.vendor == 'postgresql'
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
    call_command('refresh_publication_state')
    with connection.cursor() as cursor:
        cursor.execute("SHOW shared_preload_libraries")
        assert 'pg_stat_statements' in cursor.fetchone()[0].split(',')
        cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_stat_statements')
        cursor.execute('SHOW pg_stat_statements.track_planning')
        previous = cursor.fetchone()[0]
        cursor.execute("SET pg_stat_statements.track_planning=on")
    cases = []
    routes = [('/es/', {}), ('/en/', {}),
              ('/es/', {'q': 'photography'}), ('/en/', {'q': 'synthetic'}),
              (f"/es/listing/{dataset['sample_ids'][0]}/", {}),
              (f"/en/listing/{dataset['sample_ids'][0]}/", {})]
    try:
        for index, (path, params) in enumerate(routes):
            control = client.get(path, params)
            assert control.status_code == 200
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_stat_statements_reset(0, '
                               '(SELECT oid FROM pg_database WHERE datname=current_database()), 0)')
                cursor.execute('SELECT pg_backend_pid()')
                backend_before = cursor.fetchone()[0]
            before = read_group(pg_group)
            started, cpu = time.perf_counter(), time.thread_time()
            for _ in range(3):
                response = client.get(path, params)
                assert response.status_code == 200
                assert response['Cache-Control'] == 'no-store'
                if index < 4:
                    assert response.wsgi_request._publication_route['route'] == 'state'
                    assert response.context['page'].paginator.count == control.context['page'].paginator.count
                    assert [x.pk for x in response.context['page']] == [x.pk for x in control.context['page']]
            elapsed, cpu = time.perf_counter() - started, time.thread_time() - cpu
            after = read_group(pg_group)
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                backend_after = cursor.fetchone()[0]
                cursor.execute(STATISTICS)
                columns = [x.name for x in cursor.description]
                statements = [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
            assert statements and any(x['plans'] > 0 for x in statements)
            families = {x['family'] for x in statements}
            if index >= 4:
                assert not families.intersection({'search_count', 'search_page', 'hydration'})
            elif index >= 2:
                assert {'search_count', 'search_page', 'hydration'} <= families
            else:
                assert {'listing_count', 'listing_page', 'hydration'} <= families
            assert all(x['family'] != 'observer' or x['calls'] <= 3 for x in statements)
            cases.append({'case': index, 'language': path.split('/')[1],
                          'kind': 'listing' if index < 2 else 'search' if index < 4 else 'detail',
                          'requests': 3, 'wall_seconds': elapsed, 'thread_cpu_seconds': cpu,
                          'postgres_cpu_usec': after['cpu_stat']['usage_usec'] - before['cpu_stat']['usage_usec'],
                          'backend_pid_unchanged': backend_before == backend_after,
                          'statements': [x for x in statements if x['family'] != 'observer']})
    finally:
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('pg_stat_statements.track_planning', %s, false)", [previous])
    record_property('owned_pg_statement_ranking', cases)
    record_property('scope', '18 sequential synthetic requests, six cases, three per case after warm control; '
                    'no Celery/Beat background load asserted. Own label-verified PostgreSQL only, '
                    'database-specific statistics reset. Planning/exec elapsed are not CPU; cgroup CPU '
                    'includes own database maintenance, no background subtraction or causal attribution. '
                    'Client Django thread CPU includes ORM/render/test transport, not WSGI-only. '
                    'Tracking planning adds overhead; no clean p95/capacity/N3. SQL/parameters not exported.')
