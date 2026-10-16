"""Fixed4/6 sync admission contrast under unchanged resource limits, not SLO acceptance."""
import concurrent.futures
import hashlib
import io
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_sync_headroom(request, tmp_path, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_sync_headroom.py' for x in request.config.args):
        pytest.skip('Explicit fixed topology diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    request.getfixturevalue('directory')
    populate(10000)
    call_command('refresh_publication_state', stdout=io.StringIO())
    db = connection.settings_dict
    assert db['NAME'].startswith('test_promotion_gate_')
    (tmp_path / 'headroom_settings.py').write_text(
        'from config.settings import *\nDATABASES["default"]["NAME"] = ' + repr(db['NAME']) + '\n')
    environment = dict(os.environ, DJANGO_SETTINGS_MODULE='headroom_settings', APP_ENV='development',
                       DJANGO_DEBUG='0', PYTHONPATH=str(tmp_path) + os.pathsep + str(Path.cwd()))
    paths = ['/es/', '/en/', '/es/?q=photography', '/en/?q=synthetic']
    expected = {}
    results = []
    for block in range(3):
        for workers in ([4, 6] if block % 2 == 0 else [6, 4]):
            with socket.socket() as reserve:
                reserve.bind(('127.0.0.1', 0))
                port = reserve.getsockname()[1]
            origin = 'http://127.0.0.1:' + str(port)
            logfile = out / f'headroom-{block}-{workers}.log'
            children = set()
            process = None
            try:
                with logfile.open('w') as log:
                    process = subprocess.Popen([sys.executable, '-m', 'gunicorn', 'config.wsgi:application',
                        '--bind', '127.0.0.1:' + str(port), '--workers', str(workers), '--timeout', '60',
                        '--error-logfile', '-'], env=environment, stdout=log, stderr=log, start_new_session=True)
                    deadline = time.monotonic() + 45
                    while time.monotonic() < deadline:
                        text = logfile.read_text()
                        children = set(map(int, re.findall(r'Booting worker with pid: (\d+)', text)))
                        ready = set(map(int, re.findall(r'Static routes and templates prepared for worker pid=(\d+)', text)))
                        assert process.poll() is None
                        if len(ready) == workers:
                            break
                        time.sleep(.05)
                    assert ready == children and len(ready) == workers
                    def fetch(index):
                        wall = time.perf_counter()
                        with urllib.request.urlopen(origin + paths[index % 4], timeout=15) as response:
                            body = response.read()
                            assert response.status == 200 and response.headers['Cache-Control'] == 'no-store'
                        return {'case':index % 4, 'wall_s':time.perf_counter()-wall,
                                'sha256':hashlib.sha256(body).hexdigest()}
                    for index in range(4):
                        row = fetch(index)
                        assert row['sha256'] == expected.setdefault(index, row['sha256'])
                    begin = time.perf_counter()
                    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
                        futures = [pool.submit(fetch, index) for index in range(24)]
                        rows = [future.result() for future in futures]
                    for row in rows:
                        assert row['sha256'] == expected[row['case']]
                    results.append({'block':block, 'workers':workers, 'batch_wall_s':time.perf_counter()-begin,
                                    'ready_pids':sorted(ready), 'rows':rows})
            finally:
                if process is not None:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=5)
                    deadline = time.monotonic() + 5
                    while any(Path('/proc/' + str(pid)).exists() for pid in children) and time.monotonic() < deadline:
                        time.sleep(.05)
                    assert not any(Path('/proc/' + str(pid)).exists() for pid in children)
                (out / 'headroom-results.json').write_text(json.dumps(results, indent=2))
    assert len(results) == 6
    record_property('scope', '144 real HTTP reads in six fixed24request closed-loop bursts, current clean synthetic10k,4/6 sync AB/BA, same4CPUcontroller/PG1CPU/memory. All worker static-ready before requests, exact byte parity. Threadpool scheduling included; no arrival-rate20rps/upload/Celery/dirty/authority revocation or p95 acceptance. No product configuration changed.')
