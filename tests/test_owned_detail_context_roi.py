"""Owned A/A/C WSGI evaluation for integrated RR detail versus frozen native."""
import gc
import hashlib
import json
import statistics
import time
from pathlib import Path

import pytest
from django.core import signing
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.template import Template
from django.test import RequestFactory
from django.test.utils import _TestState
from owned_detail_context import build_detail_context_prototype, patch_detail_view
from owned_detail_native_reference import build_native_detail_reference
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import PublicationDirty
from config.worker_startup import prepare_static_structures
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_detail_context_roi(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_detail_context_roi.py'
               for x in request.config.args):
        pytest.skip('Explicit own WSGI detail diagnostic only')
    request.getfixturevalue('directory')
    data = populate(10000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    routes = ['/es/listing/' + data['sample_ids'][0] + '/',
              '/en/listing/' + data['sample_ids'][-1] + '/']
    prepare_static_structures()
    monkeypatch.setattr(Template, '_render', _TestState.saved_data.template_render)
    stamp=signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self:stamp)
    assert gc.isenabled() and gc.get_debug()==0
    flags=gc.isenabled(),gc.get_debug(),gc.get_threshold()
    native, candidate=build_native_detail_reference(),build_detail_context_prototype()
    handler,factory=WSGIHandler(),RequestFactory()

    def call(route):
        status=[]
        def begin(value,headers,exc_info=None):
            status.append((value,dict(headers)))
        response=handler(factory.get(route).environ,begin)
        try:
            body=b''.join(response)
        finally:
            response.close()
        assert status[0][0].startswith('200 ')
        assert status[0][1]['Cache-Control']=='no-store'
        return hashlib.sha256(body).hexdigest()

    signatures={route:call(route) for route in routes}
    samples,preparation=[],[]
    modes=dict.fromkeys('ABC',0)
    for route in routes:
        for block,order in enumerate(['ABC','BCA','CAB']):
            for arm in order:
                implementation=candidate if arm=='C' else native
                def observed_view(*args,**kwargs):
                    modes[arm]+=1
                    return implementation(*args,**kwargs)
                with monkeypatch.context() as patch:
                    patch_detail_view(patch,observed_view)
                    connection.close()
                    gc.collect()  # Between arms only, outside warmup and measurements.
                    for _ in range(6):
                        assert call(route)==signatures[route]
                    with connection.cursor() as cursor:
                        cursor.execute('SELECT pg_backend_pid()')
                        pid=cursor.fetchone()[0]
                    preparation.append(dict(route=route,block=block,arm=arm,backend_pid=pid))
                    for repeat in range(16):
                        counts={'sql':0,'pids':set()}
                        def counted(execute,sql,params,many,context):
                            counts['sql']+=1
                            counts['pids'].add(context['connection'].connection.info.backend_pid)
                            return execute(sql,params,many,context)
                        wall,cpu=time.perf_counter(),time.thread_time()
                        with connection.execute_wrapper(counted):
                            signature=call(route)
                        wall,cpu=time.perf_counter()-wall,time.thread_time()-cpu
                        assert signature==signatures[route]
                        assert counts['pids']=={pid}
                        samples.append(dict(route=route,block=block,arm=arm,repeat=repeat,
                                            wall=wall,cpu=cpu,sql=counts['sql']))
    assert len(samples)==288 and modes==dict.fromkeys('ABC',132)
    assert flags==(gc.isenabled(),gc.get_debug(),gc.get_threshold())
    assert not PublicationDirty.objects.exists()
    comparisons=[]
    for route in routes:
        rows=[r for r in samples if r['route']==route]
        means={arm:{metric:statistics.mean(r[metric] for r in rows if r['arm']==arm)
                    for metric in ['wall','cpu']} for arm in 'ABC'}
        relative={metric:means['C'][metric]/statistics.mean(means[a][metric] for a in 'AB')
                  for metric in ['wall','cpu']}
        stable=all(abs(means['A'][m]-means['B'][m])/
                   statistics.mean(means[a][m] for a in 'AB')<=.10 for m in ['wall','cpu'])
        gains=[]
        for block in range(3):
            base=statistics.mean(r['wall'] for r in rows if r['block']==block and r['arm'] in 'AB')
            proposed=statistics.mean(r['wall'] for r in rows if r['block']==block and r['arm']=='C')
            gains.append(proposed<=base)
        comparisons.append(dict(route=route,means=means,candidate_to_reference=relative,
                                control_stable=stable,wall_nonregression_blocks=gains,
                                eligible_for_next_controls=stable and relative['wall']<=.90
                                and relative['cpu']<=1.05 and sum(gains)>=2))
    out=Path(request.config.getoption('--gate-timings-output')).parent
    result=dict(samples=samples,preparation=preparation,comparisons=comparisons,
                eligible_for_next_controls=all(c['eligible_for_next_controls'] for c in comparisons),
                limits='Actual WSGI/Django with synthetic own PG10k, integrated RR callback. '
                       'Fixed signing timestamp only, real signature/payload and exact body. '
                       'Normal GC; collection before warmup only. A/B identical native code. '
                       'No TCP/Gunicorn/concurrency/Beat/upload; DB CPU/RSS unmeasured. '
                       'Prerequisites for follow-up: AA<=10% wall/CPU, wall saving>=10% both routes, '
                       'CPU regression<=5%, nonregression>=2/3 blocks. '
                       'PASS is completion/parity, not ROI, N2, p95 or product adoption.')
    (out/'detail-context-roi.json').write_text(json.dumps(result,indent=2)+'\n')
    record_property('detail_context_roi',json.dumps({'reads':288,'eligible':result['eligible_for_next_controls']}))
