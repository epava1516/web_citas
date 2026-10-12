"""Owned two-process WSGI server inside the already constrained test container."""

import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from contextlib import ExitStack, contextmanager
from pathlib import Path
from threading import Event, Thread
from types import SimpleNamespace
from uuid import uuid4

from capacity_request_timing import collect as collect_request_timings
from django.db import connection


def wait_observed_exit(pids, *, proc=Path('/proc'), timeout=5):
    """Require disappearance, including zombies; allow init's asynchronous reaping."""
    deadline = time.monotonic() + timeout
    while True:
        remaining = [pid for pid in pids if (proc / str(pid)).exists()]
        if not remaining:
            return
        if time.monotonic() >= deadline:
            states = {}
            for pid in remaining:
                try:
                    states[pid] = (proc / str(pid) / 'stat').read_text()[:512]
                except OSError:
                    states[pid] = 'disappeared during final inspection'
            raise AssertionError('Observed app process survived teardown: ' + str(states))
        time.sleep(.05)


@contextmanager
def server(settings, record_property):
    import json

    config = Path('/tmp/capacity_gunicorn_settings.py')
    config.write_text("from capacity_settings import *\n" +
                      f"DATABASES['default']['NAME'] = {connection.settings_dict['NAME']!r}\n" +
                      f"MEDIA_ROOT = {str(settings.MEDIA_ROOT)!r}\n" +
                      "RIGHTS_VERIFICATION_BACKEND = 'simulator'\n")
    async_enabled = any(getattr(settings, flag, False) for flag in (
        'CAPACITY_DELIVERY_COMPLETE', 'CAPACITY_DELIVERY_PROFILE_FULL', 'CAPACITY_PREFLIGHT_ONLY'))
    if async_enabled:
        with config.open('a') as generated:
            generated.write("CELERY_TASK_ALWAYS_EAGER = False\n")
            generated.write("CELERY_BEAT_SCHEDULE = dict(CELERY_BEAT_SCHEDULE)\n")
            generated.write("CELERY_BEAT_SCHEDULE.update({"
                "'reconcile-portability-export-jobs': {'task': 'apps.safety.tasks.reconcile_portability_export_jobs', 'schedule': 60.0},"
                "'purge-rights-object-deliveries': {'task': 'apps.safety.rights_object_delivery.purge_object_deliveries', 'schedule': 10.0},"
                "'purge-orphan-export-objects': {'task': 'apps.safety.rights_object_content.purge_orphan_export_objects', 'schedule': 3600.0}})\n")
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    objects = getattr(settings, "CAPACITY_OBJECT_DELIVERY", False)
    if objects:
        port = 8000
    bind = "0.0.0.0" if objects else "127.0.0.1"
    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = 'capacity_gunicorn_settings'
    application = 'config.wsgi:application'
    if (getattr(settings, 'CAPACITY_SELECTION_PROFILE', False)
            or getattr(settings, 'CAPACITY_REQUEST_TIMING', False)):
        Path('/tmp/capacity_request_timing.py').write_text(Path(__file__).with_name('capacity_request_timing.py').read_text())
        Path('/tmp/capacity_profile_wsgi.py').write_text(Path(__file__).with_name('capacity_profile_wsgi.py').read_text())
        Path('/tmp/capacity_worker_profile.py').write_text(Path(__file__).with_name('capacity_worker_profile.py').read_text())
        Path('/tmp/capacity_phase_spans.py').write_text(Path(__file__).with_name('capacity_phase_spans.py').read_text())
        application = 'capacity_profile_wsgi:application'
        if getattr(settings, 'CAPACITY_PROFESSIONAL_PROFILE', None):
            Path('/tmp/capacity_professional_profile.py').write_text(
                Path(__file__).with_name('capacity_professional_profile.py').read_text())
        if getattr(settings, 'CAPACITY_NATIVE_PROFILE', False):
            Path('/tmp/capacity_native_profile.py').write_text(
                Path(__file__).with_name('capacity_native_profile.py').read_text())
            with connection.cursor() as cursor:
                cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_stat_statements')
    command = [sys.executable, '-m', 'gunicorn', application, '--workers', '2',
               '--worker-class', 'sync', '--bind', f'{bind}:{port}', '--timeout', '90',
               '--access-logfile', '-', '--error-logfile', '-',
               '--logger-class', 'config.gunicorn_logging.SafeAccessLogger']
    scalene_mode = getattr(settings, 'CAPACITY_PROFESSIONAL_PROFILE', None) == 'scalene'
    if scalene_mode:
        tools_site = str(Path(settings.CAPACITY_DIAGNOSTIC_TOOLS_VENV) / 'lib/python3.12/site-packages')
        app_site = str(Path(sys.prefix) / 'lib/python3.12/site-packages')
        env['PYTHONPATH'] = env.get('PYTHONPATH', '') + ':' + app_site + ':' + tools_site
        Path('/tmp/capacity_scalene_launcher.py').write_text(
            "import runpy\nrunpy.run_module('gunicorn', run_name='__main__')\n")
        command = [sys.executable, '-m', 'scalene', 'run', '--cpu-only', '--off', '--profile-all',
                   '--profile-only', 'apps/safety,capacity_professional_profile',
                   '-o', '/tmp/capacity-professional-scalene-all.json',
                   '/tmp/capacity_scalene_launcher.py', '---', *command[3:]]
    log_path = Path('/tmp/capacity-gunicorn.log')
    stop, peaks = Event(), {}
    owned = []
    async_name = 'capacity-async-' + uuid4().hex + '@localhost'
    async_logs = {}
    with ExitStack() as stack:
        if async_enabled:
            from capacity_runtime_role import runtime_role_environment
            env.update(stack.enter_context(runtime_role_environment()))
        log = stack.enter_context(log_path.open('w'))
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        owned.append(('gunicorn', process, command, log_path))

        def sample():
            while not stop.is_set():
                statuses = {}
                for path in Path('/proc').iterdir():
                    if not path.name.isdecimal():
                        continue
                    try:
                        statuses[int(path.name)] = dict(line.split(':', 1) for line in
                            (path / 'status').read_text().splitlines() if ':' in line)
                    except (OSError, ValueError):
                        continue
                descendants = {item[1].pid for item in owned}
                changed = True
                while changed:
                    before_count = len(descendants)
                    descendants.update(pid for pid, status in statuses.items()
                                       if int(status.get('PPid', '-1')) in descendants)
                    changed = len(descendants) != before_count
                for pid in descendants:
                    try:
                        value = int(statuses[pid]['VmHWM'].split()[0]) * 1024
                        peaks[str(pid)] = max(value, peaks.get(str(pid), 0))
                    except (ValueError, KeyError):
                        continue
                stop.wait(.1)

        sampler = Thread(target=sample, daemon=True)
        sampler.start()
        url = f'http://127.0.0.1:{port}'
        try:
            if async_enabled:
                worker_command = [sys.executable, '-m', 'celery', '-A', 'config', 'worker',
                    '--pool=prefork', '--concurrency=2', '--hostname=' + async_name,
                    '--without-gossip', '--without-mingle', '--loglevel=WARNING',
                    '-Q', settings.CELERY_TASK_DEFAULT_QUEUE]
                beat_command = [sys.executable, '-m', 'celery', '-A', 'config', 'beat',
                    '--loglevel=WARNING', '--schedule=/tmp/capacity-celerybeat',
                    '--pidfile=/tmp/capacity-celerybeat.pid']
                for role, task_command in [('worker', worker_command), ('beat', beat_command)]:
                    task_log = Path('/tmp/capacity-' + role + '.log')
                    handle = stack.enter_context(task_log.open('w'))
                    child = subprocess.Popen(task_command, env=env, stdout=handle,
                        stderr=subprocess.STDOUT, start_new_session=True)
                    owned.append((role, child, task_command, task_log))
                # All process roots inherit the constrained container; verify actual cgroup.
                own_cgroup = Path('/proc/self/cgroup').read_text()
                for role, child, _, _ in owned:
                    assert Path(f'/proc/{child.pid}/cgroup').read_text() == own_cgroup, role
                from config.celery import app
                deadline = time.monotonic() + 45
                while time.monotonic() < deadline:
                    assert all(child.poll() is None for _, child, _, _ in owned)
                    replies = app.control.inspect(destination=[async_name], timeout=1).ping()
                    if replies and replies.get(async_name, {}).get('ok') == 'pong':
                        break
                    time.sleep(.2)
                else:
                    raise RuntimeError('Own Celery worker readiness failed')
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
            if objects:
                # Same own network; no host ports. File route health is an expected404.
                try:
                    urllib.request.urlopen("http://caddy:8080/", timeout=3)
                except urllib.error.HTTPError as error:
                    assert error.code == 404
            yield SimpleNamespace(url=url, object_delivery=objects,
                                  runtime_config=env.get("RIGHTS_EVIDENCE_RUNTIME_CONFIG"))
        finally:
            stop.set()
            sampler.join(timeout=2)
            for role, child, _, task_log in reversed(owned):
                if child.poll() is None:
                    if role == 'gunicorn' and scalene_mode:
                        stop_scalene_master(child)
                    else:
                        os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait(timeout=5)
                assert not Path(f'/proc/{child.pid}').exists(), role + ' process survived teardown'
                async_logs[role] = {'pid': child.pid, 'exit': child.returncode,
                    'log': task_log.read_text()[-20000:]}
            wait_observed_exit(peaks)
            record_property('async_generation_server', json.dumps({
                'enabled': async_enabled, 'processes': async_logs,
                'rss_peaks_bytes': peaks,
                'scope': 'Gunicorn and Celery prefork 2 plus Beat share the same owned app cgroup; sampled 100 ms; process groups terminated.'}))
            compact_scalene_profile()
            record_property('gunicorn_server', json.dumps({
                'command': command, 'exit': process.returncode, 'rss_peaks_bytes': peaks,
                'log': log_path.read_text()[-20000:],
                'request_timings': collect_request_timings(),
                'extra_profiles': {path.name: path.read_text() for path in Path('/tmp').glob('capacity-profile-*.txt')},
                'professional_profiles': {path.name: path.read_text() for path in Path('/tmp').glob('capacity-professional-*.json')},
                'native_profiles': {path.name: path.read_text() for path in Path('/tmp').glob('capacity-native-*.json')},
                'scope': 'Master and workers kernel VmHWM sampled100ms; process-group teardown. Same owned app cgroup; optional Caddy and RustFS separate owned cgroups, never deployment.',
            }))
            assert len(peaks) >= 3, 'Missing actual Gunicorn master/two-worker RSS observations'
            if async_enabled:
                assert len(peaks) >= 7, 'Missing Gunicorn/worker prefork 2/Beat RSS observations'
            assert all(value <= 1024 ** 3 for value in peaks.values()), 'App process RSS exceeds1GiB'


def stop_scalene_master(process):
    """Signal the sole owned CLI child; allow CLI to merge and exit normally."""
    children = []
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            fields = (path / 'stat').read_text().rsplit(')', 1)[1].split()
            if int(fields[1]) == process.pid:
                children.append(int(path.name))
        except (OSError, ValueError, IndexError):
            continue
    if not children and process.poll() is not None:
        return
    if len(children) != 1:
        raise AssertionError('Scalene CLI requires one observed Gunicorn child: ' + str(children))
    os.kill(children[0], signal.SIGTERM)


def compact_scalene_profile():
    """Bounded CPU evidence; exclude source text and raw sampling arrays."""
    import hashlib
    import json

    path = Path('/tmp/capacity-professional-scalene-all.json')
    if not path.exists():
        return
    if path.stat().st_size > 16 * 1024 * 1024:
        raise RuntimeError('Scalene raw profile exceeds bounded evidence size')
    raw = path.read_bytes()
    data = json.loads(raw)
    kept = {}
    count = 0
    fields = ('lineno', 'n_cpu_percent_python', 'n_cpu_percent_c', 'n_sys_percent')
    for filename, file in data.get('files', {}).items():
        lines = []
        for line in file.get('lines', []):
            if sum(line.get(k, 0) for k in fields[1:]) <= 0:
                continue
            count += 1
            if count > 2000:
                raise RuntimeError('Scalene CPU line count exceeds diagnostic bound')
            lines.append({k: line.get(k, 0) for k in fields})
        if lines:
            kept[filename] = {'percent_cpu_time': file['percent_cpu_time'], 'lines': lines}
    path.write_text(json.dumps({'instrument': 'scalene-cpu-only', 'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'elapsed_time_sec': data.get('elapsed_time_sec'), 'files': kept,
        'scope': 'Merged CPU samples of explicitly marked worker windows; filtered application/helper code. No source text, frame locals or payloads. Not HTTPp95.'}))
