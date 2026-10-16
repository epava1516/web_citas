"""Explicit py-spy diagnosis of current detail; never accepted request timing."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

CHILD = r'''
import gc, hashlib, json, os, platform, sys, time
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
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
stamp = signing.TimestampSigner().timestamp()
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
def profile_detail_requests():
    for _ in range(120):
        for route in payload['routes']:
            assert read(route)==signatures[route]
            result['completed']+=1
try:
    signatures={route:read(route) for route in payload['routes']}
    started=time.monotonic()
    profile_detail_requests()
    result['profile_loop_monotonic']=[started,time.monotonic()]
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
'''


def test_owned_detail_pyspy(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_detail_pyspy.py'
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
    child, payload = out/'profile-detail-child.py', out/'profile-detail-payload.json'
    child.write_text(CHILD)
    payload.write_text(json.dumps({'routes':[
        '/es/listing/'+data['sample_ids'][0]+'/',
        '/en/listing/'+data['sample_ids'][-1]+'/',
    ], 'summary':str(out/'profile-detail-child-summary.json'),
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
    command = [str(tool),'record','--rate','100','--gil','--full-filenames',
               '--format','speedscope','--output',str(out/'detail-speedscope.json'),
               '--',sys.executable,str(child),str(payload)]
    completed = subprocess.run(command,env=environment,capture_output=True,text=True,timeout=180)
    (out/'pyspy.stdout.log').write_text(completed.stdout)
    (out/'pyspy.stderr.log').write_text(completed.stderr)
    completed.check_returncode()
    summary = json.loads((out/'profile-detail-child-summary.json').read_text())
    assert summary['completed']==240 and summary['error_type'] is None
    assert summary['source_sha256']==hashlib.sha256(Path('apps/listings/moderation_views.py').read_bytes()).hexdigest()
    trace = json.loads((out/'detail-speedscope.json').read_text())
    frames = trace['shared']['frames']
    marked = {i for i,x in enumerate(frames) if x['name']=='profile_detail_requests'}
    assert marked
    count = sum(bool(marked.intersection(stack)) for profile in trace['profiles']
                for stack in profile.get('samples',[]))
    assert count>=25, 'Profile must actually sample the request loop'
    record_property('detail_pyspy',json.dumps({'version':version,'completed':240,'loop_samples':count,
                    'tool_sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),
                    'limits':'Current product only, own synthetic10k, two agency routes, actual WSGI child. '
                             'Python already initialized/shared PG buffers warm. GIL-holding traces only; '
                             'sample weights are not exact CPU time and omit GIL-free native/SQL waits. '
                             'No SQL/GC/PG observers or candidate policy. Instrumented times not acceptance.'}))
