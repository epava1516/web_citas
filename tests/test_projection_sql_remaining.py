"""Separate synthetic read-only plans after observed worker SQL dominance."""
import time

import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_projection_dominant_sql_separate_explain(request, record_property):
    diagnose(request, record_property, 'contractual')


def test_projection_diverse_sql_separate_explain(request, record_property):
    diagnose(request, record_property, 'diverse')


def diagnose(request, record_property, variant):
    client = request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        from test_projection_cost_cycle import alpha

        from apps.listings.models import Revision
        rows = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += ' ' + suffix
            if row.description_alternative:
                row.description_alternative += ' ' + suffix
            row.telegram = 'bench' + suffix
        Revision.objects.bulk_update(rows, ['description', 'description_alternative', 'telegram'], batch_size=250)
    patterns = {}
    reads = {}
    cache = {}

    def execute(executor, sql, params, many, context):
        if sql not in cache:
            cache[sql] = query_pattern(sql)
        pattern = cache[sql]
        if sql.lstrip().upper().startswith('SELECT'):
            reads.setdefault(pattern, (sql, params))
        bucket = patterns.setdefault(pattern, {'calls': 0, 'total_time': 0.})
        started = time.perf_counter()
        try:
            return executor(sql, params, many, context)
        finally:
            bucket['calls'] += 1
            bucket['total_time'] += time.perf_counter() - started

    started = time.perf_counter()
    with connection.execute_wrapper(execute):
        response = client.get('/es/')
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert response.context['page'].paginator.count == 10000
    assert response.wsgi_request._publication_route['route'] == 'projection'

    def redact(value):
        if isinstance(value, dict):
            return {key: redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [redact(item) for item in value]
        if isinstance(value, str):
            return query_pattern(value)
        return value

    plans = []
    for pattern in sorted(reads, key=lambda key: patterns[key]['total_time'], reverse=True)[:3]:
        sql, params = reads[pattern]
        # EXPLAIN executes only these recorded reads, in a separate read-only
        # transaction after timers close. Never put its duration in request SQL.
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, params)
            plans.append({'query_pattern': pattern, 'plan': redact(cursor.fetchone()[0])})
    sql_total = sum(b['total_time'] for b in patterns.values())
    record_property('sql_diagnosis', {
        'variant': variant, 'requests': 1,
        'plan_selection': 'Top three recorded SELECT patterns by accumulated cursor.execute duration',
        'plan_coverage_percent': 100 * sum(patterns[p['query_pattern']]['total_time'] for p in plans) / sql_total,
        'trigger': '72 completed projected worker requests: accumulated SQL execute / accumulated WSGI=51.47495%, above prefixed50% diagnostic threshold; DB CPU unknown',
        'request_seconds': elapsed, 'query_count': sum(b['calls'] for b in patterns.values()),
        'sql_execute_seconds': sum(b['total_time'] for b in patterns.values()),
        'route': response.wsgi_request._publication_route,
        'dominant_sql': [{'query_pattern': pattern, **bucket,
                         'mean_time': bucket['total_time']/bucket['calls'],
                         'calls_per_request': bucket['calls'],
                         'percent_observed_sql': 100 * bucket['total_time'] / sql_total}
                        for pattern, bucket in sorted(patterns.items(), key=lambda item: item[1]['total_time'], reverse=True)],
        'separate_plans': plans,
        'scope': 'Fresh owned PG/synthetic10000/one DjangoClient request, lightweight SQL wrapper only, no rule profiler/post_init. Not strictly equivalent to full matrix or concurrent workers; excludes network/fixtures. Parameters never stored; plan strings/literals redact via SQL normalizer. SQL execute contains client binding/driver/server/buffering; excludes subsequent fetch. EXPLAIN selects after request, warmed OS/PG caches, READ ONLY transaction; plan actual rows describe per-node streams and loops, not rows_scanned/request. No pg_stat_statements or config change.',
        'not_measured': 'rows_returned; rows_affected; rows_scanned; DB CPU/RSS/waits/locks/IO; materialization; validation/render exclusive; causal overhead; concurrent capacity',
    })
