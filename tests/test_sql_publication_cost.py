"""Opt-in paired controls and separate SQL plans for the conservative proof."""
import hashlib
import json
import os
import statistics
import time
from contextlib import contextmanager
from pathlib import Path

import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import projected_publication as projection
from apps.listings.discovery import candidates
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('SQL_PROOF_COST_OUTPUT'), reason='Explicit isolated comparison only')]


@contextmanager
def strategy(monkeypatch, mode):
    original = projection.ProjectedPublication.__init__
    with monkeypatch.context() as patch:
        def select(self, query, **kwargs):
            return original(self, query, sql=mode == 'sql')
        patch.setattr(projection.ProjectedPublication, '__init__', select)
        yield


def redact_plan(value):
    if isinstance(value, dict):
        return {k: redact_plan(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_plan(v) for v in value]
    if isinstance(value, str):
        return query_pattern(value)
    return value


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_sql_complete_path_paired_cost(request, monkeypatch, record_property, variant):
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
        del rows
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    assert projection.supported()
    digest = projection.definitions_digest()
    # Preparation of this own database only; no change of shared server policy.
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    expected = native_ids(candidates({}))
    assert len(expected) == 10000
    for sql in [False, True]:
        p = projection.ProjectedPublication(candidates({}), sql=sql)
        assert p.visible_ids(candidates({})) == expected
    expected_digest = hashlib.sha256(b''.join(pk.bytes for pk in expected)).hexdigest()
    body = None

    def equivalent(response):
        nonlocal body
        assert response.status_code == 200
        assert response.context['page'].paginator.count == 10000
        assert [r.pk for r in response.context['page']] == expected[:24]
        if body is None:
            body = response.content
        assert response.content == body
        assert projection.definitions_digest() == digest and projection.supported()
        route = response.wsgi_request._publication_route
        assert route['route'] == 'projection'
        assert route['candidate_stats']['positive'] == 10000
        assert route['candidate_stats']['native_fallback'] == 0
        return route

    for mode in ['values', 'sql']:
        with strategy(monkeypatch, mode):
            equivalent(client.get('/es/'))
    before = stats_snapshot()
    samples = []
    for pair, order in enumerate([('values', 'sql'), ('sql', 'values')]*2):
        for mode in order:
            with strategy(monkeypatch, mode):
                start = time.perf_counter()
                response = client.get('/es/')
                seconds = time.perf_counter() - start
                route = equivalent(response)
            samples.append({'pair': pair, 'mode': mode, 'seconds': seconds, 'route': route})
    after = stats_snapshot()
    patterns, reads, cache = {}, {}, {}

    def sql_timer(execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            seconds = time.perf_counter() - start
            if sql not in cache:
                cache[sql] = query_pattern(sql)
            pattern = cache[sql]
            bucket = patterns.setdefault(pattern, {'calls': 0, 'total_time': 0.})
            bucket['calls'] += 1
            bucket['total_time'] += seconds
            if sql.lstrip().upper().startswith('SELECT') and 'set_config(' not in sql:
                reads.setdefault(pattern, (sql, params))
    start = time.perf_counter()
    with connection.execute_wrapper(sql_timer):
        observed = client.get('/es/')
    observed_seconds = time.perf_counter() - start
    equivalent(observed)
    ordered = sorted(patterns, key=lambda p: patterns[p]['total_time'], reverse=True)
    selected = [p for p in ordered if p in reads][:5]
    plans = []
    for pattern in selected:
        sql, params = reads[pattern]
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            # The population SELECT uses the existing request-local jit=off
            # helper. Match that setting for its plan, without changing server.
            if '_sql_publication_positive' in sql:
                cursor.execute('SET LOCAL jit=off')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) ' + sql, params)
            plan = redact_plan(cursor.fetchone()[0])
        plans.append({'query_pattern': pattern, 'plan': plan})
    values_median = statistics.median(s['seconds'] for s in samples if s['mode']=='values')
    sql_median = statistics.median(s['seconds'] for s in samples if s['mode']=='sql')
    pairs = [{s['mode']: s['seconds'] for s in samples if s['pair']==p} for p in range(4)]
    deltas = [p['values']-p['sql'] for p in pairs]
    median_delta = statistics.median(deltas)
    report = {'variant': variant, 'candidates': 10000, 'source_fingerprint': digest,
              'ordered_native_population_sha256': expected_digest,
              'full_population_equality_both_strategies': True,
              'statistics_before': before, 'statistics_after': after,
              'statistics_endpoints_equal': before == after,
              'samples': samples, 'median_values_seconds': values_median,
              'median_sql_seconds': sql_median, 'paired_delta_seconds': deltas,
              'material_effect': median_delta>=.25 and median_delta>=.20*values_median and sum(d>0 for d in deltas)>=3,
              'sql_observed_request_seconds': observed_seconds,
              'queries': sum(v['calls'] for v in patterns.values()),
              'sql_execute_seconds': sum(v['total_time'] for v in patterns.values()),
              'dominant_sql': [{'query_pattern':p, **patterns[p], 'mean_time':patterns[p]['total_time']/patterns[p]['calls']} for p in ordered],
              'separate_readonly_plans': plans,
              'scope': 'Four paired AB/BA unprofiled DjangoClient controls, same dataset/host; ANALYZE all own fixture tables before native oracle/warmup. Complete ordered population compared to native outside timing. Stable principal stats endpoints do not prove all resources stationary. Same current code with explicit values or SQL representation selection; not a comparison to historical control wall times. Separate normalized SQL request and top5 read-only EXPLAIN after all controls; main SELECT jit off matching its helper. No parameters/text/IDs exported. Plans per-node actual rows and loops are not request SQL rows_scanned or ORM constructions.',
              'not_measured': ['per-rule times','model constructions','causal observer overhead','DB CPU/RSS/waits/locks/IO','SQL rows_returned/affected/scanned','current concurrent capacity','current route coverage outside normal listing','100/1000 matrix']}
    record_property('sql_candidate_comparison', report)
    Path(os.environ['SQL_PROOF_COST_OUTPUT'],variant+'.json').write_text(json.dumps(report,indent=2)+'\n')
