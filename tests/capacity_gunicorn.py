"""Owned two-process WSGI server inside the already constrained test container."""

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace

from django.db import connection


@contextmanager
def server(settings, record_property):
    import json

    config = Path('/tmp/capacity_gunicorn_settings.py')
    config.write_text("from capacity_settings import *\n" +
                      f"DATABASES['default']['NAME'] = {connection.settings_dict['NAME']!r}\n" +
                      f"MEDIA_ROOT = {str(settings.MEDIA_ROOT)!r}\n" +
                      "RIGHTS_VERIFICATION_BACKEND = 'simulator'\n")
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'capacity_gunicorn_settings'
    application = 'config.wsgi:application'
    if getattr(settings, 'CAPACITY_SELECTION_PROFILE', False):
        Path('/tmp/capacity_profile_wsgi.py').write_text(Path(__file__).with_name('capacity_profile_wsgi.py').read_text())
        application = 'capacity_profile_wsgi:application'
    command = [sys.executable, '-m', 'gunicorn', application, '--workers', '2',
               '--worker-class', 'sync', '--bind', f'127.0.0.1:{port}', '--timeout', '90',
               '--access-logfile', '-', '--error-logfile', '-',
               '--logger-class', 'config.gunicorn_logging.SafeAccessLogger']
    log_path = Path('/tmp/capacity-gunicorn.log')
    stop, peaks = Event(), {}
    with log_path.open('w') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)

        def sample():
            while not stop.is_set():
                for path in Path('/proc').iterdir():
                    if not path.name.isdecimal():
                        continue
                    try:
                        status = dict(line.split(':', 1) for line in (path / 'status').read_text().splitlines() if ':' in line)
                        if int(path.name) == process.pid or int(status.get('PPid', '-1')) == process.pid:
                            value = int(status['VmHWM'].split()[0]) * 1024
                            peaks[path.name] = max(value, peaks.get(path.name, 0))
                    except (OSError, ValueError, KeyError):
                        continue
                stop.wait(.1)

        sampler = Thread(target=sample, daemon=True)
        sampler.start()
        url = f'http://127.0.0.1:{port}'
        try:
            for _ in range(100):
                if process.poll() is not None:
                    raise RuntimeError('Own Gunicorn exited before readiness: ' + log_path.read_text()[-3000:])
                try:
                    with urllib.request.urlopen(url + '/health/', timeout=1) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(.1)
            else:
                raise RuntimeError('Own Gunicorn readiness failed')
            yield SimpleNamespace(url=url)
        finally:
            stop.set()
            sampler.join(timeout=2)
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
            record_property('gunicorn_server', json.dumps({
                'command': command, 'exit': process.returncode, 'rss_peaks_bytes': peaks,
                'log': log_path.read_text()[-20000:],
                'extra_profiles': {path.name: path.read_text() for path in Path('/tmp').glob('capacity-profile-*.txt')},
                'scope': 'Master and workers kernel VmHWM sampled100ms; process-group teardown. Same owned app cgroup; no Caddy or deployment.',
            }))
            assert len(peaks) >= 3, 'Missing actual Gunicorn master/two-worker RSS observations'
            assert all(value <= 1024 ** 3 for value in peaks.values()), 'Gunicorn process RSS exceeds1GiB'
