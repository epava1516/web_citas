"""Bounded real Gunicorn startup witness, not a capacity rerun."""
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
from django.db import connection

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_worker_startup_runtime(request, tmp_path, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_worker_startup_runtime.py' for x in request.config.args):
        pytest.skip('Explicit owned runtime diagnostic only')
    out = Path(request.config.getoption('--gate-timings-output')).parent
    run = json.loads((out / 'runner.json').read_text())
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'] == 'web-modelos-ci-pg-' + run['id']
    db = connection.settings_dict
    assert db['NAME'].startswith('test_promotion_gate_')
    (tmp_path / 'startup_runtime_settings.py').write_text(
        'from config.settings import *\nDATABASES["default"]["NAME"] = ' + repr(db['NAME']) + '\n')
    environment = dict(os.environ, DJANGO_SETTINGS_MODULE='startup_runtime_settings',
                       APP_ENV='development', DJANGO_DEBUG='0',
                       PYTHONPATH=str(tmp_path) + os.pathsep + str(Path.cwd()))
    with socket.socket() as reserve:
        reserve.bind(('127.0.0.1', 0))
        port = reserve.getsockname()[1]
    logfile = out / 'gunicorn-startup-runtime.log'
    process = None
    ready = set()
    children = set()
    try:
        with logfile.open('w') as output:
            process = subprocess.Popen(
                [sys.executable, '-m', 'gunicorn', 'config.wsgi:application',
                 '--bind', '127.0.0.1:' + str(port), '--workers', '4', '--timeout', '60',
                 '--access-logfile', '-', '--error-logfile', '-'],
                env=environment, stdout=output, stderr=output, start_new_session=True)
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                text = logfile.read_text()
                children = set(map(int, re.findall(r'Booting worker with pid: (\d+)', text)))
                ready = set(map(int, re.findall(r'Static routes and templates prepared for worker pid=(\d+)', text)))
                assert process.poll() is None, 'Gunicorn exited; inspect preserved owned log'
                if len(ready) == 4:
                    break
                time.sleep(.05)
            assert len(ready) == 4 and ready == children
            with urllib.request.urlopen('http://127.0.0.1:' + str(port) + '/health/', timeout=5) as response:
                assert response.status == 200
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
    assert process.returncode == 0
    record_property('startup_runtime', json.dumps({'ready_before_first_request': sorted(ready), 'health':200, 'master_exit':process.returncode, 'children_absent':True, 'scope':'Four real sync Gunicorn workers, default root config, one health request after all ready, no load or p95.'}))
