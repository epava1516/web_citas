"""Opt-in attribution of the current SQL candidate; no capacity acceptance."""
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection
from django.db.models.signals import post_init
from django.db.models.sql.compiler import SQLCompiler
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha, targets
from test_projection_http_jit_context import stats_snapshot

from apps.listings import projected_publication as projection
from apps.listings import sql_publication
from apps.listings.models import Revision
from scripts.benchmark_call_profile import CallProfile
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('SQL_PROFILE_OUTPUT'), reason='Explicit isolated attribution only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_sql_current_rule_profile(request, record_property, variant):
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
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert projection.supported()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    body = client.get('/es/').content
    before = stats_snapshot()
    controls = []
    functions = targets() + [projection.definitions, projection.code_signature,
        SQLCompiler.as_sql, SQLCompiler.execute_sql, SQLCompiler.results_iter,
        sql_publication.read_ordered_scalar_population,
        sql_publication.CapturedSQLRead.__iter__,
        sql_publication.SQLPublication.visible_keys, sql_publication.SQLPublication.scalar_page,
        sql_publication.SQLPublication.captured_revision, sql_publication.SQLPublication.__init__,
        sql_publication.SQLPublication.visible_ids, sql_publication.authority_proof,
        sql_publication.content_proof, sql_publication.bulk_authority_membership,
        sql_publication.JSONChoicesProof.as_sql, sql_publication.PlainTextProof.as_sql]
    profile = CallProfile(functions)
    patterns, cache = {}, {}

    def sql_timer(execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed = time.perf_counter()-start
            if sql not in cache:
                cache[sql] = query_pattern(sql)
            bucket = patterns.setdefault(cache[sql], {'calls': 0, 'total_time': 0.})
            bucket['calls'] += 1
            bucket['total_time'] += elapsed

    def check(response):
        assert response.status_code == 200 and response.content == body
        route = response.wsgi_request._publication_route
        assert route['route'] == 'projection'
        assert route['candidate_stats']['positive'] == 10000
        assert route['candidate_stats']['native_fallback'] == 0
        assert route['candidate_stats']['scalar_capture'] is True
        assert route['candidate_stats']['text_membership'] is True
        assert response.context['page'].paginator.count == 10000
        assert projection.supported()
        return route

    for stage in ['before', 'after']:
        for _ in range(3):
            start = time.perf_counter()
            response = client.get('/es/')
            elapsed = time.perf_counter()-start
            check(response)
            controls.append({'stage': stage, 'seconds': elapsed})
        if stage == 'before':
            post_init.connect(profile.objects, weak=False)
            try:
                start = time.perf_counter()
                with profile, connection.execute_wrapper(sql_timer):
                    measured = client.get('/es/')
                observed_seconds = time.perf_counter()-start
            finally:
                post_init.disconnect(profile.objects)
            route = check(measured)
    after = stats_snapshot()
    report = {'variant': variant, 'count': 10000, 'controls': controls,
        'control_median_seconds': statistics.median(x['seconds'] for x in controls),
        'observed_request_seconds': observed_seconds,
        'rules': profile.report(), 'objects': dict(profile.materialized),
        'objects_provenance': dict(profile.provenance), 'route': route,
        'queries': sum(v['calls'] for v in patterns.values()),
        'sql_execute_seconds': sum(v['total_time'] for v in patterns.values()),
        'dominant_sql': [{'query_pattern': p, **v, 'mean_time': v['total_time']/v['calls']}
                        for p,v in sorted(patterns.items(),key=lambda x:x[1]['total_time'],reverse=True)],
        'statistics_before': before, 'statistics_after': after,
        'statistics_endpoints_equal': before == after,
        'scope': 'Same current scalar/index code and 10000 repeated/diverse fixture. Three outer-timer controls, one nonwrapping call/return profile with post_init and execute_wrapper, three controls. Current scalar capture, consumed-page UUID conversion, proof preparation, fingerprint code-signature traversal and compiler directly observed. SQL proof predicates run inside SELECT: their rowwise calls/times are NOT Python rule measurements. Constructor/as_sql times describe preparation/compilation only. Exclusive discounts only direct instrumented children once, with child identity/time recorded. Recursive code_signature inclusive events overlap; do not sum them as request time. Lazy SQL is nested in reads, validation and rendering, not a sum of phases; SQL execute excludes explicit fetch and is not DB CPU. Model counts are constructions, not SQL rows or unique entities. Observer perturbs calls; control difference is descriptive, not a causal correction. No competing test/build; normal services not measured. Prior complete ordered native oracle from scalar A/B/C plus six public-default cases reused; these samples check status/body/count/actual combined route without repeating that oracle. Existing top5 plans from scalar/index candidate reused, no application change since that run; none during this run. Expanded target set means exclusive attribution is not identical to historical profiles.',
        'not_measured': ['SQL per-row proof rule calls/times', 'SQL rows_returned/affected/scanned',
            'causal observer overhead', 'p95 exclusive', 'DB CPU/RSS/waits/locks/IO',
            'current concurrent capacity', '100/1000 common matrix']}
    record_property('sql_current_profile', report)
    Path(os.environ['SQL_PROFILE_OUTPUT'],variant+'.json').write_text(json.dumps(report,indent=2)+'\n')
