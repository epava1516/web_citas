"""Opt-in equivalent controls for complete-proof page transfer."""
import json
import os
import statistics
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import pytest
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projected_publication import native_ids
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication import normalized_detail_body
from test_sql_publication_bulk_cost import redact_plan

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('COMPACT_COST_OUTPUT'), reason='Explicit isolated comparison only')]


@contextmanager
def strategy(monkeypatch, mode):
    original = projection.ProjectedPublication.__init__
    with monkeypatch.context() as patch:
        def select(self, query, **kwargs):
            # These comparison requests are all first-page probes. Production
            # selection stays full after the insufficient historical effect.
            kwargs['page_number'] = 1 if mode == 'after' else None
            return original(self, query, **kwargs)
        patch.setattr(projection.ProjectedPublication, '__init__', select)
        yield


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_certified_page_paired_cost(request, monkeypatch, record_property, variant):
    client = request.getfixturevalue('directory')
    dataset = populate(10000)
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
    digest = projection.definitions_digest()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    families = [('listing', '/es/', {}), ('search', '/es/?q=photography', {'q': 'photography'})]
    expected = {label: native_ids(discovery.candidates(data, stored_search=False)) for label, _, data in families}
    bodies = {}

    def equivalent(response, label):
        assert response.status_code == 200
        assert response.context['page'].paginator.count == len(expected[label])
        assert [r.pk for r in response.context['page']] == expected[label][:24]
        if label not in bodies:
            bodies[label] = response.content
        assert response.content == bodies[label]
        route = response.wsgi_request._publication_route
        assert route['route'] == 'projection'
        assert route['candidate_stats']['positive'] == 10000
        assert route['candidate_stats']['native_fallback'] == 0
        assert projection.definitions_digest() == digest and projection.supported()
        return route

    for mode in ['before', 'after']:
        with strategy(monkeypatch, mode):
            for label, path, data in families:
                query = discovery.candidates(data)
                p = projection.ProjectedPublication(query, sql=True)
                assert p.visible_ids(query) == expected[label]
                equivalent(client.get(path), label)
    before = stats_snapshot()
    samples = []
    for pair, order in enumerate([('before','after'),('after','before')]*2):
        for label, path, _ in families:
            for mode in order:
                with strategy(monkeypatch, mode):
                    start = time.perf_counter()
                    response = client.get(path)
                    seconds = time.perf_counter()-start
                    route = equivalent(response, label)
                samples.append({'pair': pair, 'family': label, 'mode': mode, 'seconds': seconds, 'route': route})
    after = stats_snapshot()
    report = {'variant': variant, 'samples': samples, 'source_fingerprint': digest,
              'statistics_before': before, 'statistics_after': after,
              'statistics_endpoints_equal': before == after, 'stage': 'controls_complete',
              'full_ordered_native_population_equal_both_families_and_modes': True}
    output = Path(os.environ['COMPACT_COST_OUTPUT'], variant+'.json')

    def persist():
        output.write_text(json.dumps(report,indent=2)+'\n')
    persist()
    patterns, reads, cache, stages = {}, {}, {}, {}

    def observer(name, original):
        @wraps(original)
        def observed(*args, **kwargs):
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                stages[name] = stages.get(name, 0.) + time.perf_counter()-start
        return observed

    def sql_timer(execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed = time.perf_counter()-start
            if sql not in cache:
                cache[sql] = query_pattern(sql)
            pattern = cache[sql]
            bucket = patterns.setdefault(pattern, {'calls': 0, 'total_time': 0.})
            bucket['calls'] += 1
            bucket['total_time'] += elapsed
            if (sql.lstrip().upper().startswith('SELECT') or sql.lstrip().upper().startswith('WITH \"_PUBLICATION_CERTIFIED\"')) and 'set_config(' not in sql:
                reads.setdefault(pattern, (sql, params))
    probes, combined = [], {}
    paths = [('listing-es', '/es/'), ('listing-en', '/en/'),
             ('search-es', '/es/?q=photography'), ('search-en', '/en/?q=synthetic'),
             ('detail-es', '/es/listing/'+dataset['sample_ids'][0]+'/'),
             ('detail-en', '/en/listing/'+dataset['sample_ids'][-1]+'/')]
    for label, path in paths:
        report['pending_probe'] = label
        persist()
        start = time.perf_counter()
        plain = client.get(path)
        plain_seconds = time.perf_counter()-start
        patterns, stages = {}, {}
        with monkeypatch.context() as patch:
            for name, owner, attribute in [('prepare', projection.ProjectedPublication, '__init__'),
                                          ('eligible_ids', projection.ProjectedPublication, 'visible_ids'),
                                          ('definitions_digest', projection, 'definitions_digest'),
                                          ('render', discovery, 'render')]:
                patch.setattr(owner, attribute, observer(name, getattr(owner, attribute)))
            assert projection.definitions_digest() == digest and projection.supported()
            stages = {}
            start = time.perf_counter()
            with connection.execute_wrapper(sql_timer):
                measured = client.get(path)
            elapsed = time.perf_counter()-start
        assert plain.status_code == measured.status_code == 200
        assert (normalized_detail_body(plain) == normalized_detail_body(measured)
                if label.startswith('detail') else plain.content == measured.content)
        assert getattr(plain.wsgi_request, '_publication_route', None) == getattr(measured.wsgi_request, '_publication_route', None)
        probes.append({'route': label, 'plain_seconds': plain_seconds, 'observed_seconds': elapsed,
            'stages': stages, 'publication_route': getattr(measured.wsgi_request, '_publication_route', 'not_measured'),
            'queries': sum(v['calls'] for v in patterns.values()), 'sql_execute_seconds': sum(v['total_time'] for v in patterns.values()),
            'dominant_sql': [{'query_pattern':p, **v, 'mean_time':v['total_time']/v['calls']}
                            for p,v in sorted(patterns.items(),key=lambda x:x[1]['total_time'],reverse=True)]})
        for pattern, v in patterns.items():
            bucket = combined.setdefault(pattern, {'calls': 0, 'total_time': 0.})
            bucket['calls'] += v['calls']
            bucket['total_time'] += v['total_time']
        report['route_probes'] = probes
        persist()
    plans = []
    for pattern in [p for p in sorted(combined,key=lambda p:combined[p]['total_time'],reverse=True) if p in reads][:5]:
        sql, params = reads[pattern]
        with transaction.atomic(), connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            if '_sql_publication_positive' in sql or ('_pv_check_status' in sql and 'listings_listing' in sql):
                cursor.execute('SET LOCAL jit=off')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+sql, params)
            plan = redact_plan(cursor.fetchone()[0])
        plans.append({'query_pattern': pattern, 'plan': plan})
    medians = {f:{m:statistics.median(x['seconds'] for x in samples if x['family']==f and x['mode']==m)
                  for m in ['before','after']} for f, _, _ in families}
    deltas = [sum(next(x['seconds'] for x in samples if x['pair']==pair and x['family']==f and x['mode']=='before')
                  - next(x['seconds'] for x in samples if x['pair']==pair and x['family']==f and x['mode']=='after')
                  for f, _, _ in families)/2 for pair in range(4)]
    reference = sum(v['before'] for v in medians.values())/2
    effect = statistics.median(deltas)>=.10 and statistics.median(deltas)>=.20*reference and sum(x>0 for x in deltas)>=3
    no_regression = all(v['after']-v['before']<=max(.05,.1*v['before']) for v in medians.values())
    report.update(stage='complete', route_medians=medians, paired_mean_family_delta_seconds=deltas,
        material_effect=effect and no_regression, 
        separate_readonly_plans=plans,
        scope='Four AB/BA pairs per listing/search family, same 10000 data/stats/schema/code. Before captures all IDs and proofs; after reduces transferred IDs only when complete materialized population proof is sufficient for every candidate. Unknown or duplicate returns full capture. Same full ordered native oracle outside timing. Complete proof precedes count/page selection. Separate six plain/coarse probes, then top5 read-only plans including the generated WITH SELECT and page reads, jit off matching implementation. Coarse callbacks preserve rule footprint/actual route/body; phases contain nested SQL/lazy work, never sum or total-SQL as validation. eligible_ids callback absent means not invoked by certified-page path, not omitted residual validation. Paginator count and header counters describe certified population; captured IDs are application values. Only explicitly fetched certified-statement rows (including its auxiliary header) are measured SQL rows_returned for that statement, never rows_scanned or all queries. No sensitive parameters/text/IDs exported. Causal overhead/concurrent capacity absent.',
        not_measured=['per-rule SQL row times','current common 100/1000 matrix','model constructions','per-rule validation on these requests','causal overhead','DB CPU/RSS/waits/locks/IO','SQL rows_returned for other statements; rows_affected/scanned for all statements','current concurrent capacity','schema write/storage overhead'])
    report.pop('pending_probe',None)
    persist()
    record_property('certified_page_comparison',report)
