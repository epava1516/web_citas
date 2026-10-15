"""Finite raw-query CPU experiment; does not broaden product preparation."""

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

from scripts.benchmark_owned_backend_cpu import (
    backend_delta,
    backend_snapshot,
    owned_backend,
    statement_family,
)
from scripts.benchmark_owned_cpu_observer import owned_pg_pid
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_prepared_guard_reads_cpu(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_prepared_guard_reads_cpu.py'
               for x in request.config.args):
        pytest.skip('Explicit owned guard-read preparation diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-' + run['id']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name], text=True))[0]
    owned_pg_pid(run, info)
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
    call_command('refresh_publication_state')
    with connection.cursor() as cursor:
        cursor.execute('SHOW shared_preload_libraries')
        assert 'pg_stat_statements' not in cursor.fetchone()[0]
        cursor.execute('SELECT pg_backend_pid()')
        sql_pid = cursor.fetchone()[0]
    identity = owned_backend(run, info, sql_pid)
    raw = connection.connection
    previous_threshold, previous_factory = raw.prepare_threshold, raw.cursor_factory
    cases = []
    try:
        raw.prepare_threshold = 5
        for kind in ('listing', 'detail'):
            captured = []
            for index in (0, 1):
                reads = []

                def capture(execute, sql, values, many, context):
                    family = statement_family(sql)
                    if (sql.lstrip().upper().startswith('SELECT')
                            and family in ('catalog', 'media', 'rights')):
                        assert not many
                        reads.append((family, sql, tuple(values) if values is not None else None))
                    return execute(sql, values, many, context)

                path = ('/es/' if kind == 'listing'
                        else f"/es/listing/{dataset['sample_ids'][index]}/")
                with connection.execute_wrapper(capture):
                    response = client.get(path, {'page': index + 1} if kind == 'listing' else {})
                assert response.status_code == 200
                if kind == 'listing':
                    assert response.wsgi_request._publication_route['route'] == 'state'
                assert {'catalog', 'media'} <= {family for family, _, _ in reads}
                captured.append(reads)

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                expected = []
                for reads in captured:
                    result = []
                    for _, sql, params in reads:
                        with connection.cursor() as cursor:
                            cursor.execute(sql, params)
                            result.append(cursor.fetchall())
                    expected.append(result)

                def operation(variant, index, family):
                    for position, (label, sql, params) in enumerate(captured[index]):
                        if label != family:
                            continue
                        if variant == 'client_native':
                            with connection.cursor() as cursor:
                                cursor.execute(sql, params)
                                rows = cursor.fetchall()
                        else:
                            with psycopg.Cursor(raw) as cursor:
                                cursor.execute(sql, params, prepare=variant == 'server_prepared')
                                rows = cursor.fetchall()
                        if rows != expected[index][position]:
                            raise AssertionError('Raw row parity changed; values not exported')

                variants = ['client_native', 'server_unprepared', 'server_prepared']
                for family in sorted({family for reads in captured for family, _, _ in reads}):
                    for variant in variants:
                        for index in range(8):
                            operation(variant, index % 2, family)
                    blocks = []
                    for block in range(3):
                        for variant in variants[block:] + variants[:block]:
                            before = backend_snapshot(identity)
                            for index in range(12):
                                operation(variant, index % 2, family)
                            after = backend_snapshot(identity)
                            blocks.append({'block': block, 'variant': variant, 'iterations': 12,
                                           'backend_cpu': backend_delta(before, after)})
                    cases.append({'kind': kind, 'family': family,
                                  'queries_per_set': [sum(label == family for label, _, _ in reads)
                                                      for reads in captured],
                                  'blocks': blocks})
        with connection.cursor() as cursor:
            cursor.execute('SELECT count(*), COALESCE(sum(generic_plans),0), '
                           'COALESCE(sum(custom_plans),0) FROM pg_prepared_statements')
            prepared, generic, custom = map(int, cursor.fetchone())
        assert prepared > 0 and generic > 0
    finally:
        raw.prepare_threshold = previous_threshold
    assert raw.cursor_factory is previous_factory and raw.prepare_threshold == previous_threshold
    record_property('prepared_guard_reads_cpu', {'cases': cases, 'prepared_count': prepared,
                    'generic_plan_uses': generic, 'custom_plan_uses': custom,
                    'backend_host_pid': identity['pid'], 'psycopg_version': psycopg.__version__})
    record_property('scope', 'Captured catalog/media/rights SELECTs from two current list pages and '
                    'two current details; exact raw rows compared every replay in own readonlyRR. '
                    'Three variants,3rotating blocks12replays after8warmups each, CPU100Hz. '
                    'Factory unchanged, threshold restored, no query/result export or product patch. '
                    'Replays omit ORM/HTTP/mutations; not full guard parity, p95, capacity or N3.')
