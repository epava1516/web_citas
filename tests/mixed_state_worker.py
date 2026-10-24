"""Real owned worker/Beat repair for mixed-state equivalence, outside any load."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

from django.db import connection
from test_worker_capacity_comparison import (
    OBSERVER_SETTINGS,
    OWNED_REDIS,
    owned_redis,
    process_tree,
    terminate_owned,
    wait_for_log,
)

from apps.listings.models import PublicationDirty
from scripts.benchmark_refresh_intervals import refresh_intervals


def repair_mixed_with_owned_worker(request, tmp_path, settings):
    # Exact PostgreSQL/Redis ownership checks precede any child or broker access.
    from capacity_runtime_role import _owned_database

    db = _owned_database()
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION and not settings.RECOVERY_MODE
    broker = owned_redis()
    generation = 't'+uuid4().hex[:31]
    prefix = f'clasificados:{generation}:'.encode()
    assert not list(broker.scan_iter(match=prefix+b'*', count=1000))
    preparation_keys = {key: hashlib.sha256(broker.dump(key)).hexdigest()
                        for key in broker.scan_iter(count=1000) if broker.exists(key)}
    assert PublicationDirty.objects.count() == 14
    out = Path(request.config.getoption('--gate-timings-output')).parent
    events = out / 'mixed-worker-events'
    events.mkdir()
    runtime = tmp_path / 'mixed_worker_settings.py'
    runtime.write_text('from config.settings import *\n'
                       + f'MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n'
                       + f'RIGHTS_DELIVERY_ROOT = Path({str(tmp_path / "delivery")!r})\n'
                       + 'PUBLICATION_STATE_READ_REPAIR = False\n'
                       + OBSERVER_SETTINGS)
    env = {**os.environ, 'POSTGRES_DB': db['NAME'], 'DJANGO_SETTINGS_MODULE': 'mixed_worker_settings',
           'PYTHONPATH': str(tmp_path)+os.pathsep+str(Path.cwd()), 'REDIS_URL': OWNED_REDIS,
           'TASK_QUEUE_GENERATION': generation, 'WEB_MODELOS_CELERY_OBSERVER_DIR': str(events)}
    commands = {
        'worker': [sys.executable, '-m', 'celery', '-A', 'config', 'worker', '--loglevel=INFO', '--concurrency=2'],
        'beat': [sys.executable, '-m', 'celery', '-A', 'config', 'beat', '--loglevel=INFO',
                 '--schedule', str(tmp_path / 'celerybeat-schedule')],
    }
    processes = {}
    identities = {}
    report = {'scope': 'Owned functional PostgreSQL/Redis worker and Beat; no HTTP load or quota/capacity credit',
              'dirty_before': 14, 'commands': commands, 'generation': generation,
              'preparation_key_count': len(preparation_keys), 'redis_scope': 'own generation only'}
    started = time.monotonic()
    try:
        for role, command in commands.items():
            with (out / f'mixed-celery-{role}.log').open('w') as log:
                processes[role] = subprocess.Popen(command, env=env | {'WEB_MODELOS_PROCESS_ROLE': role},
                                                   stdout=log, stderr=log, start_new_session=True)
        deadline = time.monotonic()+60
        for role, marker in (('worker', ' ready.'), ('beat', 'beat: Starting')):
            wait_for_log(out / f'mixed-celery-{role}.log', marker, processes[role], deadline)
        for process in processes.values():
            for pid in process_tree(process.pid):
                identities[pid] = int(Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[19])
        ready = time.monotonic()
        while True:
            assert all(process.poll() is None for process in processes.values())
            raw = []
            for path in events.glob('*.jsonl'):
                assert path.stat().st_size <= 1024**2
                raw.extend(json.loads(line) for line in path.read_bytes().splitlines(keepends=True)
                           if line.endswith(b'\n'))
            ledger = refresh_intervals(raw)
            repairs = [row for row in ledger['matched'] if row['publisher_role']=='beat'
                       and row['state']=='SUCCESS' and row.get('cleared', 0)>=14
                       and row.get('dirty_after')==0 and 'snapshot_error' not in row]
            if repairs and not PublicationDirty.objects.exists():
                report.update(ledger=ledger, repairs=repairs, dirty_after=0,
                              after_ready_seconds=time.monotonic()-ready,
                              total_seconds=time.monotonic()-started)
                break
            assert time.monotonic()<ready+45, 'Native Beat/worker did not repair mixed cohort'
            time.sleep(.2)
    finally:
        # Stop the publisher first, then drain/stop its owned worker.
        for role in ('beat', 'worker'):
            if role in processes:
                terminate_owned(processes[role])
        absent = {}
        for pid, ticks in identities.items():
            path = Path(f'/proc/{pid}/stat')
            absent[str(pid)] = not path.exists() or int(path.read_text().rsplit(')', 1)[1].split()[19])!=ticks
        keys = list(broker.scan_iter(match=prefix+b'*', count=1000))
        if keys:
            broker.delete(*keys)
        remaining = set(broker.scan_iter(count=1000))
        preserved = all(hashlib.sha256(broker.dump(key)).hexdigest()==digest
                        for key, digest in preparation_keys.items() if key in remaining)
        report.update(processes_absent=absent,
                      owned_generation_empty=not list(broker.scan_iter(match=prefix+b'*', count=1000)),
                      preparation_keys_preserved=preserved,
                      preparation_keys_expired=len(set(preparation_keys)-remaining),
                      unscoped_new_keys=len(remaining-set(preparation_keys)),
                      roots_exited={role: process.poll() is not None for role, process in processes.items()})
        (out / 'mixed-worker-repair.json').write_text(json.dumps(report, indent=2)+'\n')
    assert identities and all(report['processes_absent'].values())
    assert all(report['roots_exited'].values()) and report['owned_generation_empty']
    assert report['preparation_keys_preserved'] and report['unscoped_new_keys']==0
    assert not PublicationDirty.objects.exists()
    return report
