"""Bounded native conflict-plan diagnosis; explicit own synthetic run only."""

import hashlib
import json
import time
from pathlib import Path

import pytest
from django.db import DatabaseError, connection
from psycopg import Error as PsycopgError
from test_directory_query_plans import stripped
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_conflict_plan_after_small_fixture_statistics(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_native_conflict_plan.py'
               for x in request.config.args):
        pytest.skip('Explicit bounded native conflict-plan diagnosis only')
    request.getfixturevalue('directory')
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    target = out / 'native-conflict-plans.json'
    tables = ['mediafiles_match', 'mediafiles_photo', 'listings_revision',
              'safety_rightsrectificationexecution']
    with connection.cursor() as cursor:
        # Preserve native statistics after the original eight scope controls.
        cursor.execute('SELECT relname, reltuples::bigint, relpages FROM pg_class '
                       'WHERE relname = ANY(%s) ORDER BY relname', [tables])
        initial_stats = cursor.fetchall()
    records = []

    def save():
        target.write_text(json.dumps({'precondition': 'Native statistics after original eight controls; no ANALYZE',
                                     'initial_estimates': initial_stats, 'queries': records,
                                     'scope': 'Diagnostic only,5s statement limit. EXPLAIN without ANALYZE '
                                              'adds planning overhead; no HTTP/CPU/p95 claim. '
                                              'No SQL/parameters/filter expressions retained.'}, indent=2) + '\n')

    def observe(execute, sql, params, many, context):
        if not sql.lstrip().upper().startswith('SELECT') or 'mediafiles_match' not in sql:
            return execute(sql, params, many, context)
        record = {'fingerprint': hashlib.sha256(sql.encode()).hexdigest(),
                  'query_bytes': len(sql.encode()), 'parameter_count': len(params or []),
                  'phase': 'explain', 'outcome': 'running'}
        records.append(record)
        started = time.monotonic()
        try:
            # Raw cursor avoids observer recursion; all statements stay in own DB.
            with connection.connection.cursor() as cursor:
                cursor.execute("SELECT current_setting('statement_timeout'), current_setting('jit'), "
                               "current_setting('join_collapse_limit'), current_setting('plan_cache_mode')")
                previous_timeout, jit, joins, mode = cursor.fetchone()
                record['settings'] = {'jit': jit, 'join_collapse_limit': joins, 'plan_cache_mode': mode}
                cursor.execute("SELECT set_config('statement_timeout', '5000', true)")
                cursor.execute('EXPLAIN (FORMAT JSON) ' + sql, params)
                plan = cursor.fetchone()[0][0]
                record['plan'] = stripped(plan['Plan'])
                record['jit'] = plan.get('JIT')
                record['explain_seconds'] = time.monotonic() - started
                record['phase'] = 'execute'
                save()
            started = time.monotonic()
            result = execute(sql, params, many, context)
            record['execute_seconds'] = time.monotonic() - started
            record['outcome'] = 'completed'
            with connection.connection.cursor() as cursor:
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", [previous_timeout])
            return result
        except (DatabaseError, PsycopgError) as error:
            record['outcome'] = 'database_error'
            record['error_type'] = type(error).__name__
            record['sqlstate'] = getattr(error.__cause__, 'sqlstate', None)
            record['failed_phase_seconds'] = time.monotonic() - started
            raise
        finally:
            save()

    try:
        with connection.execute_wrapper(observe):
            dataset = populate(10000)
        assert dataset['published'] == 10000 and records
    finally:
        record_property('native_conflict_plan_artifact', str(target))
        record_property('native_conflict_outcomes', [
            {'phase': r['phase'], 'outcome': r['outcome'], 'sqlstate': r.get('sqlstate')}
            for r in records])
