"""Real owned worker/broker outages; PostgreSQL outbox remains authoritative."""
import io
import json
import os
import signal
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
import redis
from django.db import connection
from django.utils import timezone
from kombu import Connection
from kombu.exceptions import OperationalError
from test_notice_delivery import queued
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.operational_assessment import assess
from apps.core.operational_snapshot import collect_snapshot
from apps.core.operational_window import summarize_window
from apps.safety.models import ComplaintNotice, SimulatedComplaintNoticeDelivery
from config.celery import app


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('outage', ['worker', 'broker'])
def test_owned_service_outage_preserves_outbox_and_recovers_once(request, settings, tmp_path, outage):
    assert os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
    assert connection.settings_dict['NAME'].startswith('test_')
    notice, _ = queued(request, settings)
    due = timezone.now() - timedelta(seconds=180)
    ComplaintNotice.objects.filter(pk=notice.pk).update(created_at=due, next_attempt_at=due)
    container = 'web-modelos-continuity-' + uuid4().hex[:16]
    queue = 'continuity_' + uuid4().hex
    prefix = settings.CELERY_BROKER_TRANSPORT_OPTIONS['global_keyprefix']
    assert prefix == 'clasificados:' + os.environ['TASK_QUEUE_GENERATION'] + ':'
    task = 'apps.safety.tasks.deliver_safety_notices'
    workers, logs, identities = [], [], []
    broker_url = None

    def docker(*args):
        return subprocess.run(['docker', *args], capture_output=True, text=True, check=True, timeout=20)

    def ready_broker():
        port = docker('port', container, '6379').stdout.strip().rsplit(':', 1)[1]
        url = 'redis://127.0.0.1:' + port + '/0'
        client = redis.Redis.from_url(url, socket_connect_timeout=.5, socket_timeout=.5)
        deadline = time.monotonic() + 15
        try:
            while True:
                try:
                    if client.ping():
                        return url
                except redis.exceptions.ConnectionError:
                    pass
                assert time.monotonic() < deadline, 'Owned broker readiness deadline exceeded'
                time.sleep(.1)
        finally:
            client.close()

    def start_worker():
        database = connection.settings_dict
        env = {**os.environ, 'POSTGRES_DB': database['NAME'], 'POSTGRES_USER': database['USER'],
               'POSTGRES_PASSWORD': database['PASSWORD'], 'DB_HOST': database['HOST'],
               'DB_PORT': str(database['PORT']), 'REDIS_URL': broker_url,
               'SAFETY_NOTICE_BACKEND': 'simulator'}
        log = tmp_path / f'worker-{len(workers)}.log'
        with log.open('w') as output:
            process = subprocess.Popen(
                [sys.executable, '-m', 'celery', '-A', 'config', 'worker', '--pool=solo',
                 '--concurrency=1', '--loglevel=INFO', '--without-gossip', '--without-mingle',
                 '--without-heartbeat', '-Q', queue, '--hostname', queue + '@local'],
                env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True,
            )
        workers.append(process)
        fields = Path(f"/proc/{process.pid}/stat").read_text().rsplit(")", 1)[1].split()
        identities.append({"pid": process.pid, "start_ticks": int(fields[19])})
        logs.append(log)
        wait(lambda: ' ready.' in log.read_text(), process)
        return process

    def stop_worker(process, crash=False):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL if crash else signal.SIGTERM)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        assert process.poll() is not None
        if crash:
            assert process.returncode == -signal.SIGKILL

    def wait(predicate, process):
        deadline = time.monotonic() + 35
        while not predicate():
            assert process.poll() is None, 'Owned worker stopped before observation'
            assert time.monotonic() < deadline, 'Owned worker observation deadline exceeded'
            time.sleep(.1)

    def events():
        rows = []
        for log in logs:
            for line in log.read_text().splitlines():
                if not line.startswith('{'):
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if row.get('event') == 'task_result' and row.get('task') == task:
                    rows.append(row)
        return rows

    def dispatch():
        with Connection(broker_url, connect_timeout=.5, transport_options={
                'global_keyprefix': prefix, 'socket_connect_timeout': .5, 'socket_timeout': .5}) as broker:
            # Explicit connection targets only this test's broker; eager mode cannot execute it.
            app.send_task(task, queue=queue, connection=broker, retry=False)

    try:
        docker('run', '--pull=never', '-d', '--name', container,
               '--label', 'web-modelos-continuity-tests', '--cpus', '.25', '--memory', '128m',
               '--memory-swap', '128m', '--log-driver', 'none', '--tmpfs', '/data',
               '-p', '127.0.0.1::6379', 'redis:7.4-alpine', 'redis-server', '--save', '', '--appendonly', 'no')
        broker_url = ready_broker()
        process = start_worker()
        if outage == 'worker':
            stop_worker(process, crash=True)
            dispatch()
            client = redis.Redis.from_url(broker_url)
            try:
                assert client.llen(prefix + queue) == 1
            finally:
                client.close()
        else:
            docker('stop', '-t', '1', container)
            with pytest.raises(OperationalError):
                dispatch()
            stop_worker(process)
        notice.refresh_from_db()
        assert notice.status == 'queued' and notice.attempts == 0
        assert SimulatedComplaintNoticeDelivery.objects.count() == 0
        interrupted = collect_snapshot()
        assert interrupted['notices']['ComplaintNotice']['due']['count'] == 1
        assert 'notice_due_wait_old' in {r['code'] for r in assess(interrupted)['findings']}
        if outage == 'broker':
            docker('start', container)
            broker_url = ready_broker()
        process = start_worker()
        if outage == 'broker':
            dispatch()
        wait(lambda: len(events()) >= 1, process)
        notice.refresh_from_db()
        assert notice.status == 'simulated' and notice.attempts == 1 and notice.error_code == ''
        assert notice.next_attempt_at is None
        assert SimulatedComplaintNoticeDelivery.objects.filter(notice=notice).count() == 1
        assert events()[0]['delivery_counts']['simulated'] == 1
        dispatch()
        wait(lambda: len(events()) >= 2, process)
        notice.refresh_from_db()
        assert notice.attempts == 1 and events()[1]['delivery_counts']['processed'] == 0
        assert SimulatedComplaintNoticeDelivery.objects.count() == 1
        now = int(time.time())
        window = summarize_window(io.BytesIO(b''.join(json.dumps(r).encode() + b'\n' for r in events())), now - 59, now + 1)
        recovered = collect_snapshot()
        assert recovered['notices']['ComplaintNotice']['due']['count'] == 0
        evaluated = assess(recovered, window)
        assert 'notice_due_wait_old' not in {r['code'] for r in evaluated['findings']}
        assert evaluated['health'] == 'unknown'
        assert 'example.invalid' not in json.dumps(events())
        run = os.environ['LOCAL_CI_ISOLATED_BROKER_RUN']
        output = Path(__file__).resolve().parents[1] / 'artifacts' / 'local-ci' / run / f'service-continuity-{outage}.json'
        assert output.parent.is_dir() and not output.exists()
        output.write_text(json.dumps({'scope': 'Owned real services, local simulator only',
                                     'outage': outage, 'pending_before': 1, 'pending_after': 0,
                                     'attempts_after_replay': 1, 'unique_simulated_receipts': 1,
                                     'worker_processes': len(workers), 'worker_identities': identities,
                                     'owned_redis_container': container, 'events': events(),
                                     'age_seconds': 'fixture-controlled180',
                                     'limits': ['No host reboot, mid-task crash or external delivery guarantee',
                                                'Broker has no persistence; PostgreSQL outbox is recovered by normal dispatch']}, indent=2) + '\n')
    finally:
        for worker in workers:
            stop_worker(worker)
        subprocess.run(['docker', 'rm', '-f', '-v', container], capture_output=True, timeout=20)
        absent = subprocess.run(['docker', 'inspect', container], capture_output=True, timeout=10)
        assert absent.returncode != 0 and b'no such' in absent.stderr.lower()
