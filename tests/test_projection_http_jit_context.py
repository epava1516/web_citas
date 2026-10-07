"""Opt-in HTTP contrast isolates local JIT from the transaction context."""
import hashlib
import json
import os
import statistics
import time
from contextlib import nullcontext
from pathlib import Path

import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('PROJECTION_HTTP_JIT_OUTPUT'), reason='Explicit isolated diagnostic only')]
ORDERS = [('A', 'C', 'B'), ('B', 'C', 'A'), ('C', 'B', 'A'), ('A', 'B', 'C')]


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return query_pattern(value) if isinstance(value, str) else value


def stats_snapshot():
    with connection.cursor() as cursor:
        cursor.execute("SELECT relname, reltuples, relpages FROM pg_class WHERE relname IN "
                       "('listings_listing','listings_revision','core_person',"
                       "'core_verificationcheck','core_representationaction') ORDER BY relname")
        return [dict(zip(['table', 'estimated_tuples', 'pages'], row, strict=True))
                for row in cursor.fetchall()]


def test_projection_http_jit_context(request, record_property):
    client = request.getfixturevalue('directory')
    populate(10000)
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert connection.get_autocommit() and not connection.in_atomic_block
    expected = None
    settings = {}
    with connection.cursor() as cursor:
        for key in ['server_version', 'jit', 'jit_above_cost', 'jit_inline_above_cost',
                    'jit_optimize_above_cost', 'max_parallel_workers_per_gather', 'work_mem']:
            cursor.execute('SELECT current_setting(%s)', [key])
            settings[key] = cursor.fetchone()[0]
        driver_cursor = type(cursor.cursor).__module__ + '.' + type(cursor.cursor).__qualname__
    cache = {}

    def get(mode, observed):
        nonlocal expected
        patterns, main = {}, []

        def execute(executor, sql, params, many, context):
            if sql not in cache:
                cache[sql] = query_pattern(sql)
            pattern = cache[sql]
            if 'AS "_pv_check_status"' in sql and '"listings_listing"."id" AS "pk"' in sql:
                main.append((sql, tuple(params or ())))
            bucket = patterns.setdefault(pattern, {'calls': 0, 'total_time': 0.})
            start = time.perf_counter()
            try:
                return executor(sql, params, many, context)
            finally:
                bucket['calls'] += 1
                bucket['total_time'] += time.perf_counter() - start

        with (nullcontext() if mode == 'A' else transaction.atomic()):
            with connection.cursor() as cursor:
                if mode != 'A':
                    cursor.execute('SET TRANSACTION READ ONLY')
                    cursor.execute("SET LOCAL statement_timeout='65s'")
                    if mode == 'B':
                        cursor.execute('SET LOCAL jit=off')
                cursor.execute('SHOW jit')
                jit = cursor.fetchone()[0]
                cursor.execute('SHOW transaction_read_only')
                readonly = cursor.fetchone()[0]
            assert jit == ('off' if mode == 'B' else settings['jit'])
            before = stats_snapshot() if observed else None
            start = time.perf_counter()
            with (connection.execute_wrapper(execute) if observed else nullcontext()):
                response = client.get('/es/')
            elapsed = time.perf_counter() - start
            assert response.status_code == 200
            assert response.context['page'].paginator.count == 10000
            assert response.wsgi_request._publication_route['route'] == 'projection'
            if expected is None:
                expected = response.content
            assert response.content == expected
            report = {'mode': mode, 'request_seconds': elapsed, 'jit': jit,
                      'transaction_read_only': readonly, 'route': response.wsgi_request._publication_route,
                      'body_count_page_equal': True}
            if observed:
                assert len(main) == 1
                sql, params = main[0]
                pattern = query_pattern(sql)
                report.update(query_count=sum(b['calls'] for b in patterns.values()),
                    sql_execute_seconds=sum(b['total_time'] for b in patterns.values()),
                    main_execute_seconds=patterns[pattern]['total_time'],
                    dominant_sql=[{'query_pattern': p, **b, 'mean_time': b['total_time']/b['calls']}
                                  for p, b in sorted(patterns.items(), key=lambda item: item[1]['total_time'], reverse=True)],
                    stats_before_request=before, stats_after_request=stats_snapshot(),
                    raw_main_sql_sha256=hashlib.sha256(sql.encode()).hexdigest(),
                    parameter_types=[type(p).__name__ for p in params], parameters='redacted')
                # Planner-only EXPLAIN is separate and AFTER HTTP timing, in the
                # same mode. It does not execute the captured read or warm it.
                with connection.cursor() as cursor:
                    cursor.execute('EXPLAIN (FORMAT JSON) ' + sql, params)
                    report['separate_planner_only'] = redact(cursor.fetchone()[0])
            response.close()
        with connection.cursor() as cursor:
            cursor.execute('SHOW jit')
            assert cursor.fetchone()[0] == settings['jit']
            cursor.execute('SHOW transaction_read_only')
            assert cursor.fetchone()[0] == 'off'
        return report

    controls = [get(mode, False) for mode in ['A', 'C', 'B']]
    triplets = []
    for order in ORDERS:
        samples = [get(mode, True) for mode in order]
        modes = {s['mode']: s for s in samples}
        c, b = modes['C']['request_seconds'], modes['B']['request_seconds']
        triplets.append({'order': order, 'samples': samples, 'c_minus_b_seconds': c-b,
                         'c_minus_b_fraction': (c-b)/c,
                         'a_minus_c_seconds': modes['A']['request_seconds']-c})
    savings = [t['c_minus_b_seconds'] for t in triplets]
    fractions = [t['c_minus_b_fraction'] for t in triplets]
    decision = ('confirmed_material_HTTP_effect_in_equal_transactions'
                if settings['jit']=='on' and min(fractions)>=.20 and statistics.median(savings)>=.25
                else 'no_material_HTTP_effect_observed' if max(abs(x) for x in fractions)<=.10
                    and max(abs(x) for x in savings)<=.05
                else 'off_slower_in_all_triplets' if max(savings)<0 else 'inconclusive_or_mixed')
    result = {'schema': 'projection-http-jit-context-v1', 'count': 10000,
              'effective_settings': settings, 'driver_cursor': driver_cursor,
              'prepare_threshold': connection.connection.prepare_threshold,
              'controls_without_wrapper': controls, 'triplets': triplets, 'decision': decision,
              'median_c_minus_b_seconds': statistics.median(savings),
              'settings_restored': True,
              'scope': 'DjangoClient end-to-end excludes network/fixtures/transaction setup. A normal autocommit; C/B same READ ONLY transactions and65s statement timeout, differ only local jit. Controls unprofiled/no SQL wrapper, measured triplets identical lightweight SQL hooks, no rule profiler/monkeypatch/wrapping. SQL execute excludes fetch and is not PG CPU; lazy query work overlaps validation/render. Separate EXPLAIN planner-only after HTTP, not ANALYZE, estimated rows are not actual/scanned rows; contemporaneous planner state is not proof of actual timed execution plan/JIT. Warmed shared host/PG caches, fixed alternating orders, no reset. HTTP SQL parameter timestamps may advance naturally; fixture authority/expiry remain unchanged, exact bodies/count/pages/routing required. R1 frozen SELECT is not reinterpreted.',
              'not_measured': ['actual_JIT_time_during_HTTP', 'actual_plan_during_HTTP',
                               'rows_returned', 'rows_affected', 'rows_scanned',
                               'validation_materialization_render_exclusive', 'DB_CPU_RSS_IO',
                               'causal_hook_overhead', 'cold_cache', 'concurrent_capacity']}
    (Path(os.environ['PROJECTION_HTTP_JIT_OUTPUT'])/'http-jit.json').write_text(json.dumps(result, indent=2)+'\n')
    record_property('http_jit_context', result)
