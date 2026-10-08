"""Opt-in whole-request contrast: native capture, scalar capture, scalar plus text index."""
import json
import os
import statistics
import time
from contextlib import contextmanager
from functools import wraps
from pathlib import Path

import pytest
from django.db import connection, transaction
from django.db.backends.postgresql.psycopg_any import BaseTzLoader
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
    not os.getenv('SCALAR_COST_OUTPUT'), reason='Explicit isolated comparison only')]


@contextmanager
def strategy(monkeypatch, mode):
    original = projection.ProjectedPublication.__init__
    with monkeypatch.context() as patch:
        def select(self, query, **kwargs):
            kwargs['sql_legacy_text'] = True
            kwargs['sql_text_membership'] = mode == 'indexed'
            kwargs['sql_scalar_capture'] = mode != 'before'
            kwargs['page_number'] = None
            return original(self, query, **kwargs)
        patch.setattr(projection.ProjectedPublication, '__init__', select)
        yield


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_full_scalar_capture_paired_cost(request, monkeypatch, record_property, variant):
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

    for mode in ['before', 'scalar', 'indexed']:
        with strategy(monkeypatch, mode):
            for label, path, data in families:
                query = discovery.candidates(data)
                p = projection.ProjectedPublication(query, sql=True)
                assert p.visible_ids(query) == expected[label]
                assert p.stats["text_membership"] == (mode == "indexed")
                equivalent(client.get(path), label)
    before = stats_snapshot()
    samples = []
    for pair, order in enumerate([('before','scalar','indexed'),('indexed','scalar','before'),
                                 ('scalar','indexed','before'),('before','indexed','scalar'),
                                 ('indexed','before','scalar'),('scalar','before','indexed'),
                                 ('before','scalar','indexed'),('indexed','scalar','before')]):
        for label, path, _ in families:
            for mode in order:
                with strategy(monkeypatch, mode):
                    start = time.perf_counter()
                    response = client.get(path)
                    seconds = time.perf_counter()-start
                    route = equivalent(response, label)
                    assert route["candidate_stats"]["text_membership"] == (mode == "indexed")
                    assert route["candidate_stats"]["scalar_capture"] == (mode != "before")
                samples.append({'pair': pair, 'family': label, 'mode': mode, 'seconds': seconds, 'route': route})
    after = stats_snapshot()
    report = {'variant': variant, 'samples': samples, 'source_fingerprint': digest,
              'statistics_before': before, 'statistics_after': after,
              'statistics_endpoints_equal': before == after, 'stage': 'controls_complete',
              'full_ordered_native_population_equal_both_families_and_modes': True}
    output = Path(os.environ['SCALAR_COST_OUTPUT'], variant+'.json')

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
    # Route probes document the combined candidate explicitly.
    with strategy(monkeypatch, 'indexed'):
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
                  for m in ['before','scalar','indexed']} for f, _, _ in families}
    def comparison(before_mode, after_mode, minimum, fraction):
        deltas = [sum(next(x['seconds'] for x in samples if x['pair']==pair and x['family']==f and x['mode']==before_mode)
                      -next(x['seconds'] for x in samples if x['pair']==pair and x['family']==f and x['mode']==after_mode)
                      for f,_,_ in families)/2 for pair in range(8)]
        reference=sum(v[before_mode] for v in medians.values())/2
        no_regression=all(v[after_mode]-v[before_mode]<=max(.05,.1*v[before_mode]) for v in medians.values())
        return {'paired_mean_family_deltas':deltas,
                'effect':statistics.median(deltas)>=max(minimum,fraction*reference)
                        and sum(x>0 for x in deltas)>=6 and no_regression}

    # Direct loader observation is SEPARATE from timing comparisons and plans.
    decoder_samples=[]
    for mode in ['before','scalar','indexed']:
        calls,decoder_seconds=0,0.
        original=BaseTzLoader.load
        def observed_load(self, value):
            nonlocal calls,decoder_seconds
            start=time.perf_counter()
            try:
                return original(self,value)
            finally:
                calls+=1
                decoder_seconds+=time.perf_counter()-start
        with strategy(monkeypatch,mode), monkeypatch.context() as patch:
            patch.setattr(BaseTzLoader,'load',observed_load)
            assert projection.supported() and projection.definitions_digest()==digest
            start=time.perf_counter()
            measured=client.get('/es/')
            elapsed=time.perf_counter()-start
            route=equivalent(measured,'listing')
        decoder_samples.append({'mode':mode,'calls':calls,'inclusive_seconds':decoder_seconds,
                                'request_seconds':elapsed,'route':route})
    assert decoder_samples[0]['calls']-decoder_samples[1]['calls']==10000
    assert decoder_samples[1]['calls']==decoder_samples[2]['calls']
    report.update(stage='complete',route_medians=medians,
        scalar_effect=comparison('before','scalar',.05,.05),
        additional_index_effect=comparison('scalar','indexed',.05,.05),
        combined_effect=comparison('before','indexed',.10,.15),
        separate_decoder_observation=decoder_samples,separate_readonly_plans=plans,
        scope='Eight counterbalanced triplets per listing/search, same data/stats/schema. A=old typed ORM capture, B=all scalar text IDs/bool with sort values retained only in SQL, C=B plus experimental text-index membership. All10000 candidates evaluated and captured before unknown native validation/count/page; no compact page path. Complete ordered native oracle outside timers for every mode; same authority/JIT/search. Scalar A-B and additional index B-C require >=max(.05s,5%), combined A-C >=max(.10s,15%), >=6/8 favorable and no family regression >max(.05s,10%), BOTH fixtures. More triplets prefixed due observed temporal variation, not reinterpretation/repetition of the rejected index experiment: transfer mechanism is new. Six plain/coarse route probes describe C; top5 read-only plans separate; actual timestamp decoder calls separately observed AFTER timed controls/plans, body/count/route/footprint preserved. Loader inclusive time overlaps fetch/request, no subtraction as validation or CPU PG. GC neither forced nor disabled; causal allocations/GC savings not inferred. Captured rows are explicit fetch lengths only for that statement; all other row metrics absent. No capacity/extra workers/cache.',
        not_measured=['per-rule max/p95 exclusive','common100/1000 matrix','current model constructions and full validation profile','causal profiler/GC overhead','DB CPU/RSS/waits/locks/IO','SQL rows_affected/scanned and rows_returned for other statements','concurrent capacity','index write/storage overhead beyond earlier isolated sizes'])
    report.pop('pending_probe',None)
    persist()
    record_property('scalar_capture_comparison',report)
