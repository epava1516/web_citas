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
from residual_prepared_support import prepared_iter, diagnose_session
from unittest.mock import patch

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.skipif(
    not os.getenv('RESIDUAL_TCP_OUTPUT'), reason='Explicit isolated serial TCP comparison only')]


@pytest.mark.parametrize('variant', ['contractual', 'diverse'])
def test_residual_prepared_tcp_comparison(request, tmp_path, record_property, variant):
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
    from apps.listings import sql_publication as proof
    original_iterator = proof.CapturedSQLRead.__iter__
    # Current baseline plans are reused; this measures actual prepared sessions,
    # custom/generic plans and exact vectors with the corrected explicit policy.
    session_diagnosis = diagnose_session()
    with patch.object(proof.CapturedSQLRead, '__iter__', prepared_iter):
        prepared_digest = projection.definitions_digest()
    # Driver equivalence against the same captured current statements, all IDs
    # and proof booleans. Revocation/expiry changes are committed and recaptured.
    from django.utils import timezone
    from datetime import timedelta
    from apps.listings import discovery
    affected = discovery.candidates({}).last()
    checks = []
    def vector():
        return proof.SQLPublication(discovery.candidates({})).rows
    def compare(label):
        before = vector()
        with patch.object(proof.CapturedSQLRead, '__iter__', prepared_iter):
            after = vector()
        assert before == after
        checks.append({'case': label, 'candidate_count': len(before), 'equal_ordered_full_vector': True})
    compare('all current IDs/order/proofs')
    old_consent = affected.person.consent_revoked_at
    affected.person.consent_revoked_at = timezone.now(); affected.person.save(update_fields=['consent_revoked_at'])
    compare('committed off-page revocation')
    assert not next(row for row in vector() if row['pk'] == str(affected.pk))['_sql_publication_positive']
    affected.person.consent_revoked_at = old_consent; affected.person.save(update_fields=['consent_revoked_at'])
    old_expiry = affected.expires_at
    affected.expires_at = timezone.now() - timedelta(seconds=1);affected.save(update_fields=['expires_at'])
    compare('committed off-page expiry')
    affected.expires_at = old_expiry;affected.save(update_fields=['expires_at'])
    compare('restored authority freshly read')
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute('ANALYZE ' + connection.ops.quote_name(table))
    (tmp_path/'scalar_tcp_settings.py').write_text(
        'from config.settings import *\nMEDIA_ROOT = ' + repr(str(settings.MEDIA_ROOT)) +
        '\nCELERY_TASK_ALWAYS_EAGER = True\nCELERY_BEAT_SCHEDULE = {}\n')
    config = tmp_path/'scalar_tcp_gunicorn.py'
    observer_folder = tmp_path/'wsgi-events'
    observer_folder.mkdir()
    config.write_text("""import os
from scripts.benchmark_resource_observer import post_worker_init as observe, worker_exit
def post_worker_init(worker):
    from django.db import connection
    from apps.listings import projected_publication as projection, sql_publication as proof
    from residual_prepared_support import prepared_iter
    original_iterator = proof.CapturedSQLRead.__iter__
    baseline_digest = projection.EXPECTED_DEFINITIONS
    assert projection.definitions_digest() == baseline_digest
    proof.CapturedSQLRead.__iter__ = prepared_iter
    candidate_digest = projection.definitions_digest()
    proof.CapturedSQLRead.__iter__ = original_iterator
    observe(worker)
    get_response = worker.wsgi.original if hasattr(worker.wsgi, 'original') else None
    # Observe wraps the WSGI app; get_response lives on the original Django app.
""" + "\n")
    # Keep a handle to the Django app before observer wraps it.
    config.write_text(config.read_text().replace('    observe(worker)\n',
        '    django_app = worker.wsgi\n    observe(worker)\n').replace(
        "    get_response = worker.wsgi.original if hasattr(worker.wsgi, 'original') else None\n",
        '    get_response = django_app.get_response\n') + """
    def selected_response(request):
        mode = request.META.get('HTTP_X_SCALAR_COMPARISON')
        if mode not in {'A', 'B'}:
            return get_response(request)
        proof.CapturedSQLRead.__iter__ = original_iterator if mode == 'A' else prepared_iter
        projection.EXPECTED_DEFINITIONS = baseline_digest if mode == 'A' else candidate_digest
        try:
            response = get_response(request)
        finally:
            proof.CapturedSQLRead.__iter__ = original_iterator
            projection.EXPECTED_DEFINITIONS = baseline_digest
        route = getattr(request, '_publication_route', {})
        stats = route.get('candidate_stats', {})
        response['X-Diagnostic-Route'] = route.get('route', 'missing')
        response['X-Diagnostic-Reason'] = route.get('reason', 'missing')
        response['X-Diagnostic-Scalar'] = str(int(bool(stats.get('scalar_capture'))))
        response['X-Diagnostic-Index'] = str(int(bool(stats.get('text_membership'))))
        response['X-Diagnostic-Positive'] = str(stats.get('positive', -1))
        response['X-Diagnostic-Unknown'] = str(stats.get('native_fallback', -1))
        response['X-Diagnostic-Worker'] = str(os.getpid())
        response['X-Diagnostic-Backend'] = str(connection.connection.info.backend_pid)
        response['X-Diagnostic-Prepared-Count'] = str(len(connection.connection._prepared._names))
        return response
    django_app.get_response = selected_response
""")
    environment = os.environ.copy()
    environment.update(POSTGRES_DB=db['NAME'], POSTGRES_USER=db['USER'], POSTGRES_PASSWORD=db['PASSWORD'],
        DB_HOST=db['HOST'], DB_PORT=str(db['PORT']), APP_ENV='development', DJANGO_DEBUG='0',
        DJANGO_SETTINGS_MODULE='scalar_tcp_settings', PYTHONPATH=str(tmp_path)+os.pathsep+str(Path.cwd())+os.pathsep+str(Path.cwd()/'tests'),
        REDIS_URL='memory://')
    environment['WEB_MODELOS_BENCHMARK_OBSERVER_DIR'] = str(observer_folder)
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    routes = [('listing-es', '/es/'), ('listing-en', '/en/'),
              ('search-es', '/es/?q=photography'), ('search-en', '/en/?q=synthetic')]
    bodies, samples, warmup = {}, [], []
    sequence = 0
    process = None
    report = {'variant': variant, 'source_fingerprint': digest, 'stage': 'prepared',
              'session_diagnosis': session_diagnosis, 'driver_equivalence': checks,
              'runtime_configuration_sha256': hashlib.sha256(config.read_bytes()).hexdigest()}
    output = Path(os.environ['RESIDUAL_TCP_OUTPUT'], variant+'.json')

    def persist():
        output.write_text(json.dumps(report, indent=2)+'\n')

    def fetch(label, path, mode):
        nonlocal sequence
        sequence += 1
        identity = 'd-' + str(sequence)
        start = time.perf_counter()
        with urllib.request.urlopen(urllib.request.Request(origin+path,
                headers={'X-Scalar-Comparison': mode, 'X-Benchmark-ID': identity}), timeout=65) as response:
            body = response.read()
            status = response.status
            headers = response.headers
        elapsed = time.perf_counter()-start
        if mode == 'B':
            assert int(headers['X-Diagnostic-Prepared-Count']) > 0
        assert status == 200 and re.search(rb'<p>10000 (?:results|resultados)</p>', body)
        assert headers['X-Diagnostic-Route'] == 'projection'
        assert headers['X-Diagnostic-Scalar'] == '1'
        assert headers['X-Diagnostic-Index'] == '1'
        assert headers['X-Diagnostic-Positive'] == '10000' and headers['X-Diagnostic-Unknown'] == '0'
        bodies.setdefault(label, body)
        assert body == bodies[label]
        return {'id': identity, 'family': label, 'mode': mode, 'seconds': elapsed, 'postgres_pid': int(headers['X-Diagnostic-Backend']), 'prepared_count': int(headers['X-Diagnostic-Prepared-Count']), 'reason': headers['X-Diagnostic-Reason'],
                'worker_pid': int(headers['X-Diagnostic-Worker']), 'status': status,
                'body_sha256': hashlib.sha256(body).hexdigest(), 'route': 'projection',
                'scalar': True, 'indexed': True, 'positive': 10000, 'unknown': 0}

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
            mode = 'AB'[index % 2]
            sample = fetch(label, path, mode)
            warmup.append(sample)
            seen.add((sample['worker_pid'], mode))
            if len(seen) == 8 and len({p for p, _ in seen}) == 4:
                break
        assert len(seen) == 8
        before = stats_snapshot()
        orders = [('A','B'),('B','A')]*4
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
            prepared_effect=comparison('A','B',.05,.08), statistics_before=before,
            statistics_after=after, statistics_endpoints_equal=before==after,
            scope='Serial TCP 4 sync, repeated/diverse10000,8AB/BApairs x listing/search ESEN. Only scalar read Cursor/prepare policy varies, current SQL/parameters refreshed. No profiler/SQL stage timers in controls. Matched minimal WSGI observer, two reviewed test-only iterator fingerprints precomputed outside requests. Exact route/body/count verified; no production digest loosening or backend adoption. Mean WSGI correlated by unique ID, not inferred from HTTP medians. No loads/uploads or capacity inference. Session limits60s unchanged; new backend PIDs are observed rather than concealed.',
            not_measured=['per-rule validation/model construction/SQL/render in TCP controls',
                          'SQL rows_affected/scanned', 'causal hook overhead',
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
        import shutil
        if (tmp_path/'gunicorn-private.log').exists():
            shutil.copy2(tmp_path/'gunicorn-private.log', Path(os.environ['RESIDUAL_TCP_OUTPUT'])/(variant+'-gunicorn.log'))
        persist()
        records = [json.loads(line) for f in observer_folder.glob('*.jsonl') for line in f.read_text().splitlines()]
        ends = {r['id']: r for r in records if r['event'] == 'wsgi_end'}
        assert len(ends) == len(samples) + len(warmup)
        for sample in samples:
            event = ends[sample['id']]
            assert event['pid'] == sample['worker_pid'] and event['status'] == 200 and event['error_type'] is None
            sample['wsgi_seconds'] = event['wall']
        if samples:
            means = {f: {m: statistics.mean(x['wsgi_seconds'] for x in samples if x['family']==f and x['mode']==m) for m in 'AB'} for f, _ in routes}
            deltas = {family: statistics.mean(means[f]['A'] - means[f]['B'] for f, _ in routes if f.startswith(family)) for family in ['listing','search']}
            report.update(wsgi_means_by_route=means, wsgi_mean_deltas_by_family=deltas,
                delta_D_observed_affected_routes=(deltas['listing']+deltas['search'])/3,
                delta_W20_observed_affected_routes=20*(deltas['listing']+deltas['search'])/3,
                other_family_delta='not_measured; detail unaffected by scalar population read, no extrapolation',
                WSGI_scope='WorkerObserver entry to iterable close, includes matched event overhead; no profiler. 16 complete requests/mode/family (8 ES+8 EN),32/mode across affected families. Serial population distinct from saturated checkpoint.',
                observer_records=records)
            persist()
    assert projection.definitions_digest() == digest and projection.supported()
    record_property('scalar_tcp_comparison', report)
