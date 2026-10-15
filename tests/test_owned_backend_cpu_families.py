"""Exact owned backend CPU grouped without PostgreSQL statement tracking."""

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

from scripts.benchmark_owned_backend_cpu import (
    backend_delta,
    backend_snapshot,
    owned_backend,
    statement_family,
)
from scripts.benchmark_owned_cpu_observer import group_path, owned_pg_pid, read_group
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_backend_cpu_by_family(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_backend_cpu_families.py'
               for x in request.config.args):
        pytest.skip('Explicit owned backend CPU diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    pg_group = group_path(owned_pg_pid(run, info))
    assert info['Id'] in str(pg_group)
    assert connection.vendor == 'postgresql'
    with connection.cursor() as cursor:
        cursor.execute('SHOW shared_preload_libraries')
        assert 'pg_stat_statements' not in cursor.fetchone()[0]
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
    call_command('refresh_publication_state')
    routes = [('/es/', {}), ('/en/', {}),
              ('/es/', {'q': 'photography'}), ('/en/', {'q': 'synthetic'}),
              (f"/es/listing/{dataset['sample_ids'][0]}/", {}),
              (f"/en/listing/{dataset['sample_ids'][0]}/", {})]
    cases = []
    for index, (path, params) in enumerate(routes):
        control = client.get(path, params)
        assert control.status_code == 200
        if index < 4:
            assert control.wsgi_request._publication_route['population'] == 'projection'
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            sql_pid = cursor.fetchone()[0]
        identity = owned_backend(run, info, sql_pid)
        groups = {}

        def observe(execute, sql, values, many, context):
            family = statement_family(sql)
            before = backend_snapshot(identity)
            started = time.perf_counter()
            try:
                return execute(sql, values, many, context)
            finally:
                after = backend_snapshot(identity)
                cpu = backend_delta(before, after)
                bucket = groups.setdefault(family, {'calls': 0, 'cpu_seconds': 0,
                                                    'wall_seconds': 0})
                bucket['calls'] += 1
                bucket['cpu_seconds'] += cpu['cpu_seconds']
                bucket['wall_seconds'] += time.perf_counter() - started

        before_pg = read_group(pg_group)
        before_backend = backend_snapshot(identity)
        started, cpu = time.perf_counter(), time.thread_time()
        with connection.execute_wrapper(observe):
            for _ in range(12):
                response = client.get(path, params)
                assert response.status_code == 200
                assert response['Cache-Control'] == 'no-store'
                if index < 4:
                    assert response.wsgi_request._publication_route['route'] == 'state'
                    assert response.wsgi_request._publication_route['population'] == 'projection'
                    assert response.context['page'].paginator.count == control.context['page'].paginator.count
                    assert [x.pk for x in response.context['page']] == [x.pk for x in control.context['page']]
                else:
                    assert response.context['public'] == control.context['public']
        elapsed, cpu = time.perf_counter() - started, time.thread_time() - cpu
        after_backend = backend_snapshot(identity)
        after_pg = read_group(pg_group)
        phase = backend_delta(before_backend, after_backend)
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            assert cursor.fetchone()[0] == sql_pid
        expected = ({'listing_count', 'listing_page', 'state_current', 'hydration'} if index < 2
                    else {'search_count', 'search_page', 'state_current', 'hydration'} if index < 4
                    else set())
        assert expected <= groups.keys()
        if index >= 4:
            assert not {'search_count', 'search_page', 'state_current', 'hydration'}.intersection(groups)
        attributed = sum(g['cpu_seconds'] for g in groups.values())
        assert attributed <= phase['cpu_seconds'] + 1e-9
        cases.append({'kind': 'listing' if index < 2 else 'search' if index < 4 else 'detail',
                      'language': path.split('/')[1], 'requests': 12,
                      'population': 'projection' if index < 4 else 'native_detail',
                      'backend_host_pid': identity['pid'], 'backend_cpu': phase,
                      'unattributed_backend_cpu_seconds': phase['cpu_seconds'] - attributed,
                      'postgres_cpu_usec': after_pg['cpu_stat']['usage_usec'] - before_pg['cpu_stat']['usage_usec'],
                      'client_thread_cpu_seconds': cpu, 'wall_seconds': elapsed, 'families': groups})
    record_property('owned_backend_cpu_families', cases)
    record_property('scope', '72 sequential synthetic requests, no PostgreSQL statement/planning tracking. '
                    'Each cursor.execute bracketed by exact own backend proc counters with identity guards. '
                    '100Hz quantization applies; family sums exclude work outside execute and parallel/background processes. '
                    'Application CPU/wall includes many proc reads and test assertions, not clean WSGI performance. '
                    'No SQL/parameters/bodies exported. Not p95, capacity, causal overhead or N3.')
