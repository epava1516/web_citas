"""Owned external GIL sampling with matched unprofiled TCP controls; no load gate."""
import hashlib
import json
import os
import re
import signal
import socket
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
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
    not os.getenv('READING_SAMPLING_OUTPUT'), reason='Explicit isolated serial TCP comparison only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_reading_sampling_tcp(request, tmp_path, monkeypatch, record_property, variant):
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
    (tmp_path/'sampling_tcp_settings.py').write_text(
        'from config.settings import *\nMEDIA_ROOT = ' + repr(str(settings.MEDIA_ROOT)) +
        '\nCELERY_TASK_ALWAYS_EAGER = True\nCELERY_BEAT_SCHEDULE = {}\n')
    config = tmp_path/'sampling_tcp_gunicorn.py'
    config.write_text('''import os, time
def post_worker_init(worker):
    from apps.listings import projected_publication as projection
    assert projection.supported()
    get_response = worker.wsgi.get_response
    def selected_response(request):
        start = time.thread_time()
        response = get_response(request)
        elapsed = time.thread_time() - start
        route = getattr(request, '_publication_route', {})
        stats = route.get('candidate_stats', {})
        presentation = getattr(request, '_presentation_reads', {})
        response['X-Diagnostic-Route'] = route.get('route', 'missing')
        response['X-Diagnostic-Scalar'] = str(int(bool(stats.get('scalar_capture'))))
        response['X-Diagnostic-Index'] = str(int(bool(stats.get('text_membership'))))
        response['X-Diagnostic-Positive'] = str(stats.get('positive', -1))
        response['X-Diagnostic-Unknown'] = str(stats.get('native_fallback', -1))
        response['X-Diagnostic-Grouped'] = str(int(bool(presentation.get('grouped'))))
        response['X-Diagnostic-Photo-Native'] = str(presentation.get('photo_native', -1))
        response['X-Diagnostic-Check-Native'] = str(presentation.get('check_native', -1))
        response['X-Diagnostic-Worker'] = str(os.getpid())
        response['X-Diagnostic-Thread-CPU'] = str(elapsed)
        return response
    worker.wsgi.get_response = selected_response
''')
    environment = os.environ.copy()
    environment.update(POSTGRES_DB=db['NAME'], POSTGRES_USER=db['USER'], POSTGRES_PASSWORD=db['PASSWORD'],
        DB_HOST=db['HOST'], DB_PORT=str(db['PORT']), APP_ENV='development', DJANGO_DEBUG='0',
        DJANGO_SETTINGS_MODULE='sampling_tcp_settings', PYTHONPATH=str(tmp_path)+os.pathsep+str(Path.cwd()),
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
              'runtime_configuration_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
              'pyspy_binary_sha256': hashlib.sha256(Path(os.environ['READING_PYSPY_BIN']).read_bytes()).hexdigest()}
    output = Path(os.environ['READING_SAMPLING_OUTPUT'], variant+'.json')

    def persist():
        output.write_text(json.dumps(report, indent=2)+'\n')

    def fetch(label, path, mode):
        start = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(origin+path,
                headers={'X-Presentation-Comparison': mode}), timeout=65) as response:
            body = response.read()
            status = response.status
            headers = response.headers
        elapsed = time.perf_counter()-start
        assert status == 200 and re.search(rb'<p>10000 (?:results|resultados)</p>', body)
        assert headers['X-Diagnostic-Route'] == 'projection'
        assert headers['X-Diagnostic-Scalar'] == '1'
        assert headers['X-Diagnostic-Index'] == '1'
        assert headers['X-Diagnostic-Positive'] == '10000' and headers['X-Diagnostic-Unknown'] == '0'
        assert headers['X-Diagnostic-Grouped'] == '1'
        assert headers['X-Diagnostic-Photo-Native'] == '0'
        assert headers['X-Diagnostic-Check-Native'] == '0'
        bodies.setdefault(label, body)
        assert body == bodies[label]
        return {'family': label, 'mode': mode, 'seconds': elapsed,
                'worker_pid': int(headers['X-Diagnostic-Worker']), 'status': status,
                'body_sha256': hashlib.sha256(body).hexdigest(), 'route': 'projection',
                'scalar': True, 'indexed': True, 'grouped': True, 'wsgi_thread_cpu_seconds': float(headers['X-Diagnostic-Thread-CPU']), 'positive': 10000, 'unknown': 0}

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
            mode = 'AB'[(index // len(routes)) % 2]
            sample = fetch(label, path, mode)
            warmup.append(sample)
            seen.add((sample['worker_pid'], mode))
            if len(seen) == 8 and len({p for p, _ in seen}) == 4:
                break
        assert len(seen) == 8
        before = stats_snapshot()
        collector_runs = []
        orders = [('A', 'B'), ('B', 'A')]*6
        for pair, order in enumerate(orders):
            for mode in order:
                collector = None
                profile_path = Path(os.environ['READING_SAMPLING_OUTPUT'], f'{variant}-sample-{pair}.json')
                log_path = Path(os.environ['READING_SAMPLING_OUTPUT'], f'{variant}-sampler-{pair}.log')
                try:
                    if mode == 'B':
                        with log_path.open('w') as collector_log:
                            collector = subprocess.Popen([os.environ['READING_PYSPY_BIN'], 'record',
                                '--pid', str(process.pid), '--subprocesses', '--gil', '--rate', '100',
                                '--format', 'speedscope', '--duration', '30', '--output', str(profile_path)],
                                stdout=collector_log, stderr=subprocess.STDOUT)
                        deadline = time.monotonic()+10
                        while 'Sampling process' not in log_path.read_text():
                            assert collector.poll() is None, log_path.read_text()
                            assert time.monotonic() < deadline, 'Sampler did not become ready'
                            time.sleep(.05)
                    for label, path in routes:
                        sample = fetch(label, path, mode)
                        assert (sample['worker_pid'], mode) in seen, 'Unexpected unprimed/restarted worker'
                        samples.append({'pair': pair, **sample})
                    if collector is not None:
                        assert collector.poll() is None, 'Sampler ended before observed block'
                finally:
                    if collector is not None:
                        if collector.poll() is None:
                            collector.send_signal(signal.SIGINT)
                        try:
                            collector.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            collector.kill()
                            collector.wait(timeout=5)
                        collector_runs.append({'pair': pair, 'returncode': collector.returncode,
                            'output': profile_path.name, 'log': log_path.name})
                        assert collector.returncode == 0 and profile_path.is_file(), log_path.read_text()
            report.update(stage='controls', samples=samples, warmup=warmup, collector_runs=collector_runs)
            persist()
        after = stats_snapshot()
        medians = {f: {m: statistics.median(s['seconds'] for s in samples if s['family']==f and s['mode']==m)
                       for m in 'AB'} for f, _ in routes}

        deltas = [statistics.mean(
            next(x['seconds'] for x in samples if x['pair']==pair and x['family']==family and x['mode']=='B')
            - next(x['seconds'] for x in samples if x['pair']==pair and x['family']==family and x['mode']=='A')
            for family, _ in routes) for pair in range(12)]
        reference = statistics.mean(v['A'] for v in medians.values())
        compatible = abs(statistics.median(deltas)) <= max(.025, .05*reference) and all(
            abs(v['B']-v['A']) <= max(.040, .10*v['A']) for v in medians.values())
        inclusive, exclusive, totals = Counter(), Counter(), Counter()
        for run in collector_runs:
            raw = json.loads(Path(os.environ['READING_SAMPLING_OUTPUT'], run['output']).read_text())
            frames = raw['shared']['frames']
            for prof in raw['profiles']:
                assert prof['type'] == 'sampled'
                for stack in prof['samples']:
                    callstack = [frames[index] for index in stack]
                    totals['all_recorded_stacks'] += 1
                    if not any(f.get('name') == 'selected_response' and 'sampling_tcp_gunicorn.py' in f.get('file','') for f in callstack):
                        continue
                    totals['request_stacks'] += 1
                    labels = []
                    for frame in callstack:
                        file = frame.get('file', '')
                        if not file:
                            continue
                        root = str(Path.cwd())+'/'
                        if file.startswith(root):
                            file = file[len(root):]
                        labels.append(file+':'+str(frame.get('line','?'))+':'+frame['name'])
                    assert labels
                    inclusive.update(set(labels))
                    exclusive[labels[-1]] += 1
        assert totals['request_stacks'] >= 300, 'Too few request stacks for this diagnostic'
        def table(counter):
            return [{'location': name, 'samples': count,
                'share_of_request_stacks': count/totals['request_stacks']} for name,count in counter.most_common(100)]
        report.update(stage='complete', medians=medians, samples=samples, warmup=warmup,
            paired_observed_minus_plain_mean_family_deltas=deltas, numerical_compatibility=compatible,
            statistics_before=before, statistics_after=after, statistics_endpoints_equal=before==after,
            collector_runs=collector_runs, sampled_stacks=dict(totals),
            inclusive_stack_locations=table(inclusive), exclusive_leaf_locations=table(exclusive),
            pyspy_version=subprocess.check_output([os.environ['READING_PYSPY_BIN'],'--version'],text=True).strip(),
            scope='Actual serial TCP ownGunicorn4sync, max1outstanding, 10000original/diverse. Twelve AB/BA blocks each4ESENlist/search. A withoutsampler, B externalpy-spy100Hz GIL-only Python stacks on ownmaster/children; no call hooks/localvalues/native-rules replacements. Same WSGI boundary threadCPU+routeheaders bothmodes. Warm allworkers/modes, body/count/route exact. Sampler startup/stop outside requesttimers, logs+rawspeedscopehashed. Inclusive samplecounts count each location once perstack; exclusive is leaflocation, not exact rulecalls/time. No conversion samplecount/rate to CPU/request or walltime; GIL/native/idle filtering and stopped-process sampling bias documented. WSGIthreadCPU clock directly measured handlerboundary, not serverCPU/SQL or fullTCPtime. Existing matrix/rule/SQLplans reused, backend unchanged. Compatibility margin fixed before run; not causaloverhead, negative delta notnegativeoverhead. No load/capacity/optimization acceptance.',
            not_measured=['per-rule exactcalls/inclusive/exclusivetime in samplingrun (reuse matrix with source)',
                'SQL metrics in this run (reuse samebackend matrix/plans)', 'rows_returned/affected/scanned',
                'CPU PostgreSQL/waits/locks/IO/RSS', 'causal profiler overhead', 'CPU withoutGIL/nativeextensions',
                'capacity','new backend effect'])
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
    assert hashlib.sha256(Path(os.environ['READING_PYSPY_BIN']).read_bytes()).hexdigest() == report['pyspy_binary_sha256']
    record_property('reading_sampling_tcp', json.dumps(report))
