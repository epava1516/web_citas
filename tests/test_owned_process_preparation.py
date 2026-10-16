"""Isolated-process preparation diagnostic; never contractual HTTP acceptance."""
import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

CHILD = r'''
import time
started, initial_cpu = time.perf_counter(), time.process_time()
import gc, hashlib, json, os, re, sys
from urllib.parse import parse_qs, quote, urlsplit
from html import unescape
payload = json.load(sys.stdin)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.core import signing
from django.test import RequestFactory
from config.worker_startup import prepare_static_structures
assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
assert connection.connection is None
prepare_static_structures()
assert connection.connection is None
handler, factory = WSGIHandler(), RequestFactory()
static_seconds = time.perf_counter() - started
flags = gc.isenabled(), gc.get_debug(), gc.get_threshold()
assert flags[0] and flags[1] == 0
sql_count = [0]
captured = set()
def read_only(execute, sql, params, many, context):
    first = str(sql).lstrip().split(None, 1)[0].upper()
    assert first in {'SELECT','SHOW','SET','BEGIN','COMMIT','ROLLBACK','SAVEPOINT','RELEASE'}, first
    sql_count[0] += 1
    return execute(sql, params, many, context)
def call(route):
    status=[]
    def begin(value, headers, exc_info=None):
        status.append((value, dict(headers)))
    sql_before = sql_count[0]
    wall, cpu = time.perf_counter(), time.thread_time()
    response = handler(factory.get(route).environ, begin)
    try:
        body = b''.join(response)
    finally:
        response.close()
    elapsed, used_cpu = time.perf_counter()-wall, time.thread_time()-cpu
    assert status[0][0].startswith('200 ')
    assert status[0][1]['Cache-Control'] == 'no-store'
    raw_hash = hashlib.sha256(body).hexdigest()
    if route not in captured:
        Path = __import__('pathlib').Path
        (Path(payload['capture_dir']) / (str(payload['routes'].index(route))+'.html')).write_bytes(body)
        captured.add(route)
    report_payload = None
    if '/listing/' in route:
        links = [unescape(link) for link in re.findall(r'href="([^"]+)"', body.decode())]
        tokens = [parse_qs(urlsplit(link).query)['target'][0] for link in links
                  if 'target' in parse_qs(urlsplit(link).query)]
        assert len(tokens) == 1
        report_payload = signing.loads(tokens[0], salt='public-report-target-v1', max_age=7200)
        assert report_payload == payload['expected_report_payloads'][route]
        encoded = quote(tokens[0], safe='/').encode()
        assert body.count(encoded) == 1
        body = body.replace(encoded, b'VERIFIED_REPORT_TARGET')
    return dict(route=route, wall=elapsed, cpu=used_cpu,
                sql=sql_count[0]-sql_before, comparable_body_sha256=hashlib.sha256(body).hexdigest(),
                raw_body_sha256=raw_hash, verified_report_payload=report_payload,
                backend_pid=connection.connection.info.backend_pid)
warm=[]
with connection.execute_wrapper(read_only):
    if payload['arm']=='C':
        warm=[call(route) for route in payload['routes']]
    ready_seconds = time.perf_counter()-started
    samples=[call(route) for route in payload['routes']*2]
assert flags == (gc.isenabled(), gc.get_debug(), gc.get_threshold())
assert len({s['backend_pid'] for s in warm+samples}) == 1
connection.close()
print(json.dumps(dict(pid=os.getpid(), arm=payload['arm'], static_seconds=static_seconds,
                      ready_seconds=ready_seconds, warm=warm, samples=samples,
                      lifecycle_seconds=time.perf_counter()-started,
                      lifecycle_cpu_seconds=time.process_time()-initial_cpu,
                      write_commands=0)))
'''


def test_owned_process_preparation(request, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_process_preparation.py'
               for x in request.config.args):
        pytest.skip('Explicit owned process-lifecycle diagnostic only')
    request.getfixturevalue('directory')
    data = populate(10000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    routes = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
              '/es/listing/' + data['sample_ids'][0] + '/',
              '/en/listing/' + data['sample_ids'][-1] + '/']
    environment = {**os.environ, 'POSTGRES_DB': connection.settings_dict['NAME']}
    expected_report_payloads={route:dict(listing=route.split('/')[3], revision=str(
        Listing.objects.get(pk=route.split('/')[3]).approved_revision_id))
        for route in routes if '/listing/' in route}
    out=Path(request.config.getoption('--gate-timings-output')).parent
    samples=[]
    for block, order in enumerate(['ABC', 'BCA', 'CAB']):
        for arm in order:
            capture=out/f'process-preparation-{block}-{arm}'
            capture.mkdir()
            result = subprocess.run([sys.executable, '-c', CHILD],
                                    input=json.dumps(dict(arm=arm, routes=routes, capture_dir=str(capture),
                                                          expected_report_payloads=expected_report_payloads)),
                                    capture_output=True, text=True, env=environment,
                                    timeout=90, check=False)
            (capture/'stdout.json').write_text(result.stdout)
            (capture/'stderr.log').write_text(result.stderr)
            result.check_returncode()
            value=json.loads(result.stdout)
            value['block']=block
            samples.append(value)
    assert len({r['pid'] for r in samples}) == 9
    signatures={}
    for run in samples:
        for item in run['warm'] + run['samples']:
            signatures.setdefault(item['route'], item['comparable_body_sha256'])
            assert item['comparable_body_sha256'] == signatures[item['route']]
    assert not PublicationDirty.objects.exists()
    comparisons=[]
    for metric in ['wall', 'cpu']:
        means={arm:statistics.mean(item[metric] for run in samples if run['arm']==arm
                                   for item in run['samples'][:6]) for arm in 'ABC'}
        reference=statistics.mean([means['A'],means['B']])
        comparisons.append(dict(metric=metric, first_six_means=means,
                                aa_relative_difference=abs(means['A']-means['B'])/reference,
                                candidate_relative=means['C']/reference))
    diagnostic=dict(runs=samples, comparisons=comparisons,
                    limits='Nine fresh Python/Django processes, one physical DB connection each, '
                           'A/B static only; C six real native WSGI reads before readiness. '
                           'Shared PG buffers not reset. No forked Gunicorn/TCP/concurrency/upload/Beat. '
                           'Startup cost included explicitly, no cached results or forced GC. '
                           'SQL command allowlist in every arm; not DB-server write auditing. '
                           'PASS means parity/completion, not ROI, p95 or production adoption.')
    (out/'process-preparation.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
    record_property('process_preparation', json.dumps(comparisons))
