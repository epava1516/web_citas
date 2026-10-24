"""Actual prefork/task/outbox recovery with natural backoff; local simulator only."""
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
from django.db import connection
from django.utils import timezone
from test_notice_delivery import queued
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.operational_assessment import assess
from apps.core.operational_snapshot import collect_snapshot
from apps.core.operational_window import summarize_window
from apps.listings import publication_state
from apps.listings.models import PublicationDirty
from apps.safety.models import SimulatedComplaintNoticeDelivery
from config.celery import app


@pytest.mark.django_db(transaction=True)
def test_prefork_outbox_failure_natural_backoff_then_unique_recovery(request, settings, tmp_path):
    notice, _ = queued(request, settings)
    assert collect_snapshot()['notices']['ComplaintNotice']['due']['count'] == 1
    queue = 'notice_recovery_probe_' + uuid4().hex
    log = tmp_path / 'worker.log'
    marker = tmp_path / 'failed-once'
    database = connection.settings_dict
    assert database['NAME'].startswith('test_')
    environment = {
        **os.environ, 'POSTGRES_DB': database['NAME'], 'POSTGRES_USER': database['USER'],
        'POSTGRES_PASSWORD': database['PASSWORD'], 'DB_HOST': database['HOST'],
        'DB_PORT': str(database['PORT']), 'SAFETY_NOTICE_BACKEND': 'simulator',
    }
    task = 'apps.safety.tasks.deliver_safety_notices'

    def events(task_name=task):
        rows = []
        for line in log.read_text().splitlines():
            if not line.startswith('{'):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get('event') == 'task_result' and (task_name is None or row.get('task') == task_name):
                rows.append(row)
        return rows

    def wait(predicate, timeout=35):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            assert process.poll() is None, 'Owned prefork worker terminated'
            if predicate():
                return
            time.sleep(.1)
        raise AssertionError('Owned prefork observation deadline exceeded')

    def dispatch(expected_count):
        app.send_task(task, queue=queue)
        wait(lambda: len(events()) >= expected_count)
        return events()[expected_count - 1]

    def assessment(start=None):
        now = int(timezone.now().timestamp())
        rows = b''.join(json.dumps(row).encode() + b'\n' for row in events(None))
        observed = summarize_window(io.BytesIO(rows), start if start is not None else now - 59, now + 1)
        started = time.perf_counter()
        snapshot = collect_snapshot()
        return assess(snapshot, observed, collection_seconds=time.perf_counter() - started)

    with log.open('w') as output:
        process = subprocess.Popen(
            [sys.executable, '-m', 'scripts.probe_notice_recovery', '--queue', queue,
             '--failure-marker', str(marker)], env=environment,
            cwd=Path(__file__).resolve().parents[1], stdout=output,
            stderr=subprocess.STDOUT, start_new_session=True,
        )
    try:
        wait(lambda: ' ready.' in log.read_text())
        before = timezone.now()
        first = dispatch(1)
        notice.refresh_from_db()
        assert marker.exists() and notice.status == 'retry' and notice.attempts == 1
        assert notice.error_code == 'adapter_failure'
        due_at = notice.next_attempt_at
        assert 59 <= (due_at - before).total_seconds() <= 65
        assert SimulatedComplaintNoticeDelivery.objects.count() == 0
        snapshot = collect_snapshot()['notices']['ComplaintNotice']
        assert snapshot['scheduled']['count'] == 1 and snapshot['due']['count'] == 0
        assert first['outcome'] == 'succeeded' and first['delivery_counts']['retry'] == 1
        interrupted = assessment()
        interrupted_codes = {row['code'] for row in interrupted['findings']}
        assert 'delivery_retry_observed' in interrupted_codes
        assert 'task_failed_observed' not in interrupted_codes
        assert 'notice_due_wait_old' not in interrupted_codes
        assert dispatch(2)['delivery_counts']['processed'] == 0
        notice.refresh_from_db()
        assert notice.attempts == 1 and notice.next_attempt_at == due_at
        # Real wall-clock backoff. No DB timestamp manipulation or frozen clock.
        wait(lambda: timezone.now() >= due_at, timeout=70)
        assert collect_snapshot()['notices']['ComplaintNotice']['due']['count'] == 1
        recovered = dispatch(3)
        notice.refresh_from_db()
        assert notice.status == 'simulated' and notice.attempts == 2
        assert notice.error_code == '' and notice.next_attempt_at is None
        assert recovered['delivery_counts']['simulated'] == 1
        assert SimulatedComplaintNoticeDelivery.objects.count() == 1
        assert dispatch(4)['delivery_counts']['processed'] == 0
        assert SimulatedComplaintNoticeDelivery.objects.count() == 1
        assert all(row['outcome'] == 'succeeded' for row in events())
        assert len(events()) == 4
        assert 'example.invalid' not in json.dumps(events())
        assert 'Synthetic local adapter interruption' not in json.dumps(events())
        assert collect_snapshot()['notices']['ComplaintNotice']['due']['count'] == 0
        resolved = assessment(start=recovered['timestamp_seconds'])
        assert resolved['health'] == 'unknown' and resolved['coverage'] == 'unverified'
        assert not {'delivery_retry_observed', 'notice_due_wait_old', 'notice_failed'} & {
            row['code'] for row in resolved['findings']}
        # Fixture-controlled lag age; actual domain refresh runs in the owned worker.
        publication_state.mark_all()
        assert PublicationDirty.objects.exists()
        PublicationDirty.objects.update(marked_at=timezone.now() - timedelta(minutes=5))
        publication_interrupted = assessment(start=recovered['timestamp_seconds'])
        assert 'publication_backlog_old' in {row['code'] for row in publication_interrupted['findings']}
        publication_task = 'apps.listings.tasks.refresh_publication_state'
        app.send_task(publication_task, queue=queue)
        wait(lambda: any(row['outcome'] == 'succeeded' for row in events(publication_task)))
        assert PublicationDirty.objects.count() == 0
        publication_event = events(publication_task)[-1]
        publication_resolved = assessment(start=publication_event['timestamp_seconds'])
        assert 'publication_backlog_old' not in {row['code'] for row in publication_resolved['findings']}
        assert publication_resolved['health'] == 'unknown'
        run_id = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
        if run_id:
            root = Path(__file__).resolve().parents[1] / 'artifacts' / 'local-ci'
            output = root / run_id / 'assessment-outbox-runbook.json'
            assert output.resolve().is_relative_to(root.resolve()) and not output.exists()
            output.write_text(json.dumps({
                'scope': 'Actual prefork2 outbox failure/recovery, local simulator only',
                'interrupted': interrupted, 'after_recovery_new_window': resolved,
                'publication_interrupted': publication_interrupted,
                'publication_after_worker': publication_resolved,
                'publication_lag_age': 'fixture-controlled300seconds',
                'publication_dirty_after_worker': 0,
                'backoff': 'natural60seconds', 'unique_simulated_receipt_count': 1,
                'no_all_clear_claim': True,
            }, indent=2) + '\n')
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=5)
        assert process.poll() is not None
        with app.connection_for_write() as broker:
            broker.default_channel.queue_delete(queue)
