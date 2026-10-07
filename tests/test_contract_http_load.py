"""Contractual arrival-rate HTTP load on isolated local Gunicorn/PostgreSQL."""

import concurrent.futures
import http.cookies
import json
import math
import os
import platform
import queue
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.db import connection
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def percentile(values, ratio):
    return sorted(values)[max(0, math.ceil(len(values) * ratio) - 1)] if values else None


@pytest.mark.parametrize('large', [False, True], ids=['functional', 'measured'])
def test_contract_arrival_rate_http_with_limited_uploads(request, tmp_path, record_property, large):
    request.getfixturevalue("directory")
    assert connection.vendor == 'postgresql'
    dataset = populate(10000 if large else 10)
    db = connection.settings_dict
    assert db['NAME'].startswith('test_promotion_gate_')
    environment = os.environ.copy()
    environment.update(POSTGRES_DB=db['NAME'], POSTGRES_USER=db['USER'], POSTGRES_PASSWORD=db['PASSWORD'],
                       DB_HOST=db['HOST'], DB_PORT=str(db['PORT']), APP_ENV='development',
                       DJANGO_DEBUG='0', DJANGO_SETTINGS_MODULE='load_runtime_settings',
                       PYTHONPATH=str(tmp_path)+os.pathsep+str(Path.cwd()), REDIS_URL='memory://',
                       TASK_QUEUE_GENERATION='l'+uuid4().hex[:31])
    (tmp_path / 'load_runtime_settings.py').write_text(
        'from config.settings import *\n'
        + 'MEDIA_ROOT = '+repr(str(django_settings.MEDIA_ROOT))+'\n'
        + 'CELERY_TASK_ALWAYS_EAGER = True\nCELERY_TASK_EAGER_PROPAGATES = True\n'
        + 'CELERY_BEAT_SCHEDULE = {}\nCELERY_RESULT_BACKEND = "cache+memory://"\n'
    )
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        port = port_socket.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    logfile = tmp_path / 'gunicorn-private.log'
    accessfile = tmp_path / 'gunicorn-access.log'
    rows, cold, uploads = [], [], []
    with connection.cursor() as cursor:
        cursor.execute('SHOW server_version')
        postgres_version = cursor.fetchone()[0]
    resources = {'os': platform.platform(), 'cpu_count': os.cpu_count(), 'cpu_affinity_count': len(os.sched_getaffinity(0)),
                 'postgres_version': postgres_version, 'gunicorn_version': version('gunicorn'),
                 'django_version': version('Django'), 'python_version': platform.python_version(),
                 'pg_server_shared': True, 'limits': 'Runner database isolated; PostgreSQL service and host shared with idle normal stack. No competing test/build workload.'}
    for name, file in [('memory_total', '/proc/meminfo'), ('cgroup_memory_max', '/sys/fs/cgroup/memory.max'), ('cgroup_cpu_max', '/sys/fs/cgroup/cpu.max')]:
        if Path(file).is_file():
            value = Path(file).read_text()
            resources[name] = value.splitlines()[0] if name == 'memory_total' else value.strip()
    process = None
    summary = {'dataset': dataset, 'resources': resources, 'success': False, 'duration_seconds': 900 if large else 2,
               'arrival_rps': 20 if large else 6, 'server': 'Gunicorn4 sync workers local TCP',
               'scope': 'Synthetic local server capacity; external production/identity/CDN excluded. Upload processing eager in request, no real worker throughput claim.'}
    routes = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic',
              '/es/listing/'+dataset['sample_ids'][0]+'/', '/en/listing/'+dataset['sample_ids'][-1]+'/']

    def fetch(path, *, data=None, headers=None, expected=200, scheduled=None):
        begin = time.perf_counter()
        result = {'path': path, 'expected': expected, 'scheduled_lag_seconds': max(0, begin-scheduled) if scheduled else 0}
        request = urllib.request.Request(origin+path, data=data, headers=headers or {})
        try:
            try:
                response = urllib.request.build_opener(NoRedirect()).open(request, timeout=65)
            except urllib.error.HTTPError as error:
                response = error
            with response:
                payload = response.read()
                result.update(status=response.code, bytes=len(payload), unexpected=response.code != expected)
        except (OSError, TimeoutError) as error:
            result.update(status=0, bytes=0, unexpected=True, error=type(error).__name__)
        result['seconds'] = time.perf_counter()-begin
        return result

    try:
        with logfile.open('w') as output:
            process = subprocess.Popen([sys.executable, '-m', 'gunicorn', 'config.wsgi:application',
                                        '--bind', f'127.0.0.1:{port}', '--workers', '4', '--timeout', '60',
                                        '--access-logfile', str(accessfile),
                                        '--access-logformat', '%(s)s %(L)s %(U)s', '--error-logfile', '-', '--graceful-timeout', '10'],
                                       env=environment, stdout=output, stderr=output, start_new_session=True)
        deadline = time.monotonic()+30
        while True:
            assert process.poll() is None, 'Gunicorn exited during startup'
            try:
                with urllib.request.urlopen(origin+'/health/', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                if time.monotonic() >= deadline:
                    raise AssertionError('Gunicorn did not become healthy')
                time.sleep(0.1)
        for path in routes:
            cold.append(fetch(path))
        summary['cold_probes'] = cold
        assert all(not row['unexpected'] for row in cold), 'Cold HTTP prerequisite failed; full workload not executed'
        if large:
            assert percentile([row['seconds'] for row in cold], 0.95) < 0.8, 'Cold latency prerequisite failed; full workload not executed'
        manager = User.objects.get(username='fixture-v1-individual')
        person = Person.objects.get(individual=manager)
        client = Client()
        client.force_login(manager)
        cookies = http.cookies.SimpleCookie()
        with urllib.request.urlopen(origin+'/es/account/login/', timeout=65) as response:
            for value in response.headers.get_all('Set-Cookie', []):
                cookies.load(value)
        csrf = cookies[django_settings.CSRF_COOKIE_NAME].value
        cookie = f'{django_settings.SESSION_COOKIE_NAME}={client.cookies[django_settings.SESSION_COOKIE_NAME].value}; {django_settings.CSRF_COOKIE_NAME}={csrf}'
        draft_rows = Revision.objects.bulk_create([Revision(listing=person.listing, manager_version=person.manager_version) for _ in range(16 if large else 1)])
        raw = raw_image(782134)
        boundary = 'synthetic-'+uuid4().hex
        multipart = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="synthetic.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
        headers = {'Cookie': cookie, 'X-CSRFToken': csrf, 'Referer': origin+'/es/',
                   'Content-Type': 'multipart/form-data; boundary='+boundary}
        completed = queue.SimpleQueue()
        started = time.perf_counter()
        count = int(summary['duration_seconds']*summary['arrival_rps'])
        outstanding = set()
        upload_futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=80) as pool:
            for index in range(count):
                scheduled = started+index/summary['arrival_rps']
                time.sleep(max(0, scheduled-time.perf_counter()))
                outstanding = {future for future in outstanding if not future.done()}
                if len(outstanding) >= 80:
                    rows.append({'unexpected': True, 'status': 0, 'error': 'arrival_capacity_exhausted', 'seconds': None})
                else:
                    future = pool.submit(fetch, routes[index % len(routes)], scheduled=scheduled)
                    future.add_done_callback(lambda done: completed.put(done.result()))
                    outstanding.add(future)
                if index % (summary['arrival_rps']*60) == 0:
                    draft = draft_rows[len(upload_futures)]
                    upload_futures.append(pool.submit(fetch, f'/es/draft/{draft.pk}/photos/upload/', data=multipart, headers=headers, expected=302))
            for future in upload_futures:
                uploads.append(future.result())
        while not completed.empty():
            rows.append(completed.get())
        summary.update(observed_seconds=time.perf_counter()-started, scheduled_requests=count,
                       recorded_requests=len(rows), unexpected=sum(row['unexpected'] for row in rows),
                       client_p95_seconds=percentile([row['seconds'] for row in rows if row['seconds'] is not None], 0.95),
                       uploads=uploads, samples=rows)
        assert len(rows) == count and all(not row['unexpected'] for row in uploads)
        assert uploads and all(row['bytes'] > 0 for row in rows if row.get('status') == 200)
        if not large:
            assert summary['unexpected'] == 0, 'Functional HTTP load returned unexpected results'
        if large:
            assert summary['unexpected']/count < 0.01 and summary['client_p95_seconds'] < 0.8
        summary['success'] = True
    finally:
        if process and process.poll() is None:
            import signal

            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
        summary['gunicorn_stopped'] = process is None or process.poll() is not None
        if logfile.exists():
            import re

            summary['startup_error_types'] = re.findall(r'([A-Za-z]+Error):', logfile.read_text())[-10:]
        summary['cold_probes'] = cold
        if accessfile.exists():
            server_rows = [line.split() for line in accessfile.read_text().splitlines()]
            summary['gunicorn_service_p95_seconds'] = percentile([float(row[1]) for row in server_rows if len(row) >= 3], 0.95)
        (tmp_path / 'load-summary.json').write_text(json.dumps(summary, indent=2))
        compact = {key: value for key, value in summary.items() if key != 'samples'}
        record_property('load_summary', json.dumps(compact))
