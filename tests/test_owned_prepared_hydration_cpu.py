"""Raw SELECT preparation experiment, isolated from product cursor configuration."""

import hashlib
import json
import os
import subprocess
from pathlib import Path

import psycopg
import pytest
from django.core.management import call_command
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.benchmark_owned_backend_cpu import backend_delta, backend_snapshot, owned_backend
from scripts.benchmark_owned_cpu_observer import owned_pg_pid
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_prepared_hydration_cpu(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_prepared_hydration_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit owned prepared-hydration CPU diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    owned_pg_pid(run, info)
    client = request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state')
    captured = []

    def capture(execute, sql, values, many, context):
        if '"_pv_history"' in sql:
            captured.append((sql, values))
        return execute(sql, values, many, context)

    for number in (1, 2):
        with connection.execute_wrapper(capture):
            response = client.get('/es/', {'page': number})
        assert response.status_code == 200
        assert response.wsgi_request._publication_route['route'] == 'state'
    assert len(captured) == 2
    assert captured[0][0] == captured[1][0] and captured[0][1] != captured[1][1]
    with connection.cursor() as cursor:
        cursor.execute('SHOW shared_preload_libraries')
        assert 'pg_stat_statements' not in cursor.fetchone()[0]
        cursor.execute('SELECT pg_backend_pid()')
        sql_pid = cursor.fetchone()[0]
    identity = owned_backend(run, info, sql_pid)
    raw = connection.connection
    previous_threshold = raw.prepare_threshold
    previous_factory = raw.cursor_factory
    results = []
    try:
        # This single disposable connection only. Django settings/factory unchanged.
        raw.prepare_threshold = 5
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                cursor.execute('SET LOCAL jit=off')
                cursor.execute('SET LOCAL join_collapse_limit=1')
            expected = []
            for sql, params in captured:
                with connection.cursor() as cursor:
                    cursor.execute(sql, params)
                    expected.append(cursor.fetchall())
            assert [len(x) for x in expected] == [24, 24]

            def operation(variant, index):
                sql, params = captured[index]
                if variant == 'client_native':
                    with connection.cursor() as cursor:
                        cursor.execute(sql, params)
                        rows = cursor.fetchall()
                else:
                    with psycopg.Cursor(raw) as cursor:
                        cursor.execute(sql, params, prepare=variant == 'server_prepared')
                        rows = cursor.fetchall()
                if rows != expected[index]:
                    raise AssertionError('Raw row parity changed; values intentionally not emitted')

            variants = ['client_native', 'server_unprepared', 'server_prepared']
            for variant in variants:
                for index in range(8):
                    operation(variant, index % 2)
            for block in range(3):
                order = variants[block:] + variants[:block]
                for variant in order:
                    before = backend_snapshot(identity)
                    for index in range(12):
                        operation(variant, index % 2)
                    after = backend_snapshot(identity)
                    results.append({'block': block, 'variant': variant, 'iterations': 12,
                                    'backend_cpu': backend_delta(before, after)})
            with connection.cursor() as cursor:
                cursor.execute('SELECT count(*), COALESCE(sum(generic_plans),0), '
                               'COALESCE(sum(custom_plans),0) FROM pg_prepared_statements')
                prepared_count, generic_count, custom_count = map(int, cursor.fetchone())
                assert prepared_count >= 1
    finally:
        raw.prepare_threshold = previous_threshold
    assert raw.cursor_factory is previous_factory
    assert raw.prepare_threshold == previous_threshold
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_backend_pid()')
        assert cursor.fetchone()[0] == sql_pid
    record_property('prepared_hydration_cpu', {
        'query_sha256': hashlib.sha256(captured[0][0].encode()).hexdigest(),
        'query_bytes': len(captured[0][0].encode()), 'parameter_sets': 2,
        'rows_per_set': 24, 'blocks': results, 'prepared_count': prepared_count,
        'generic_plan_uses': generic_count, 'custom_plan_uses': custom_count,
        'psycopg_version': psycopg.__version__, 'backend_host_pid': identity['pid'],
        'threshold_restored': True, 'cursor_factory_unchanged': True,
    })
    record_property('scope', 'Exact captured hydration SELECT/parameters from current guarded pages1/2; '
                    'raw row equality every operation, one own readonlyRR snapshot and same jit/join policy. '
                    'Three variants isolate client binding/server binding/preparation;3rotating blocks12each '
                    'after8warmups each. No global settings/factory change, product patch, pgtracker, load or p95. '
                    'BackendCPU100Hz quantization; no claim for other SQL/types/mutations/plan invalidation/N3.')
