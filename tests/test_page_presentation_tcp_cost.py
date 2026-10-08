"""Owned serial TCP A/B of fresh grouped presentation, no load gate."""
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
from unittest.mock import patch

import pytest
from django.conf import settings
from django.db import connection, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot
from test_sql_publication_bulk_cost import redact_plan

from apps.listings import discovery
from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from apps.listings.presentation_reads import PagePresentation
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('PRESENTATION_TCP_OUTPUT'), reason='Explicit isolated serial TCP comparison only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_grouped_presentation_tcp_comparison(request, tmp_path, monkeypatch, record_property, variant):
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
    (tmp_path/'presentation_tcp_settings.py').write_text(
        'from config.settings import *\nMEDIA_ROOT = ' + repr(str(settings.MEDIA_ROOT)) +
        '\nCELERY_TASK_ALWAYS_EAGER = True\nCELERY_BEAT_SCHEDULE = {}\n')
    config = tmp_path/'presentation_tcp_gunicorn.py'
    config.write_text('''import os
def post_worker_init(worker):
    from apps.listings import discovery, projected_publication as projection
    from apps.listings.presentation_reads import PagePresentation
    assert projection.supported()
    get_response = worker.wsgi.get_response
    def selected_response(request):
        mode = request.META.get('HTTP_X_PRESENTATION_COMPARISON')
        if mode not in {'A', 'B'}:
            return get_response(request)
        original = discovery.PagePresentation
        discovery.PagePresentation = lambda rows: PagePresentation(rows, grouped=mode == 'B')
        try:
            response = get_response(request)
        finally:
            discovery.PagePresentation = original
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
        return response
    worker.wsgi.get_response = selected_response
''')
    environment = os.environ.copy()
    environment.update(POSTGRES_DB=db['NAME'], POSTGRES_USER=db['USER'], POSTGRES_PASSWORD=db['PASSWORD'],
        DB_HOST=db['HOST'], DB_PORT=str(db['PORT']), APP_ENV='development', DJANGO_DEBUG='0',
        DJANGO_SETTINGS_MODULE='presentation_tcp_settings', PYTHONPATH=str(tmp_path)+os.pathsep+str(Path.cwd()),
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
    output = Path(os.environ['PRESENTATION_TCP_OUTPUT'], variant+'.json')

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
        assert headers['X-Diagnostic-Grouped'] == str(int(mode == 'B'))
        assert headers['X-Diagnostic-Photo-Native'] == str(24 if mode == 'A' else 0)
        assert headers['X-Diagnostic-Check-Native'] == str(24 if mode == 'A' else 0)
        bodies.setdefault(label, body)
        assert body == bodies[label]
        return {'family': label, 'mode': mode, 'seconds': elapsed,
                'worker_pid': int(headers['X-Diagnostic-Worker']), 'status': status,
                'body_sha256': hashlib.sha256(body).hexdigest(), 'route': 'projection',
                'scalar': True, 'indexed': True, 'grouped': mode == 'B', 'positive': 10000, 'unknown': 0}

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
        orders = [('A','B'), ('B','A')]*4
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
                       for m in 'AB'} for f, _ in routes}

        def comparison(a, b, minimum, fraction):
            deltas = [statistics.mean(
                next(s['seconds'] for s in samples if s['pair']==pair and s['family']==f and s['mode']==a)
                - next(s['seconds'] for s in samples if s['pair']==pair and s['family']==f and s['mode']==b)
                for f, _ in routes) for pair in range(8)]
            reference = statistics.mean(v[a] for v in medians.values())
            no_regression = all(v[b]-v[a] <= max(.025, .05*v[a]) for v in medians.values())
            return {'paired_mean_family_deltas': deltas,
                    'effect': statistics.median(deltas) >= max(minimum, fraction*reference)
                              and sum(d > 0 for d in deltas) >= 6 and no_regression}

        report.update(stage='complete', medians=medians, samples=samples, warmup=warmup,
            material_effect=comparison('A','B',.05,.08), statistics_before=before,
            statistics_after=after, statistics_endpoints_equal=before==after,
            scope='Actual serial loopback TCP, own Gunicorn4sync, same scalar/index backend/schema/data. Eight counterbalanced AB/BA pairs each ES/EN listing/search, at most1outstanding. A uses ordinary per-card reads through the same accessor; B uses fresh grouped reads after guard, tie/absence fallback preserved. Test-only selector/actual-route headers same instrumentation both, no server profiler/SQL/GC observers or extra fingerprint. Warm allworkers/modes; timer spans send through full response body. Bodies/count/routing exact, unchanged proof/ordering/publication logic. No interarrival schedule/uploads/capacity. Native/scalar full-population equivalences reused; focal presentation selection and concurrent commits checked separately. Causal hook overhead not_measured; no normal runtime change or new resources.',
            not_measured=['per-rule validation/render events in TCP controls','SQL rows_affected/scanned',
                          'causal hook overhead','PG CPU/RSS/waits/locks/IO','currentcommonmatrix/N2','capacity','uploads'])
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
    # Separate mechanism observation after all TCP controls and server shutdown.
    # No claim that these DjangoClient timers describe the TCP worker samples.
    client = request.getfixturevalue('directory')
    observations = []
    reads = {}
    observed_body = None
    for mode in ['A','B']:
        patterns = {}
        def sql_timer(execute, sql, params, many, context):
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                elapsed = time.perf_counter()-start
                pattern = query_pattern(sql)
                bucket = patterns.setdefault(pattern, {'calls':0,'total_time':0.})
                bucket['calls'] += 1
                bucket['total_time'] += elapsed
                if '_presentation_rank' in sql:
                    reads.setdefault(pattern,(sql,params))
        with patch.object(discovery,'PagePresentation',lambda rows:PagePresentation(rows,grouped=mode=='B')):
            with connection.execute_wrapper(sql_timer):
                measured = client.get('/es/')
        assert measured.status_code == 200
        if observed_body is None:
            observed_body = measured.content
        assert measured.content == observed_body
        assert measured.wsgi_request._publication_route['route'] == 'projection'
        observations.append({'mode':mode,'queries':sum(v['calls'] for v in patterns.values()),
            'sql_execute_seconds':sum(v['total_time'] for v in patterns.values()),
            'presentation':measured.wsgi_request._presentation_reads,
            'dominant_sql':[{'query_pattern':p,**v,'mean_time':v['total_time']/v['calls']}
                for p,v in sorted(patterns.items(),key=lambda item:item[1]['total_time'],reverse=True)]})
    assert observations[0]['queries']-observations[1]['queries'] == 46
    plans=[]
    assert len(reads)==2
    for pattern,(sql,params) in reads.items():
        with transaction.atomic(),connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION READ ONLY')
            cursor.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+sql,params)
            plans.append({'query_pattern':pattern,'plan':redact_plan(cursor.fetchone()[0])})
    report.update(separate_mechanism_observations=observations,separate_new_read_plans=plans,
        mechanism_scope='DjangoClient SQL events after timed TCP controls/server shutdown. Same fixture/source; SQL execute includes driver/DB/waits/buffering, not PG CPU. Two new grouped read plans only, existing main/top read plans reused. No row counts inferred from ORM; no validation from total-minus-SQL. Read node rows/loops/times overlap and are not global scanned rows.')
    persist()
    record_property('presentation_tcp_comparison', report)
