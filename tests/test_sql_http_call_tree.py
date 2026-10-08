"""Opt-in C call-tree attribution; no wrapping of audited rules."""
import cProfile
import gc
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('HTTP_CALL_TREE_OUTPUT'), reason='Explicit owned attribution only')]


def identity(code):
    if isinstance(code, str):
        return code
    return f'{code.co_filename}:{code.co_firstlineno}:{code.co_name}'


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_current_complete_http_call_tree(request, monkeypatch, record_property, variant):
    client = request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        rows = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += ' '+suffix
            if row.description_alternative:
                row.description_alternative += ' '+suffix
            row.telegram = 'bench'+suffix
        Revision.objects.bulk_update(rows, ['description', 'description_alternative', 'telegram'], batch_size=250)
        del rows
    assert connection.vendor == 'postgresql' and projection.supported()
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE '+connection.ops.quote_name(table))
    original = projection.ProjectedPublication.__init__
    def indexed(self, query, **kwargs):
        kwargs['sql_text_membership'] = True
        return original(self, query, **kwargs)
    monkeypatch.setattr(projection.ProjectedPublication, '__init__', indexed)
    digest = projection.definitions_digest()
    warm = client.get('/es/')
    body = warm.content
    route = warm.wsgi_request._publication_route
    ids = [row.pk for row in warm.context['page']]
    assert route['route']=='projection' and route['candidate_stats']['positive']==10000
    assert route['candidate_stats']['text_membership'] is True
    del warm
    before = stats_snapshot()
    samples = []
    for pair, order in enumerate([('plain','profiled'),('profiled','plain')]*2):
        for mode in order:
            profile = cProfile.Profile()
            gc_events, gc_start = [], {}
            def gc_observer(phase, info):
                now = time.perf_counter()
                if phase == 'start':
                    gc_start[info['generation']] = now
                else:
                    began = gc_start.pop(info['generation'], now)
                    gc_events.append({'generation':info['generation'], 'seconds':now-began,
                        'start_relative_request':began-start,'collected':info['collected'],
                        'uncollectable':info['uncollectable']})
            counts_before = gc.get_count()
            start = time.perf_counter()
            if mode == 'profiled':
                gc.callbacks.append(gc_observer)
                profile.enable()
            try:
                response = client.get('/es/')
            finally:
                profile.disable()
                if mode == "profiled":
                    gc.callbacks.remove(gc_observer)
            seconds = time.perf_counter()-start
            assert response.status_code==200 and response.content==body
            assert response.context['page'].paginator.count==10000
            assert [row.pk for row in response.context['page']]==ids
            assert response.wsgi_request._publication_route==route
            assert projection.definitions_digest()==digest and projection.supported()
            rules = []
            if mode == 'profiled':
                for entry in sorted(profile.getstats(),key=lambda x:x.inlinetime,reverse=True):
                    rules.append({'rule':identity(entry.code), 'calls':entry.callcount,
                        'recursive_calls':entry.reccallcount, 'inclusive_time':entry.totaltime,
                        'exclusive_time':entry.inlinetime,
                        'mean_exclusive_time':entry.inlinetime/entry.callcount,
                        'max_exclusive_time':'not_measured', 'p95_exclusive_time':'not_measured',
                        'instrumented_direct_children':[{'rule':identity(child.code),
                            'calls':child.callcount,'inclusive_time':child.totaltime,
                            'exclusive_time':child.inlinetime} for child in entry.calls or []]})
            samples.append({'pair':pair,'mode':mode,'seconds':seconds,'rules':rules,
                'gc_counts_before':counts_before,'gc_counts_after':gc.get_count(),
                'gc_events':gc_events if mode=='profiled' else 'not_measured'})
            del response
    after = stats_snapshot()
    medians={m:statistics.median(x['seconds'] for x in samples if x['mode']==m) for m in ['plain','profiled']}
    deltas=[next(x['seconds'] for x in samples if x['pair']==p and x['mode']=='profiled')-
            next(x['seconds'] for x in samples if x['pair']==p and x['mode']=='plain') for p in range(4)]
    result={'variant':variant,'stage':'complete','source_fingerprint':digest,'route':route,
        'samples':samples,'request_medians':medians,'paired_observed_minus_plain':deltas,
        'observation_compatible':abs(statistics.median(deltas))<=max(.05,.1*medians['plain']),
        'statistics_before':before,'statistics_after':after,'statistics_endpoints_equal':before==after,
        'scope':'Four counterbalanced plain/cProfile pairs, current full-capture indexed-text path, listing10000 repeated/diverse. Native equivalence reused from reviewed same-source N1/cost; status/body/page/count/route/fingerprint checked per sample. No native function wrapping. C profiler observes Python and C calls; inline/exclusive subtracts traced children once, recursion handled by profiler; inclusive entries overlap lazy SQL/fetch and must not be summed. Generator call counts are resumed segments. No SQL normalization callback in measured samples. GC callbacks in profiled samples record wall intervals, overlap call events and do not identify allocation causality; plain requests have neither profiler nor callbacks. No collection disabled or forced. Indexed candidate explicitly selected only in this diagnostic; public default restored to row proof after insufficient joint HTTP criterion. cProfile changes timings; profiled totals are not operational latency or savings. Compatibility is numerical, not causal overhead. Function labels only, no values/SQL params exported. New uncertainty: locate remaining measured request work below prepare/materialization boundaries; only directly dominant consistent entries justify next candidate, not total minus SQL.',
        'not_measured':['per-call max/p95 exclusive','SQL normalized pattern metrics in this focused run (reuse prior cost)','SQL rows_returned/affected/scanned','ORM constructions (function calls are not rows)','CPU/RSS/waits/IO PostgreSQL','causal profiler overhead','concurrent capacity']}
    Path(os.environ['HTTP_CALL_TREE_OUTPUT'],variant+'.json').write_text(json.dumps(result,indent=2)+'\n')
    record_property('call_tree_summary',{k:v for k,v in result.items() if k!='samples'})
