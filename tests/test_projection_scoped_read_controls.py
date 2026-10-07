"""Absolute normal-request controls after targeted JIT scope, no rule profiler."""
import time

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_normal_scoped_read_controls(request, monkeypatch, record_property, variant):
    client = request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        rows = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += ' ' + suffix
            if row.description_alternative:
                row.description_alternative += ' ' + suffix
            row.telegram = 'bench' + suffix
        Revision.objects.bulk_update(rows, ['description', 'description_alternative', 'telegram'], batch_size=250)
    before = stats_snapshot()
    with monkeypatch.context() as patch:
        patch.setattr(projection, 'supported', lambda **kwargs: False)
        start = time.perf_counter()
        native = client.get('/es/')
        native_seconds = time.perf_counter()-start
    start = time.perf_counter()
    control = client.get('/es/')
    control_seconds = time.perf_counter()-start
    assert native.status_code == control.status_code == 200
    assert native.context['page'].paginator.count == control.context['page'].paginator.count == 10000
    assert control.content == native.content
    assert control.wsgi_request._publication_route['route'] == 'projection'
    patterns = {}
    cache = {}

    def sql_timer(executor, sql, params, many, context):
        if sql not in cache:
            cache[sql] = query_pattern(sql)
        bucket = patterns.setdefault(cache[sql], {'calls': 0, 'total_time': 0.})
        start = time.perf_counter()
        try:
            return executor(sql, params, many, context)
        finally:
            bucket['calls'] += 1
            bucket['total_time'] += time.perf_counter()-start

    start = time.perf_counter()
    with connection.execute_wrapper(sql_timer):
        observed = client.get('/es/')
    observed_seconds = time.perf_counter()-start
    assert observed.content == control.content
    assert observed.wsgi_request._publication_route == control.wsgi_request._publication_route
    record_property('scoped_control', {'variant': variant, 'count': 10000,
        'native_control_seconds': native_seconds, 'projected_control_seconds': control_seconds,
        'projected_SQL_observed_request_seconds': observed_seconds,
        'query_count': sum(b['calls'] for b in patterns.values()),
        'sql_execute_seconds': sum(b['total_time'] for b in patterns.values()),
        'dominant_sql': [{'query_pattern': p, **b, 'mean_time': b['total_time']/b['calls']}
                        for p, b in sorted(patterns.items(), key=lambda item: item[1]['total_time'], reverse=True)],
        'route': observed.wsgi_request._publication_route,
        'tracked_statistics_before_controls': before, 'tracked_statistics_after': stats_snapshot(),
        'scope': 'Unprofiled DjangoClient controls, fixed native then projected, one each; SQL wrapper only in separate projected observation, same body/count/route. Preparation/stats outside timers; shared PG host caches warm, not reset. SQL execute not PG CPU, excludes fetch; lazy overlaps validation/render. Three local JIT configuration statements added to targeted scalar read, SQL unchanged; settings restoration and errors covered in N1. No causal source-to-source HTTP improvement claim from controls, no throughput/SLO acceptance.',
        'not_measured': ['validation', 'render', 'materialization_in_control', 'rows_returned',
                         'rows_affected', 'rows_scanned', 'causal_hook_overhead', 'DB_CPU_RSS_IO',
                         'concurrent_capacity', 'p95_request']})
