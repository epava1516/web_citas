"""Explicit PostgreSQL snapshot measurement; synthetic rows, not public capacity."""
import hashlib
import json
import os
import resource
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from django.db import connection
from django.utils import timezone

from apps.core.operational_snapshot import collect_snapshot
from apps.listings.models import PublicationDirty
from apps.mediafiles.models import Blob, MediaPreparationCleanup
from apps.safety.crypto import seal
from apps.safety.models import Report, ReportNotice


def rss_bytes():
    return next(int(line.split()[1]) * 1024 for line in Path('/proc/self/status').read_text().splitlines()
                if line.startswith('VmRSS:'))


@pytest.mark.django_db(transaction=True)
def test_snapshot_cost_empty_then_fifty_thousand_synthetic_rows():
    run_id = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
    if not run_id:
        pytest.skip('Explicit isolated local CI run required')
    root = Path(__file__).resolve().parents[1] / 'artifacts' / 'local-ci'
    output = root / run_id / 'snapshot-cost.json'
    assert output.resolve().is_relative_to(root.resolve())
    assert output.parent.is_dir() and not output.exists()
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_')
    results = []
    now = timezone.now()
    for size in (0, 10000):
        if size:
            PublicationDirty.objects.bulk_create([
                PublicationDirty(listing_id=uuid4(), generation=1, marked_at=now - timedelta(minutes=10))
                for _ in range(size)
            ], batch_size=1000)
            # Synthetic diagnostic rows: no moderation/authority/delivery claim.
            report = Report.objects.create(
                submission_key=uuid4(), receipt_digest='a' * 64, payload_digest='b' * 64,
                encrypted_payload=seal({'synthetic': True}), mode='listing', reason='other',
                receipt_expires_at=now + timedelta(days=1),
            )
            payload = seal({'recipient': 'synthetic@example.invalid', 'subject': 'Synthetic', 'body': 'Synthetic'})
            modes = [('queued', 0, None), ('retry', 1, now),
                     ('retry', 1, now + timedelta(hours=1)), ('retry', 5, now), ('failed', 5, None)]
            ReportNotice.objects.bulk_create([
                ReportNotice(event_key=f'snapshot-cost-{index}', report=report, kind='receipt',
                             encrypted_payload=payload, status=modes[index % 5][0],
                             attempts=modes[index % 5][1], next_attempt_at=modes[index % 5][2])
                for index in range(size)
            ], batch_size=1000)
            blobs = [Blob(sha256=f'{index + 1:064x}', status='queued' if index < size else 'purging')
                     for index in range(size * 2)]
            Blob.objects.bulk_create(blobs, batch_size=1000)
            MediaPreparationCleanup.objects.bulk_create([
                MediaPreparationCleanup(blob=item, status='failed', attempts=1, next_attempt_at=now)
                for item in blobs[size:]
            ], batch_size=1000)
        initial_rss = rss_bytes()
        first_start = time.perf_counter_ns()
        collect_snapshot()
        first_ns = time.perf_counter_ns() - first_start
        for _ in range(5):
            collect_snapshot()
        walls, cpus = [], []
        for _ in range(30):
            cpu_start = time.process_time_ns()
            tick = time.perf_counter_ns()
            snapshot = collect_snapshot()
            walls.append(time.perf_counter_ns() - tick)
            cpus.append(time.process_time_ns() - cpu_start)
            assert snapshot['publication']['count'] == size
            assert {key: value['count'] for key, value in snapshot['notices']['ReportNotice'].items()} == {
                'due': size * 2 // 5, 'scheduled': size // 5,
                'exhausted': size // 5, 'failed': size // 5,
            }
            assert connection.get_autocommit() and not connection.in_atomic_block
            assert snapshot['media']['processing']['queued']['count'] == size
            assert snapshot['media']['physical_jobs']['MediaPreparationCleanup']['due']['count'] == size
        sql = {'statements': 0, 'selects': 0, 'execute_ns': 0}

        def measure(execute, statement, params, many, context):
            started = time.perf_counter_ns()
            try:
                return execute(statement, params, many, context)
            finally:
                sql['statements'] += 1
                sql['selects'] += statement.startswith('SELECT')
                sql['execute_ns'] += time.perf_counter_ns() - started

        with connection.execute_wrapper(measure):
            collect_snapshot()
        results.append({'dirty_rows': size, 'notice_rows': size, 'warmups': 5,
                        'media_blob_rows': size * 2, 'preparation_cleanup_rows': size,
                        'measured_calls': 30, 'first_call_ns': first_ns,
                        'wall_ns': walls, 'client_cpu_ns': cpus,
                        'rss_before_bytes': initial_rss, 'rss_after_bytes': rss_bytes(),
                        'process_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
                        'separate_sql_observation': sql})
    assert ReportNotice.objects.count() == PublicationDirty.objects.count() == 10000
    assert Blob.objects.count() == 20000 and MediaPreparationCleanup.objects.count() == 10000
    sources = ['tests/beta_snapshot_cost_diagnostic.py', 'apps/core/operational_snapshot.py']
    output.write_text(json.dumps({
        'scope': 'Actual PostgreSQL aggregate snapshot, isolated synthetic rows only',
        'samples': results, 'order': ['empty', '10000dirty_and_10000notices'],
        'source_sha256': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sources},
        'limits': ['One fixed order and warm local PostgreSQL, no cold database guarantee',
                   'MediaErasure and other snapshot tables remain empty; not every production cardinality',
                   'Client CPU excludes PostgreSQL server CPU; SQL execute excludes fetch',
                   'RSS samples and whole-process high water include fixture/test process',
                   'No capacity, provider delivery, cadence or B12 acceptance'],
    }, indent=2) + '\n')
