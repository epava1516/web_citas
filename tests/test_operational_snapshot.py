"""Aggregate privacy, PostgreSQL read-only scope and durable work boundaries."""
import ast
import inspect
import json
from datetime import timedelta
from io import StringIO
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_jobs import enqueue, prepared

from apps.core import operational_snapshot as snapshots
from apps.listings.models import PublicationDirty
from apps.mediafiles.models import Blob, MediaPreparationCleanup
from apps.safety import tasks
from apps.safety.models import Report, ReportNotice

pytestmark = pytest.mark.django_db(transaction=True)


def test_empty_snapshot_has_explicit_scope_and_read_only_aggregates():
    with CaptureQueriesContext(connection) as captured:
        result = snapshots.collect_snapshot()
    assert result['publication'] == {'count': 0, 'oldest_age_seconds': None}
    assert set(result) == {
        'schema_version', 'sampled_at', 'scope', 'export_job_semantics', 'publication',
        'notice_processor', 'notices', 'export_jobs', 'expired_temporaries',
        'unissued_final_drafts', 'not_measured', 'media', 'expired_account_confirmation_delivery',
        'private_delivery_cache', 'object_storage',
    }
    for group in (result['notices']['ReportNotice'], result['export_jobs']):
        for name, metric in group.items():
            expected = {'count', 'oldest_age_seconds'}
            if group is result['notices']['ReportNotice'] and name == 'due':
                expected.add('oldest_due_wait_seconds')
            assert set(metric) == expected
    assert all(set(metric) == {'count', 'oldest_age_seconds', 'task'}
               for metric in result['expired_temporaries'].values())
    assert result['scope'] == 'durable_database_work_only'
    assert 'worker_liveness' in result['not_measured']
    assert all(item['count'] == 0 for item in result['expired_temporaries'].values())
    sql = [row['sql'] for row in captured.captured_queries]
    assert 'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY' in sql
    assert all(query.startswith(('BEGIN', 'SET ', 'SELECT ', 'COMMIT')) for query in sql)
    assert connection.get_autocommit() and not connection.in_atomic_block
    with connection.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only')
        assert cursor.fetchone()[0] == 'off'


def test_due_notice_boundary_and_private_values_never_emitted(monkeypatch, settings):
    now = timezone.now()
    monkeypatch.setattr(snapshots.timezone, 'now', lambda: now)
    settings.PRODUCTION = False
    settings.SAFETY_NOTICE_BACKEND = 'simulator'
    report = Report.objects.create(
        submission_key=uuid4(), receipt_digest='a' * 64, payload_digest='b' * 64,
        encrypted_payload='PRIVATE_REPORT_CONTENT', mode='listing', reason='other',
        receipt_expires_at=now + timedelta(days=1),
    )
    for index, (status, attempts, next_attempt) in enumerate([
        ('queued', 0, None), ('retry', 1, now),
        ('retry', 2, now + timedelta(seconds=1)), ('failed', 5, None),
        ('retry', 5, now), ('simulated', 1, None),
    ]):
        ReportNotice.objects.create(
            event_key=f'PRIVATE_EVENT_{index}', report=report, kind='receipt',
            encrypted_payload='PRIVATE_NOTICE_CONTENT', error_code='PRIVATE_ERROR',
            status=status, attempts=attempts, next_attempt_at=next_attempt,
        )
    PublicationDirty.objects.create(listing_id=uuid4(), generation=1, marked_at=now - timedelta(minutes=4))
    before = list(ReportNotice.objects.order_by('pk').values())
    result = snapshots.collect_snapshot()
    assert result['publication'] == {'count': 1, 'oldest_age_seconds': 240.0}
    notice = result['notices']['ReportNotice']
    assert {key: value['count'] for key, value in notice.items()} == {'due': 2, 'scheduled': 1, 'failed': 1, 'exhausted': 1}
    assert result['notice_processor'] == 'simulator'
    assert list(ReportNotice.objects.order_by('pk').values()) == before
    assert 'PRIVATE_' not in json.dumps(result)
    settings.PRODUCTION = True
    assert snapshots.collect_snapshot()['notice_processor'] == 'disabled'


def test_due_wait_uses_eligibility_not_original_creation_age(monkeypatch):
    now = timezone.now()
    monkeypatch.setattr(snapshots.timezone, 'now', lambda: now)
    report = Report.objects.create(
        submission_key=uuid4(), receipt_digest='c' * 64, payload_digest='d' * 64,
        encrypted_payload='SYNTHETIC_PRIVATE', mode='listing', reason='other',
        receipt_expires_at=now + timedelta(days=1),
    )
    for index, next_attempt in enumerate((now - timedelta(seconds=120), now + timedelta(seconds=1), None)):
        notice = ReportNotice.objects.create(event_key=f'due-wait-{index}', report=report,
                                             kind='receipt', encrypted_payload='SYNTHETIC_PRIVATE',
                                             status='retry' if index < 2 else 'queued',
                                             attempts=1 if index < 2 else 0, next_attempt_at=next_attempt)
        ReportNotice.objects.filter(pk=notice.pk).update(
            created_at=now - timedelta(seconds=3600 if index < 2 else 30))
    result = snapshots.collect_snapshot()['notices']['ReportNotice']
    assert result['due'] == {'count': 2, 'oldest_age_seconds': 3600.0, 'oldest_due_wait_seconds': 120.0}
    assert result['scheduled']['count'] == 1
    ReportNotice.objects.filter(event_key='due-wait-0').update(next_attempt_at=now)
    assert snapshots.collect_snapshot()['notices']['ReportNotice']['due']['oldest_due_wait_seconds'] == 30.0


def test_media_queue_boundaries_do_not_read_storage_paths_or_limit_preparation_retries(monkeypatch):
    now = timezone.now()
    monkeypatch.setattr(snapshots.timezone, 'now', lambda: now)

    def forbidden(*args, **kwargs):
        raise AssertionError('Aggregate snapshot must not access physical storage')

    storage = Blob._meta.get_field('original').storage
    monkeypatch.setattr(storage, 'exists', forbidden)
    monkeypatch.setattr(storage, 'delete', forbidden)

    def blob(status, **values):
        return Blob.objects.create(sha256=uuid4().hex * 2, status=status,
                                   original='SYNTHETIC_PRIVATE_FILE', **values)

    queued = blob('queued')
    Blob.objects.filter(pk=queued.pk).update(created_at=now - timedelta(seconds=240))
    stale = blob('processing', started_at=now - timedelta(seconds=181))
    blob('processing')
    blob('failed', attempts=4)
    failed = MediaPreparationCleanup.objects.create(
        blob=blob('purging'), status='failed', attempts=99,
        next_attempt_at=now - timedelta(seconds=121), encrypted_paths='SYNTHETIC_PRIVATE_PATHS')
    MediaPreparationCleanup.objects.create(blob=blob('ready'), next_attempt_at=now + timedelta(seconds=1))
    MediaPreparationCleanup.objects.create(blob=blob('ready'), status='retained',
                                            next_attempt_at=now - timedelta(seconds=300))
    result = snapshots.collect_snapshot()
    media = result['media']
    assert {key: value['count'] for key, value in media['processing'].items()} == {
        'queued': 1, 'failed': 1, 'stale': 1, 'missing_start': 1}
    group = media['physical_jobs']['MediaPreparationCleanup']
    assert {key: value['count'] for key, value in group.items()} == {
        'due': 1, 'scheduled': 1, 'failed': 1, 'retained': 1, 'retained_due': 1}
    assert group['due']['oldest_age_seconds'] == 121
    assert 'exhausted' not in group and failed.attempts == 99
    assert 'SYNTHETIC_PRIVATE' not in json.dumps(result)
    assert 'physical_object_absence' in result['not_measured']
    Blob.objects.filter(pk=stale.pk).update(started_at=now - timedelta(seconds=180))
    assert snapshots.collect_snapshot()['media']['processing']['stale']['count'] == 0


def test_inherited_transaction_rejected_without_changing_it():
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SHOW transaction_read_only')
            before = cursor.fetchone()
        with pytest.raises(snapshots.SnapshotUnavailable):
            snapshots.collect_snapshot()
        with connection.cursor() as cursor:
            cursor.execute('SHOW transaction_read_only')
            assert cursor.fetchone() == before
            cursor.execute('SELECT 1')
            assert cursor.fetchone() == (1,)


def test_database_failure_is_sanitized_and_command_never_writes_partial_json():
    def fail(execute, sql, params, many, context):
        if sql.startswith('SELECT'):
            raise DatabaseError('PRIVATE_DATABASE_DETAIL')
        return execute(sql, params, many, context)
    output = StringIO()
    with connection.execute_wrapper(fail):
        with pytest.raises(CommandError) as error:
            call_command('operational_snapshot', stdout=output)
    assert str(error.value) == 'Operational snapshot database read failed'
    assert output.getvalue() == ''
    assert connection.get_autocommit() and not connection.in_atomic_block


def test_expiry_registry_covers_simple_periodic_safety_purges():
    tree = ast.parse(inspect.getsource(tasks))
    actual = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef) or not node.name.startswith('purge_expired_'):
            continue
        # Account-confirmation delivery has its own predicate, explicitly excluded.
        names = [alias.name for stmt in node.body if isinstance(stmt, ast.ImportFrom)
                 and stmt.module == 'models' for alias in stmt.names]
        if names:
            assert len(names) == 1
            actual[names[0]] = node.name
    actual['RightsExport'] = 'purge_expired_exports'  # module-level imports
    assert dict(snapshots.EXPIRING_MODELS) == actual


def test_export_leases_and_expiry_boundary_use_real_durable_rows(request, settings, monkeypatch):
    case, author, row, decision, *_ = prepared(request, settings, monkeypatch, account_only=True)
    job = enqueue(case, author, row, decision)
    now = timezone.now()
    monkeypatch.setattr(snapshots.timezone, 'now', lambda: now)
    model = type(job)
    for state, available, lease, expected in [
        ('queued', now, None, {'available_queued': 1}),
        ('queued', now + timedelta(seconds=1), None, {'scheduled': 1}),
        ('running', now, now + timedelta(seconds=1), {'running': 1}),
        ('running', now, now, {'running': 1, 'expired_lease': 1}),
        ('running', now, None, {'running': 1, 'missing_lease': 1}),
        ('failed', now, None, {'failed': 1}),
    ]:
        model.objects.filter(pk=job.pk).update(state=state, available_at=available, lease_until=lease)
        actual = snapshots.collect_snapshot()['export_jobs']
        assert {key: value['count'] for key, value in actual.items()} == {
            key: expected.get(key, 0) for key in actual
        }
        job.refresh_from_db()
        assert job.state == state and job.lease_until == lease
    model_name = type(row).__name__
    assert model_name == 'RightsPortabilitySelection'
    type(row).objects.filter(pk=row.pk).update(expires_at=now + timedelta(seconds=1))
    assert snapshots.collect_snapshot()['expired_temporaries'][model_name]['count'] == 0
    type(row).objects.filter(pk=row.pk).update(expires_at=now)
    assert snapshots.collect_snapshot()['expired_temporaries'][model_name]['count'] == 1
    type(row).objects.filter(pk=row.pk).update(purged_at=now)
    assert snapshots.collect_snapshot()['expired_temporaries'][model_name]['count'] == 0
