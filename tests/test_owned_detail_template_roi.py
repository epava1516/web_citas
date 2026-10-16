"""Owned WSGI first-connection comparison, current detail versus resolved query template."""
import gc
import hashlib
import json
import os
import statistics
import subprocess
import time
from pathlib import Path

import pytest
from django.core import signing
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from owned_detail_context import patch_detail_view
from owned_detail_query_template import build_detail_template_view
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import moderation_views, publication_state
from config.worker_startup import prepare_static_structures
from scripts.benchmark_owned_backend_cpu import backend_snapshot, owned_backend
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_detail_template_roi(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_detail_template_roi.py'
               for x in request.config.args):
        pytest.skip('Explicit owned first-connection detail diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out/'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-'+run['id']
    inspection = json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
    request.getfixturevalue('directory')
    data = populate(10000)
    publication_state.refresh_all()
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: stamp)
    original_view = moderation_views.public_detail
    proposed_view, template, retained = build_detail_template_view()
    selected = [original_view]
    def dispatch(*args, **kwargs):
        return selected[0](*args, **kwargs)
    patch_detail_view(monkeypatch, dispatch)
    handler, factory = WSGIHandler(), RequestFactory()
    routes = ['/es/listing/'+data['sample_ids'][0]+'/',
              '/en/listing/'+data['sample_ids'][-1]+'/']
    flags = gc.isenabled(), gc.get_threshold(), gc.get_debug()
    assert flags[0] and flags[2] == 0

    def call(route):
        statuses = []
        def begin(status, headers, exc_info=None):
            statuses.append((status,dict(headers)))
        response = handler(factory.get(route).environ, begin)
        try:
            body = b''.join(response)
        finally:
            response.close()
        assert statuses[0][0].startswith('200 ') and statuses[0][1]['Cache-Control']=='no-store'
        return hashlib.sha256(body).hexdigest()

    signatures = {route:call(route) for route in routes}
    samples, preparations = [], []
    for route in routes:
        for block, order in enumerate(['ABC','BCA','CAB']*4):
            for arm in order:
                started = time.perf_counter()
                selected[0] = proposed_view if arm=='C' else original_view
                connection.close()
                gc.collect()  # Prior-arm garbage only, outside every timed request.
                connection.ensure_connection()
                raw = connection.connection
                native_factory, threshold = raw.cursor_factory, raw.prepare_threshold
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pid = cursor.fetchone()[0]
                identity = owned_backend(run, inspection, pid)

                def cpu():
                    snap = backend_snapshot(identity)
                    try:
                        fields = list(map(int,Path(f'/proc/{identity["pid"]}/schedstat').read_text().split()))
                        assert len(fields)==3 and fields[0]>=0
                        return snap | {'runtime_ns':fields[0] or None, 'wait_ns':fields[1]}
                    except OSError:
                        return snap | {'runtime_ns':None, 'wait_ns':None}

                preparations.append(dict(route=route,block=block,arm=arm,backend_pid=pid,
                                         wall=time.perf_counter()-started))
                for phase, count in [('first6',6),('warm12',12)]:
                    before = cpu()
                    measured = []
                    for _ in range(count):
                        counts = [0]
                        def counted(execute, sql, params, many, context):
                            assert context['connection'].connection.info.backend_pid==pid
                            counts[0]+=1
                            return execute(sql,params,many,context)
                        wall, used = time.perf_counter(), time.thread_time()
                        with connection.execute_wrapper(counted):
                            digest = call(route)
                        measured.append(dict(wall=time.perf_counter()-wall,
                                             cpu=time.thread_time()-used,sql=counts[0]))
                        assert digest==signatures[route]
                        assert raw.cursor_factory is native_factory and raw.prepare_threshold==threshold
                    after = cpu()
                    precise = before['runtime_ns'] is not None and after['runtime_ns'] is not None
                    if precise:
                        assert after['runtime_ns']>before['runtime_ns']
                        runtime = (after['runtime_ns']-before['runtime_ns'])/1e9
                        waiting = (after['wait_ns']-before['wait_ns'])/1e9
                    else:
                        runtime = ((after['user_ticks']+after['system_ticks'])-
                                   (before['user_ticks']+before['system_ticks']))/os.sysconf('SC_CLK_TCK')
                        waiting = None
                    samples.append(dict(route=route,block=block,arm=arm,phase=phase,reads=measured,
                                        backend_runtime_seconds=runtime, backend_wait_seconds=waiting,
                                        high_resolution_runtime=precise,
                                        before=before,after=after))
                with connection.cursor() as cursor:
                    cursor.execute('SHOW plan_cache_mode')
                    assert cursor.fetchone()[0]=='auto'
    assert flags==(gc.isenabled(),gc.get_threshold(),gc.get_debug())
    assert len(samples)==144 and sum(len(x['reads']) for x in samples)==1296
    comparisons = []
    for route in routes:
        metrics = {}
        for phase in ['first6','warm12','all18']:
            metrics[phase] = {}
            for arm in 'ABC':
                selected = [x for x in samples if x['route']==route and x['arm']==arm
                            and (phase=='all18' or x['phase']==phase)]
                reads = [r for x in selected for r in x['reads']]
                metrics[phase][arm] = dict(
                    wall=statistics.mean(x['wall'] for x in reads),
                    cpu=statistics.mean(x['cpu'] for x in reads),
                    backend_runtime=sum(x['backend_runtime_seconds'] for x in selected)/len(reads),
                )
        stable = all(statistics.mean([values['A'][metric],values['B'][metric]]) > 0 and
                     abs(values['A'][metric]-values['B'][metric]) /
                     statistics.mean([values['A'][metric],values['B'][metric]]) <= .10
                     for values in metrics.values() for metric in ['wall','cpu','backend_runtime'])
        ratios = {phase:{metric:(values['C'][metric]/statistics.mean([values['A'][metric],values['B'][metric]])
                                 if statistics.mean([values['A'][metric],values['B'][metric]]) > 0 else None)
                         for metric in ['wall','cpu','backend_runtime']} for phase,values in metrics.items()}
        nonregression = []
        for block in range(12):
            means = {arm:statistics.mean(r['wall'] for x in samples if x['route']==route
                                        and x['block']==block and x['phase']=='first6' and x['arm']==arm
                                        for r in x['reads']) for arm in 'ABC'}
            nonregression.append(means['C']<=statistics.mean([means['A'],means['B']]))
        precise = all(x['high_resolution_runtime'] for x in samples if x['route']==route)
        total_stable = all(abs(metrics['all18']['A'][metric]-metrics['all18']['B'][metric]) /
                           statistics.mean([metrics['all18']['A'][metric],metrics['all18']['B'][metric]]) <= .05
                           for metric in ['wall','cpu','backend_runtime'])
        eligible = (precise and stable and total_stable and ratios['first6']['wall']<=1.05 and ratios['all18']['wall']<=.95
                    and ratios['warm12']['wall']<=1.05 and ratios['all18']['cpu']<=.90
                    and ratios['all18']['backend_runtime']<=1.05 and sum(nonregression)>=8)
        comparisons.append(dict(route=route,metrics=metrics,control_stable=stable,
                                candidate_to_reference=ratios,total_control_stable=total_stable,nonregression_blocks=nonregression,
                                high_resolution_runtime=precise,
                                eligible_for_followup=eligible))
    assert len({x['backend_pid'] for x in preparations})==72
    assert all(q._result_cache is None for q in retained)
    result = dict(template_cache=str(template.cache_info()),samples=samples,preparations=preparations,comparisons=comparisons,
                  eligible_for_followup=all(x['eligible_for_followup'] for x in comparisons),
                  limits='Owned synthetic10k, actual WSGI without TCP/workers/upload/Beat. '
                         'Both routes agency/agency clone.12balanced blocks/route, A/B same current '
                         'product,C resolved unevaluated detail query template.6first+12warm,72fresh backends, Python '
                         'and shared PG buffers already warm. GC normal, collect only before first '
                         'request per arm. Timestamp component fixed equally, real signing. '
                         'Own exact backend schedstat runtime, not cgroup CPU; parallel workers '
                         'excluded if any. Tick counters retained with coarse resolution. '
                         'Preparation separately recorded, no operational warmup or p95 acceptance.')
    (out/'detail-template-roi.json').write_text(json.dumps(result,indent=2)+'\n')
    record_property('detail_template_roi',json.dumps({'reads':1296,'blocks':12,'routes':2}))
