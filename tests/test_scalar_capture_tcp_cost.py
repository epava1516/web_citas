"""Owned serial TCP A/B/C of the measured transfer intervention, no load gate."""
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

import pytest
from django.conf import settings
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('SCALAR_TCP_OUTPUT'), reason='Explicit isolated serial TCP comparison only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_scalar_capture_tcp_comparison(request, tmp_path, record_property, variant):
    request.getfixturevalue('directory')
    populate(10000)
    if variant == 'diverse':
        rows = list(Revision.objects.filter(status='approved').order_by('pk'))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += ' ' + suffix
            if row.description_alternative:
                row.description_alternative += ' ' + suffix
            row.telegram = 'bench' + suffix
        Revision.objects.bulk_update(rows, ['description', 'description_alternative', 'telegram'], batch_size=250)
    db = connection.settings_dict
    assert connection.vendor == 'postgresql' and db['NAME'].startswith('test_promotion_gate_')
    assert projection.supported()
    digest = projection.definitions_digest()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    (tmp_path/'scalar_tcp_settings.py').write_text(
        'from config.settings import *\nMEDIA_ROOT = ' + repr(str(settings.MEDIA_ROOT)) +
        '\nCELERY_TASK_ALWAYS_EAGER = True\nCELERY_BEAT_SCHEDULE = {}\n')
    config = tmp_path/'scalar_tcp_gunicorn.py'
    config.write_text('''import os
def post_worker_init(worker):
    from apps.listings import projected_publication as projection
    assert projection.supported()
    get_response = worker.wsgi.get_response
    constructor = projection.ProjectedPublication.__init__
    def selected_response(request):
        mode = request.META.get('HTTP_X_SCALAR_COMPARISON')
        if mode not in {'A', 'B', 'C'}:
            return get_response(request)
        def selected(self, query, **kwargs):
            kwargs['sql_scalar_capture'] = mode != 'A'
            kwargs['sql_text_membership'] = mode == 'C'
            return constructor(self, query, **kwargs)
        projection.ProjectedPublication.__init__ = selected
        try:
            response = get_response(request)
        finally:
            projection.ProjectedPublication.__init__ = constructor
        route = getattr(request, '_publication_route', {})
        stats = route.get('candidate_stats', {})
        response['X-Diagnostic-Route'] = route.get('route', 'missing')
        response['X-Diagnostic-Scalar'] = str(int(bool(stats.get('scalar_capture'))))
        response['X-Diagnostic-Index'] = str(int(bool(stats.get('text_membership'))))
        response['X-Diagnostic-Positive'] = str(stats.get('positive', -1))
        response['X-Diagnostic-Unknown'] = str(stats.get('native_fallback', -1))
        response['X-Diagnostic-Worker'] = str(os.getpid())
        return response
    worker.wsgi.get_response = selected_response
''')
    environment = os.environ.copy()
    environment.update(POSTGRES_DB=db['NAME'], POSTGRES_USER=db['USER'], POSTGRES_PASSWORD=db['PASSWORD'],
        DB_HOST=db['HOST'], DB_PORT=str(db['PORT']), APP_ENV='development', DJANGO_DEBUG='0',
        DJANGO_SETTINGS_MODULE='scalar_tcp_settings', PYTHONPATH=str(tmp_path)+os.pathsep+str(Path.cwd()),
        REDIS_URL='memory://')
    environment.pop('WEB_MODELOS_BENCHMARK_OBSERVER_DIR', None)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    routes = [('listing-es', '/es/'), ('listing-en', '/en/'),
              ('search-es', '/es/?q=photography'), ('search-en', '/en/?q=synthetic')]
    bodies, samples, warmup = {}, [], []
    process = None
    report = {'variant': variant, 'source_fingerprint': digest, 'stage': 'prepared',
              'runtime_configuration_sha256': hashlib.sha256(config.read_bytes()).hexdigest()}
    output = Path(os.environ['SCALAR_TCP_OUTPUT'], variant+'.json')

    def persist():
        output.write_text(json.dumps(report, indent=2)+'\n')

    def fetch(label, path, mode):
        start = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(origin+path,
                headers={'X-Scalar-Comparison': mode}), timeout=65) as response:
            body = response.read()
            status = response.status
            headers = response.headers
        elapsed = time.perf_counter()-start
        assert status == 200 and re.search(rb'<p>10000 (?:results|resultados)</p>', body)
        assert headers['X-Diagnostic-Route'] == 'projection'
        assert headers['X-Diagnostic-Scalar'] == str(int(mode != 'A'))
        assert headers['X-Diagnostic-Index'] == str(int(mode == 'C'))
        assert headers['X-Diagnostic-Positive'] == '10000' and headers['X-Diagnostic-Unknown'] == '0'
        bodies.setdefault(label, body)
        assert body == bodies[label]
        return {'family': label, 'mode': mode, 'seconds': elapsed,
                'worker_pid': int(headers['X-Diagnostic-Worker']), 'status': status,
                'body_sha256': hashlib.sha256(body).hexdigest(), 'route': 'projection',
                'scalar': mode != 'A', 'indexed': mode == 'C', 'positive': 10000, 'unknown': 0}

    try:
        with (tmp_path/'gunicorn-private.log').open('w') as log:
            process = subprocess.Popen([sys.executable, '-m', 'gunicorn', '--config', str(config),
                'config.wsgi:application', '--bind', f'127.0.0.1:{port}', '--workers', '4',
                '--timeout', '65', '--worker-class', 'sync'], env=environment,
                stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic()+45
        while True:
            try:
                with urllib.request.urlopen(origin+'/health/', timeout=2) as response:
                    assert response.status == 200
                break
            except (OSError, urllib.error.URLError):
                assert process.poll() is None and time.monotonic() < deadline
                time.sleep(.1)
        # Warm every observed worker/mode before timing controls. Bound this
        # startup check; missing workers cannot silently become a four-worker run.
        seen = set()
        for index in range(96):
            label, path = routes[index % len(routes)]
            mode = 'ABC'[index % 3]
            sample = fetch(label, path, mode)
            warmup.append(sample)
            seen.add((sample['worker_pid'], mode))
            if len(seen) == 12 and len({p for p, _ in seen}) == 4:
                break
        assert len(seen) == 12
        before = stats_snapshot()
        orders = [('A','B','C'), ('C','B','A'), ('B','C','A'), ('A','C','B'),
                  ('C','A','B'), ('B','A','C'), ('A','B','C'), ('C','B','A')]
        for pair, order in enumerate(orders):
            for label, path in routes:
                for mode in order:
                    sample = fetch(label, path, mode)
                    assert (sample['worker_pid'], mode) in seen, 'Unexpected unprimed/restarted worker'
                    samples.append({'pair': pair, **sample})
            report.update(stage='controls', samples=samples, warmup=warmup)
            persist()
        after = stats_snapshot()
        medians = {f: {m: statistics.median(s['seconds'] for s in samples if s['family']==f and s['mode']==m)
                       for m in 'ABC'} for f, _ in routes}

        def comparison(a, b, minimum, fraction):
            deltas = [statistics.mean(
                next(s['seconds'] for s in samples if s['pair']==pair and s['family']==f and s['mode']==a)
                - next(s['seconds'] for s in samples if s['pair']==pair and s['family']==f and s['mode']==b)
                for f, _ in routes) for pair in range(8)]
            reference = statistics.mean(v[a] for v in medians.values())
            no_regression = all(v[b]-v[a] <= max(.05, .1*v[a]) for v in medians.values())
            return {'paired_mean_family_deltas': deltas,
                    'effect': statistics.median(deltas) >= max(minimum, fraction*reference)
                              and sum(d > 0 for d in deltas) >= 6 and no_regression}

        report.update(stage='complete', medians=medians, samples=samples, warmup=warmup,
            scalar_effect=comparison('A','B',.05,.05), additional_index_effect=comparison('B','C',.05,.05),
            combined_effect=comparison('A','C',.10,.15), statistics_before=before,
            statistics_after=after, statistics_endpoints_equal=before==after,
            scope='Actual serial HTTP over loopback TCP, own fresh Gunicorn4 sync on synthetic PG/media. Same backend, worker pool, schema/indexes/data and eight counterbalanced triplets per ES/EN listing/search. A=typed/full capture,row text proof; B=scalar/full capture,row proof; C=scalar plus partial-index membership. A/B/C vary only constructor arguments in a test-only get_response hook restored after each synchronous request. Diagnostic response headers read actual public route/stats; same hook for all modes, no profiler/SQL/GC observer/timing in server and no extra supported() inside request. All worker/mode combinations warmed before controls, PIDs recorded; at most one HTTP request outstanding. Complete bodies/count/route verified; previous full native population/page equivalences reused on unchanged backend, not new universal equivalence. Timer spans client send through complete response body, no setup/assertions. No request interarrival schedule, uploads, concurrency or capacity. OS/PG caches warm, not reset; all original SLO/load gates unchanged. No worker increase vs contractual4. Header/hook causal overhead not_measured. No application/runtime deployment.',
            not_measured=['per-rule validation/model construction/SQL/render in TCP controls',
                          'SQL rows_returned/affected/scanned', 'causal hook overhead',
                          'PG CPU/RSS/waits/locks/IO', 'current100/1000 matrix', 'capacity', 'uploads'])
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        report.update(own_server_stopped=process is None or process.poll() is not None,
                      server_returncode=process.returncode if process is not None else None)
        persist()
    assert projection.definitions_digest() == digest and projection.supported()
    record_property('scalar_tcp_comparison', report)
