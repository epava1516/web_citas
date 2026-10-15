"""Finite cold-connection diagnostic; no startup requests discarded."""

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
from test_public_detail_prepared_guard import canonical_body

from apps.listings.models import Listing
from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('candidate', ['eager_generic', 'eager_auto'])
def test_owned_cold_prepared_cpu(request, record_property, candidate):
    if not any(str(x).split('::')[0] == 'tests/test_owned_cold_prepared_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit cold backend diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
    call_command('refresh_publication_state')
    listing = Listing.objects.get(pk=dataset['sample_ids'][0])
    routes = [('/es/', {}), ('/en/', {}),
              ('/es/', {'q': 'photography'}), ('/en/', {'q': 'synthetic'}),
              (f'/es/listing/{listing.pk}/', {}), (f'/en/listing/{listing.pk}/', {})]
    bodies, results = {}, []
    for block in range(3):
        arms = ('current', candidate) if block % 2 == 0 else (candidate, 'current')
        for arm in arms:
            connection.close()
            connection.ensure_connection()
            raw = connection.connection
            factory, threshold = raw.cursor_factory, raw.prepare_threshold
            assert threshold is None
            with connection.cursor() as cursor:
                cursor.execute('SHOW shared_preload_libraries')
                assert 'pg_stat_statements' not in cursor.fetchone()[0]
                cursor.execute('SHOW plan_cache_mode')
                previous_mode = cursor.fetchone()[0]
                assert previous_mode == 'auto'
                cursor.execute('SELECT pg_backend_pid(), (SELECT count(*) FROM pg_prepared_statements)')
                sql_pid, plans = cursor.fetchone()
                assert plans == 0
            identity = owned_backend(run, info, sql_pid)
            try:
                if arm == 'eager_generic':
                    with connection.cursor() as cursor:
                        cursor.execute("SET plan_cache_mode = force_generic_plan")
                # ClientCursor never prepares; these fixed arm thresholds apply
                # only when the product helper selects its server-binding cursor.
                raw.prepare_threshold = 5 if arm == 'current' else 0
                expected_threshold = raw.prepare_threshold
                rows = []
                for index in range(30):
                    case = index % len(routes)
                    path, params = routes[case]
                    before = backend_snapshot(identity)
                    wall, cpu = time.perf_counter(), time.thread_time()
                    response = client.get(path, params)
                    elapsed, app_cpu = time.perf_counter() - wall, time.thread_time() - cpu
                    after = backend_snapshot(identity)
                    assert connection.connection is raw
                    assert raw.cursor_factory is factory and raw.prepare_threshold == expected_threshold
                    assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                    if case < 4:
                        assert response.wsgi_request._publication_route['population'] == 'projection'
                        body = response.content
                    else:
                        body = canonical_body(response, listing)
                    if case not in bodies:
                        assert arm == 'current'
                        bodies[case] = body
                    assert body == bodies[case]
                    # Observation is outside the CPU/time bracket and uses unprepared client binding.
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT pg_backend_pid(), count(*), '
                                       'COALESCE(sum(generic_plans),0), COALESCE(sum(custom_plans),0) '
                                       'FROM pg_prepared_statements')
                        pid, count, generic, custom = cursor.fetchone()
                        assert pid == sql_pid
                    rows.append({'request_index': index, 'case': case,
                                 'backend_cpu_seconds': backend_delta(before, after)['cpu_seconds'],
                                 'app_cpu_seconds': app_cpu, 'wall_seconds': elapsed,
                                 'plans': count, 'generic': int(generic), 'custom': int(custom)})
                assert rows[-1]['plans'] > 0
                results.append({'block': block, 'arm': arm, 'backend_host_pid': identity['pid'],
                                'rows': rows})
            finally:
                raw.cursor_factory, raw.prepare_threshold = factory, threshold
                with connection.cursor() as cursor:
                    cursor.execute('SELECT set_config(%s, %s, false)', ['plan_cache_mode', previous_mode])
                connection.close()
    record_property('cold_prepared_cpu', results)
    record_property('scope', '180 sequential actual synthetic requests, fresh physical backend per arm/block. '
                    'Two fixed arms, 3 alternating blocks, no warmup or omitted first requests. '
                    'Candidate ' + candidate + ' is experimental session configuration, not product implementation: '
                    'future scoped SET/restore overhead is excluded. Python process/database buffers remain warm; '
                    'not actual cold Gunicorn workers, p95/capacity, or causal attribution of load transient. '
                    'CPU backend 100Hz counters; app timings include test-client request execution. '
                    'Exact full HTML parity; signed detail target verified then timestamp canonicalized.')
