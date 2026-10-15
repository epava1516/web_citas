"""Explicit fresh-process GC diagnosis; sequential WSGI client, never capacity proof."""

import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

CHILD = r'''
import gc, hashlib, json, os, time
initial_freeze_count=gc.get_freeze_count()
from django.core.wsgi import get_wsgi_application
from django.test import Client
started=time.perf_counter()
application=get_wsgi_application()
initialization=time.perf_counter()-started
policy=(gc.isenabled(),gc.get_threshold())
assert policy[0] and gc.get_freeze_count()==initial_freeze_count
startup=None
if os.environ['GC_ARM']=='collect':
    wall,cpu=time.perf_counter(),time.thread_time()
    count=gc.collect(2)
    startup={'wall':time.perf_counter()-wall,'cpu':time.thread_time()-cpu,'collected':count}
events=[]; pending={}
def observe(phase, info):
    if phase=='start':pending[info['generation']]=(time.perf_counter(),time.thread_time())
    else:
        wall,cpu=pending.pop(info['generation'])
        events.append({'generation':info['generation'],'wall':time.perf_counter()-wall,
                       'cpu':time.thread_time()-cpu,'collected':info['collected']})
gc.callbacks.append(observe)
client=Client(); listing=os.environ['GC_LISTING']
routes=['/es/','/en/','/es/?q=photography','/en/?q=synthetic',
        '/es/listing/'+listing+'/', '/en/listing/'+listing+'/']
rows=[]
try:
    for i in range(30):
        before=len(events);wall,cpu=time.perf_counter(),time.thread_time()
        response=client.get(routes[i%6])
        elapsed,used=time.perf_counter()-wall,time.thread_time()-cpu
        assert response.status_code==200 and response['Cache-Control']=='no-store'
        if i%6<4:
            assert response.wsgi_request._publication_route['population']=='projection'
            digest=hashlib.sha256(response.content).hexdigest()
        else: digest=None # Signed report token varies; no universal body equality claim.
        rows.append({'index':i,'case':i%6,'wall':elapsed,'cpu':used,
                     'body_sha256':digest,'gc_events':events[before:]})
finally:gc.callbacks.remove(observe)
assert not pending and policy==(gc.isenabled(),gc.get_threshold()) and gc.get_freeze_count()==initial_freeze_count
from django.db import connections
connections.close_all()
print(json.dumps({'initialization_wall':initialization,'startup_collect':startup,
                  'rows':rows,'gc_events':events,'policy_unchanged':True,
                  'initial_freeze_count':initial_freeze_count}))
'''


def test_owned_startup_gc(request, record_property, tmp_path):
    if not any(str(x).split('::')[0] == 'tests/test_owned_startup_gc.py'
               for x in request.config.args):
        pytest.skip('Explicit fresh-process diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    request.getfixturevalue('directory')
    data = populate(10000)
    call_command('refresh_publication_state', stdout=io.StringIO())
    db = connection.settings_dict
    assert db['NAME'].startswith('test_promotion_gate_')
    (tmp_path / 'startup_gc_settings.py').write_text(
        'from config.settings import *\nMEDIA_ROOT = ' + repr(str(settings.MEDIA_ROOT)) + '\n')
    environment = dict(os.environ, POSTGRES_DB=db['NAME'], POSTGRES_USER=db['USER'],
                       POSTGRES_PASSWORD=db['PASSWORD'], DB_HOST=db['HOST'], DB_PORT=str(db['PORT']),
                       APP_ENV='development', DJANGO_DEBUG='0', REDIS_URL='memory://',
                       PYTHONPATH=str(tmp_path) + os.pathsep + str(Path.cwd()),
                       GC_LISTING=str(data['sample_ids'][0]),
                       DJANGO_SETTINGS_MODULE='startup_gc_settings')
    launcher = ('import json, traceback\ntry:\n exec(' + repr(CHILD)
                + ')\nexcept Exception as exc:\n'
                + ' print(json.dumps({"error_type":type(exc).__name__,"frames":'
                + '[(f.filename,f.lineno,f.name) for f in traceback.extract_tb(exc.__traceback__)]}))\n'
                + ' raise SystemExit(1)\n')
    results = []
    baseline = {}
    evidence = out / 'startup-gc.json'
    try:
        for block in range(3):
            arms = ('current', 'collect') if block % 2 == 0 else ('collect', 'current')
            for arm in arms:
                child = subprocess.run([sys.executable, '-c', launcher],
                                       env=dict(environment, GC_ARM=arm),
                                       capture_output=True, text=True, timeout=90, check=False)
                result = json.loads(child.stdout)
                result.update(block=block, arm=arm)
                results.append(result)
                assert child.returncode == 0, result
                for row in result['rows']:
                    if row['body_sha256'] is not None:
                        expected = baseline.setdefault(row['case'], row['body_sha256'])
                        assert expected == row['body_sha256']
    finally:
        evidence.write_text(json.dumps({'results': results,
                                       'scope': '180 sequential actual Django WSGI test-client requests; '
                                       'six fresh Python processes, three alternating blocks. '
                                       'No concurrent admission, HTTP socket or capacity proof. '
                                       'All first requests included; only startup collect differs. '
                                       'Callbacks add unmeasured overhead. Freeze count unchanged; no policy change. '
                                       'Child exceptions retain only type/frames, never SQL/credentials. '
                                       'Initialization timer covers get_wsgi_application, not full Python boot. '
                                       'Django Client uses its own handler; this is not a real Gunicorn worker.'}, indent=2))
    assert len(results) == 6
    record_property('startup_gc_artifact', str(evidence))
