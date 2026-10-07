"""Opt-in causal SQL/JIT contrast; never a load or acceptance substitute."""
import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('PROJECTION_JIT_DIAGNOSTIC_OUTPUT'), reason='Explicit owned diagnostic only')]

SETTINGS = ['server_version', 'jit', 'jit_above_cost', 'jit_inline_above_cost',
            'jit_optimize_above_cost', 'max_parallel_workers_per_gather', 'work_mem',
            'shared_buffers', 'random_page_cost', 'effective_cache_size', 'plan_cache_mode']
ORDERS = [('A', 'B'), ('B', 'A'), ('A', 'B'), ('B', 'A')]


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return query_pattern(value) if isinstance(value, str) else value


@pytest.mark.parametrize('count', [1000, 10000])
def test_captured_projection_jit(request, record_property, count):
    client = request.getfixturevalue('directory')
    populate(count)
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    captured = []

    def capture(execute, sql, params, many, context):
        if sql.lstrip().upper().startswith('SELECT') and 'AS "_pv_check_status"' in sql:
            captured.append((sql, tuple(params or ())))
        return execute(sql, params, many, context)

    started = time.perf_counter()
    with connection.execute_wrapper(capture):
        response = client.get('/es/')
    control_seconds = time.perf_counter() - started
    assert response.status_code == 200
    assert response.context['page'].paginator.count == count
    assert response.wsgi_request._publication_route['route'] == 'projection'
    assert len(captured) == 1
    sql, params = captured[0]
    assert not connection.in_atomic_block
    # Psycopg auto-prepared plans would otherwise couple mode to execution order.
    raw_connection = connection.connection
    original_prepare = raw_connection.prepare_threshold
    raw_connection.prepare_threshold = None
    effective = {}
    with connection.cursor() as cursor:
        for name in SETTINGS:
            cursor.execute('SELECT current_setting(%s)', [name])
            effective[name] = cursor.fetchone()[0]
    (Path(os.environ['PROJECTION_JIT_DIAGNOSTIC_OUTPUT']) / f'captured-{count}.json').write_text(
        json.dumps({'raw_sql_sha256': hashlib.sha256(sql.encode()).hexdigest(),
                    'query_pattern': query_pattern(sql), 'parameter_count': len(params),
                    'parameter_types': [type(p).__name__ for p in params],
                    'effective_settings': effective, 'pairs': ORDERS,
                    'values': 'redacted; exact SQL/params frozen in memory'}, indent=2) + '\n')
    reference = None

    def read(mode, *, plan=False):
        nonlocal reference
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute("SET LOCAL statement_timeout = '65s'")
            if mode == 'B':
                cursor.execute('SET LOCAL jit=off')
            cursor.execute('SHOW jit')
            jit = cursor.fetchone()[0]
            assert jit == ('off' if mode == 'B' else effective['jit'])
            if plan:
                cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, params)
                return {'mode': mode, 'jit': jit, 'plan': redact(cursor.fetchone()[0])}
            start = time.perf_counter()
            cursor.execute(sql, params)
            executed = time.perf_counter()
            rows = cursor.fetchall()
            finished = time.perf_counter()
            if reference is None:
                reference = rows
            assert rows == reference, 'Full ordered captured values diverged'
            assert len(rows) == count
            return {'mode': mode, 'jit': jit, 'execute_seconds': executed-start,
                    'fetch_seconds': finished-executed, 'select_seconds': finished-start,
                    'rows_returned': len(rows), 'full_ordered_values_equal': True}

    try:
        warmups = [read('A'), read('B')]
        pairs = []
        for index, order in enumerate(ORDERS):
            samples = [read(mode) for mode in order]
            modes = {sample['mode']: sample for sample in samples}
            a, b = modes['A']['select_seconds'], modes['B']['select_seconds']
            pairs.append({'index': index, 'order': order, 'samples': samples,
                          'saving_seconds': a-b, 'relative_saving': (a-b)/a})
        # Separate plans after ALL paired SELECTs; never mixed with their timers.
        plans = [read('A', plan=True), read('B', plan=True)]
        savings = [p['saving_seconds'] for p in pairs]
        ratios = [p['relative_saving'] for p in pairs]
        if effective['jit'] == 'on' and min(ratios) >= .20 and statistics.median(savings) >= .25:
            decision = 'confirmed_material_select_effect'
        elif max(abs(r) for r in ratios) <= .10 and max(abs(s) for s in savings) <= .05:
            decision = 'no_material_select_effect_observed'
        elif max(savings) < 0:
            decision = 'off_slower_in_all_pairs'
        else:
            decision = 'inconclusive_or_mixed'
        with connection.cursor() as cursor:
            cursor.execute('SHOW jit')
            assert cursor.fetchone()[0] == effective['jit']
        report = {
            'schema': 'projection-jit-causal-v1', 'count': count, 'variant': 'contractual',
            'query_pattern': query_pattern(sql),
            'raw_sql_sha256': hashlib.sha256(sql.encode()).hexdigest(),
            'parameters': {'count': len(params), 'types': [type(p).__name__ for p in params],
                           'values': 'redacted; frozen once in memory before paired SELECTs'},
            'capture_control_request_seconds': control_seconds,
            'capture_route': response.wsgi_request._publication_route,
            'effective_settings': effective, 'original_prepare_threshold': original_prepare,
            'paired_prepare_threshold': None, 'warmups_excluded': warmups,
            'pairs': pairs, 'separate_plans': plans, 'decision': decision,
            'median_saving_seconds': statistics.median(savings),
            'median_relative_saving': statistics.median(ratios),
            'settings_restored': True,
            'scope': 'Actual projection SELECT captured from one DjangoClient GET; identical SQL/parameters and full ordered values compared in memory. Raw cursor execute plus fetch, no ORM/rule profiler. Each read in own READ ONLY transaction; B changes only local jit; timeout equal in both. No global settings, schema/index/cache change. OS/PG caches warmed, not reset, shared host; no concurrent test load. Plans run AFTER pairs, per-node rows/loops/buffers are not global scanned rows. Capture request not A/B HTTP comparison; no request improvement/capacity attribution.',
            'not_measured': ['rows_affected', 'rows_scanned', 'DB_CPU', 'DB_RSS',
                             'DB_waits_over_time', 'causal_instrumentation_overhead',
                             'paired_HTTP_gain', 'validation', 'materialization', 'render',
                             'concurrent_capacity', 'cold_cache_effect'],
        }
        target = Path(os.environ['PROJECTION_JIT_DIAGNOSTIC_OUTPUT']) / f'jit-{count}.json'
        target.write_text(json.dumps(report, indent=2) + '\n')
        record_property('jit_diagnosis', report)
    finally:
        raw_connection.prepare_threshold = original_prepare
