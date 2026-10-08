"""Isolated serial HTTP attribution, never the concurrent/load capacity gate."""
import hashlib
import json
import os
import re
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote

import pytest
from django.conf import settings
from django.core import signing
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha

from apps.listings import projected_publication as projection
from apps.listings.models import Listing, Revision
from scripts.benchmark_gc_observer import GCObserver
from scripts.benchmark_worker_observer import collect_events
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('SERIAL_RUNTIME_OUTPUT'), reason='Explicit isolated diagnostic only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_serial_runtime_and_client_gc(request, tmp_path, record_property, variant):
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
        del rows
    db = connection.settings_dict
    assert connection.vendor == 'postgresql' and db['NAME'].startswith('test_promotion_gate_')
    assert projection.supported()
    digest = projection.definitions_digest()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE '+connection.ops.quote_name(table))
    routes = [('listing-es', '/es/'), ('listing-en', '/en/'),
              ('search-es', '/es/?q=photography'), ('search-en', '/en/?q=synthetic'),
              ('detail-es', '/es/listing/'+dataset['sample_ids'][0]+'/'),
              ('detail-en', '/en/listing/'+dataset['sample_ids'][-1]+'/')]
    bindings = {label: {'listing': str(row.pk), 'revision': str(row.approved_revision_id)}
                for label, path in routes if label.startswith('detail')
                for row in [Listing.objects.get(pk=path.split('/')[-2])]}
    expected_bodies = {}

    def compare(label, body):
        if label.startswith('detail'):
            match = re.search(rb'\?target=([^&"]+)&amp;reference=', body)
            assert match
            assert signing.loads(unquote(match[1].decode()), salt='public-report-target-v1', max_age=65) == bindings[label]
            assert body.count(match[1]) == 1
            body = body.replace(match[1], b'VERIFIED_SIGNED_REPORT_TARGET')
        else:
            assert re.search(rb'<p>10000 (?:results|resultados)</p>', body)
        if label not in expected_bodies:
            expected_bodies[label] = body
        assert expected_bodies[label] == body, label

    client_samples = []
    # No collection/policy changes; fixture heap provenance is not inferred.
    for pair in range(4):
        for mode in (['plain','gc'] if pair%2 == 0 else ['gc','plain']):
            observer = GCObserver() if mode == 'gc' else None
            if observer:
                observer.__enter__()
            start = time.perf_counter()
            try:
                response = client.get('/es/')
                elapsed = time.perf_counter()-start
            finally:
                if observer:
                    observer.__exit__(None,None,None)
            assert response.status_code == 200
            assert response.context['page'].paginator.count == 10000
            assert response.wsgi_request._publication_route['route'] == 'projection'
            client_samples.append({'pair':pair,'mode':mode,'seconds':elapsed,
                'gc':observer.report() if observer else 'not_measured'})
    report = {'variant':variant,'client_samples':client_samples,'stage':'client_controls_complete',
              'source_fingerprint':digest,'count':10000}
    out = Path(os.environ['SERIAL_RUNTIME_OUTPUT'])
    output = out/(variant+'.json')
    def persist():
        output.write_text(json.dumps(report,indent=2)+'\n')
    persist()
    events_dir = tmp_path/'events'
    events_dir.mkdir()
    (tmp_path/'serial_settings.py').write_text('from config.settings import *\nMEDIA_ROOT = '+repr(str(settings.MEDIA_ROOT))+'\nCELERY_TASK_ALWAYS_EAGER = True\nCELERY_BEAT_SCHEDULE = {}\n')
    config = tmp_path/'serial_gunicorn.py'
    config.write_text('''from scripts.benchmark_worker_observer import post_worker_init as setup, worker_exit
from scripts.benchmark_gc_observer import GCObserver
import re

def post_worker_init(worker):
    setup(worker)
    original = worker.wsgi
    def application(environ, start_response):
        identity = environ.get('HTTP_X_BENCHMARK_ID', '')
        if not re.fullmatch(r'd-[0-9]+', identity):
            return original(environ, start_response)
        with GCObserver() as observer:
            response = original(environ, start_response)
        worker._benchmark_observer.write({'id':identity}, 'gc_application_return', gc=observer.report())
        return response
    worker.wsgi = application
''')
    environment = os.environ.copy()
    environment.update(POSTGRES_DB=db['NAME'],POSTGRES_USER=db['USER'],POSTGRES_PASSWORD=db['PASSWORD'],
        DB_HOST=db['HOST'],DB_PORT=str(db['PORT']),APP_ENV='development',DJANGO_DEBUG='0',
        DJANGO_SETTINGS_MODULE='serial_settings',PYTHONPATH=str(tmp_path)+os.pathsep+str(Path.cwd()),
        REDIS_URL='memory://',WEB_MODELOS_BENCHMARK_OBSERVER_DIR=str(events_dir),WEB_MODELOS_BENCHMARK_ROUTE_ONLY='1')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    process = None
    samples = []
    cold = []
    bodies = expected_bodies
    identity = 0

    def fetch(label, path, observed):
        nonlocal identity
        name = f'd-{identity}'
        identity += 1
        headers = {'X-Benchmark-Id':name} if observed else {}
        start = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(origin+path,headers=headers),timeout=65) as response:
            body = response.read()
            status = response.status
        elapsed = time.perf_counter()-start
        assert status == 200
        compare(label,body)
        return {'id':name if observed else None,'route':label,'mode':'observed' if observed else 'plain',
                'seconds':elapsed,'status':status,'body_sha256':hashlib.sha256(bodies[label]).hexdigest()}

    try:
        with (tmp_path/'gunicorn-private.log').open('w') as log:
            process = subprocess.Popen([sys.executable,'-m','gunicorn','--config',str(config),'config.wsgi:application',
                '--bind',f'127.0.0.1:{port}','--workers','4','--timeout','65','--worker-class','sync'],
                env=environment,stdout=log,stderr=subprocess.STDOUT)
        deadline = time.monotonic()+45
        while True:
            try:
                with urllib.request.urlopen(origin+'/health/',timeout=2) as response:
                    assert response.status==200
                break
            except (OSError, urllib.error.URLError):
                assert process.poll() is None and time.monotonic()<deadline, 'Own Gunicorn failed to become ready'
                time.sleep(.1)
        for label,path in routes:
            cold.append(fetch(label,path,True))
        for pair in range(4):
            for label,path in routes:
                for mode in (['plain','observed'] if pair%2==0 else ['observed','plain']):
                    samples.append({'pair':pair,**fetch(label,path,mode=='observed')})
            report.update(stage='runtime_pairs',cold=cold,samples=samples)
            persist()
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        report['own_server_stopped'] = process is None or process.poll() is not None
        report['server_returncode'] = process.returncode if process is not None else None
        logfile = tmp_path/'gunicorn-private.log'
        if logfile.exists():
            text = logfile.read_text()[-4000:].replace(db['PASSWORD'], '[REDACTED]').replace(db['NAME'], '[OWN_DB]')
            report['server_log_tail_redacted'] = re.sub(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', '[UUID]', text)
        events = collect_events(events_dir)
        report.update(worker_events=events,cold=cold,samples=samples)
        persist()
    assert not events['parse_errors']
    indexed = {}
    for event in events['events']:
        indexed.setdefault(event['id'],{})[event['event']] = event
    for sample in cold+samples:
        if sample['id'] is None:
            continue
        records = indexed[sample['id']]
        assert records['wsgi_end']['status']==200
        route = records['publication_route']
        assert route['route'] == ('native' if sample['route'].startswith('detail') else 'projection')
        if route['route']=='projection':
            assert route['candidate_stats']['positive']==10000 and route['candidate_stats']['native_fallback']==0
        gc = records['gc_application_return']['gc']
        assert gc['policy_before']==gc['policy_after'] and not gc['unfinished_events']
    report.update(stage='complete',route_medians={label:{mode:statistics.median(s['seconds'] for s in samples if s['route']==label and s['mode']==mode)
        for mode in ['plain','observed']} for label,_ in routes},
        runtime_configuration_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
        scope='10000 current-code synthetic records, repeated/diverse separately; own PG/media, ANALYZE preparation. DjangoClient four plain/GC callback pairs on listing in fixture process, no forced collections or policy changes. Fresh Gunicorn4 sync processes then six first-hit route probes and four AB/BA plain/observed pairs per ES/EN listing/search/detail. At most one HTTP request outstanding: NO arrival rate, uploads, concurrency or capacity acceptance. Normal stack remains, shared host/PG caches not reset. Plain runtime controls have no request-ID event collection or active GC callback; installed hook dispatch remains, causal overhead not_measured. Observed WSGI/SQL/render/route events use existing route-only hooks, with GC callbacks around application invocation EXCLUDING response iteration/close; no native rule replacements. GC intervals overlap request/SQL/render, never subtracted as predicted saving; heap provenance/causal comparison across DjangoClient and Gunicorn not_measured. Plain route itself not_measured, observed routes directly verified; body/count/status equivalence and existing nonwrapping route checks reused. SQL execute excludes fetch and is not DB CPU. Signed detail token authenticated and current binding checked before replacing it; all other bytes exact. Normalized SQL and separate plans reused from prior same backend, not relabeled as runtime samples.',
        not_measured=['concurrent capacity','app allocation/heap provenance','causal overhead','TCP accept/worker dispatch wait','DB CPU/RSS/waits/locks/IO','SQL rows_returned/affected/scanned','per-rule validation and model counts in this run','current common matrix','uploads'])
    persist()
    record_property('serial_runtime',report)
