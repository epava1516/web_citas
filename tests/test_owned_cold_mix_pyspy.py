"""Explicit py-spy first request and mixed-route diagnosis; not accepted timing."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.core import signing
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.test import RequestFactory
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

CHILD = r'''
import gc, hashlib, json, os, platform, sys, time
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
identity_stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split()
Path(payload['identity']).write_text(json.dumps({'pid':os.getpid(),'start_ticks':int(identity_stat[19])}))
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django
django.setup()
from django.conf import settings
from django.core import signing
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.test import RequestFactory
from apps.listings import moderation_views, public_validation
from apps.safety.canonical_kernel_loader import kernel_identity
from config.worker_startup import prepare_static_structures
assert settings.DEBUG is False
assert connection.force_debug_cursor is False
assert str(settings.MEDIA_ROOT)==payload['media_root']
assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
assert moderation_views.PublicationContext is public_validation.PublicationContext
identity = kernel_identity()
assert identity['mode']=='native-sealed'
prepare_static_structures()
stamp = payload['stamp']
signing.TimestampSigner.timestamp = lambda self: stamp
handler, factory = WSGIHandler(), RequestFactory()
flags = gc.isenabled(), gc.get_threshold(), gc.get_debug()
assert flags[0] and flags[2]==0
result = dict(completed=0,error_type=None,python=platform.python_version(),kernel=identity,
              debug=settings.DEBUG,force_debug_cursor=connection.force_debug_cursor,
              source_sha256=hashlib.sha256(Path('apps/listings/moderation_views.py').read_bytes()).hexdigest())
def read(route):
    statuses=[]
    def begin(status,headers,exc_info=None): statuses.append((status,dict(headers)))
    response=handler(factory.get(route).environ,begin)
    try: body=b''.join(response)
    finally: response.close()
    assert statuses[0][0].startswith('200 ')
    assert statuses[0][1]['Cache-Control']=='no-store'
    return hashlib.sha256(body).hexdigest()
def checked(route):
    wall,cpu=time.perf_counter(),time.thread_time()
    assert read(route)==signatures[route]
    result.setdefault('reads',[]).append({'route':route,'wall':time.perf_counter()-wall,'cpu':time.thread_time()-cpu})
    result['completed']+=1
def profile_first_request():
    checked(payload['routes'][0])
def profile_first_cycle_tail():
    for route in payload['routes'][1:]: checked(route)
def profile_later_requests():
    for _ in range(11):
        for route in payload['routes']: checked(route)
try:
    signatures=payload['signatures']
    assert connection.connection is None, 'No child DB reads before first request'
    started=time.monotonic()
    profile_first_request()
    first_done=time.monotonic()
    profile_first_cycle_tail()
    cycle_done=time.monotonic()
    profile_later_requests()
    result['profile_intervals']={'first':[started,first_done],
                                'tail':[first_done,cycle_done],
                                'later':[cycle_done,time.monotonic()]}
    assert flags==(gc.isenabled(),gc.get_threshold(),gc.get_debug())
    with connection.cursor() as cursor:
        cursor.execute('SHOW plan_cache_mode')
        assert cursor.fetchone()[0]=='auto'
    result['body_signatures']=signatures
except BaseException as error:
    result['error_type']=type(error).__name__
    raise
finally:
    connection.close()
    Path(payload['summary']).write_text(json.dumps(result,indent=2)+'\n')
# Work is complete, summary durable and DB closed before profiler ends its window.
time.sleep(120)
'''


SUPERVISOR = r'''
import ctypes,json,os,signal,subprocess,sys,time
from pathlib import Path
child,payload,out=map(Path,sys.argv[1:])
assert ctypes.CDLL(None,use_errno=True).prctl(36,1,0,0,0)==0
configuration=json.loads(payload.read_text())
tool=Path.home()/'.local/share/web-citas-diagnostics/venv/bin/py-spy'
completed=None
try:
    completed=subprocess.run([str(tool),'record','--duration','45','--rate','100','--gil',
        '--full-filenames','--format','speedscope','--output',str(out/'cold-mix-speedscope.json'),
        '--',sys.executable,str(child),str(payload)],capture_output=True,text=True,timeout=120)
    (out/'pyspy.stdout.log').write_text(completed.stdout)
    (out/'pyspy.stderr.log').write_text(completed.stderr)
finally:
    identity=json.loads(Path(configuration['identity']).read_text())
    pid=identity['pid'];stat=Path(f'/proc/{pid}/stat')
    if stat.exists():
        assert int(stat.read_text().split(') ',1)[1].split()[19])==identity['start_ticks']
        # py-spy normally already killed its completed idle child. Timeout/error cleanup
        # targets only the identified child of this isolated subreaper.
        if stat.read_text().split(') ',1)[1].split()[0]!='Z': os.kill(pid,signal.SIGKILL)
    deadline=time.monotonic()+5
    while True:
        reaped,status=os.waitpid(pid,os.WNOHANG)
        if reaped:break
        assert time.monotonic()<deadline
        time.sleep(.05)
    assert not stat.exists()
    receipt={'tool_exit':completed.returncode if completed else None,'pid':pid,
        'start_ticks':identity['start_ticks'],'wait_status':status,'pid_absent':True,
        'expected_teardown':'py-spy duration ends and kills completed idle child; isolated supervisor reaps it'}
    (out/'profiler-lifecycle.json').write_text(json.dumps(receipt,indent=2)+'\n')
assert completed.returncode==0
assert os.WIFSIGNALED(status) and os.WTERMSIG(status)==signal.SIGKILL
'''


def test_owned_cold_mix_pyspy(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_cold_mix_pyspy.py'
               for x in request.config.args):
        pytest.skip('Explicit owned current-detail py-spy diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    tool = Path.home()/'.local/share/web-citas-diagnostics/venv/bin/py-spy'
    version = subprocess.check_output([str(tool),'--version'],text=True).strip()
    assert version == 'py-spy 0.4.2'
    run = json.loads((out/'runner.json').read_text())
    name = os.environ['LOCAL_CI_POSTGRES_CONTAINER']
    assert name == 'web-modelos-ci-pg-'+run['id']
    inspection = json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
    from scripts.benchmark_owned_cpu_observer import owned_pg_pid

    owned_pg_pid(run,inspection)
    request.getfixturevalue('directory')
    data = populate(10000)
    publication_state.refresh_all()
    child, payload = out/'profile-cold-mix-child.py', out/'profile-cold-mix-payload.json'
    child.write_text(CHILD)
    routes = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
              '/es/listing/'+data['sample_ids'][0]+'/',
              '/en/listing/'+data['sample_ids'][-1]+'/']
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: stamp)
    handler = WSGIHandler()
    signatures = {}
    for route in routes:
        statuses = []
        def begin(status, headers, exc_info=None): statuses.append((status,dict(headers)))
        response = handler(RequestFactory().get(route).environ, begin)
        try:
            body = b''.join(response)
        finally:
            response.close()
        assert statuses[0][0].startswith('200 ') and statuses[0][1]['Cache-Control']=='no-store'
        signatures[route] = hashlib.sha256(body).hexdigest()
    payload.write_text(json.dumps({'routes':routes, 'signatures':signatures, 'stamp':stamp, 'identity':str(out/'profile-child-identity.json'), 'summary':str(out/'profile-cold-mix-child-summary.json'),
        'media_root':str(settings.MEDIA_ROOT)}))
    (out/'profile_runtime_settings.py').write_text(
        'from config.settings import *\nMEDIA_ROOT = '+repr(str(settings.MEDIA_ROOT))+'\n')
    db = connection.settings_dict
    environment = {**os.environ, 'POSTGRES_DB':db['NAME'],
                   'POSTGRES_USER':db['USER'], 'POSTGRES_PASSWORD':db['PASSWORD'],
                   'DB_HOST':db['HOST'], 'DB_PORT':str(db['PORT']),
                   'APP_ENV':'development', 'DJANGO_DEBUG':'0',
                   'DJANGO_SETTINGS_MODULE':'profile_runtime_settings',
                   'PYTHONPATH':str(out.resolve())+os.pathsep+str(Path.cwd()),
                   'REDIS_URL':'memory://'}
    supervisor = out/'profile-supervisor.py'
    supervisor.write_text(SUPERVISOR)
    completed = subprocess.run([sys.executable,str(supervisor),str(child),str(payload),str(out)],
                               env=environment,capture_output=True,text=True,timeout=180)
    (out/'supervisor.stdout.log').write_text(completed.stdout)
    (out/'supervisor.stderr.log').write_text(completed.stderr)
    completed.check_returncode()
    lifecycle = json.loads((out/'profiler-lifecycle.json').read_text())
    assert lifecycle['tool_exit']==0 and lifecycle['pid_absent']
    summary = json.loads((out/'profile-cold-mix-child-summary.json').read_text())
    assert summary['completed']==72 and summary['error_type'] is None
    assert summary['source_sha256']==hashlib.sha256(Path('apps/listings/moderation_views.py').read_bytes()).hexdigest()
    trace = json.loads((out/'cold-mix-speedscope.json').read_text())
    frames = trace['shared']['frames']
    marked = {i for i,x in enumerate(frames) if x['name'] in {'profile_first_request','profile_first_cycle_tail','profile_later_requests'}}
    assert marked
    first = {i for i,x in enumerate(frames) if x['name']=='profile_first_request'}
    first_count = sum(bool(first.intersection(stack)) for profile in trace['profiles'] for stack in profile.get('samples',[]))
    assert first_count>=5, 'At least five GIL samples must cover the very first request'
    count = sum(bool(marked.intersection(stack)) for profile in trace['profiles']
                for stack in profile.get('samples',[]))
    assert count>=25, 'Profile must actually sample the request loop'
    record_property('cold_mix_pyspy',json.dumps({'version':version,'completed':72,'loop_samples':count,'first_samples':first_count,'lifecycle':lifecycle,
                    'tool_sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),
                    'limits':'Current product only, own synthetic10k, six routes, fresh WSGI child. '
                             'Child performs no reference requests or DB reads before first request. Static worker preparation retained. '
                             'sample weights are not exact CPU time and omit GIL-free native/SQL waits. '
                             'No SQL/GC/PG observers or candidate policy. Instrumented times not acceptance.'}))
