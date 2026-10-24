"""Attention policy boundaries, sanitized administrative output and PostgreSQL faults."""
import io
import json
from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import DatabaseError, connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.core.operational_assessment import AssessmentUnavailable, assess
from apps.core.operational_snapshot import collect_snapshot
from apps.core.operational_window import NOTICE_TASK, summarize_window
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def window(rows=()):
    now = int(timezone.now().timestamp())
    encoded = b''.join(json.dumps({'schema_version': 1, 'timestamp_seconds': now, **row}).encode() + b'\n'
                       for row in rows)
    return summarize_window(io.BytesIO(encoded), now - 59, now + 1)


def codes(result):
    return {row['code'] for row in result['findings']}


def test_empty_observation_never_reports_healthy_and_missing_window_is_visible():
    snapshot = collect_snapshot()
    result = assess(snapshot, window())
    assert result['status'] == 'unknown' and result['health'] == 'unknown'
    assert result['coverage'] == 'unverified'
    assert result['policy']['publication_warning_age_seconds'] == 110
    assert result['policy']['notice_due_warning_age_seconds'] == 120
    assert 'event_window_missing' in codes(assess(snapshot))


def test_lag_boundaries_and_old_creation_do_not_misclassify_newly_due_retry(settings):
    settings.SAFETY_NOTICE_BACKEND = 'simulator'
    snapshot = collect_snapshot()
    snapshot['publication'] = {'count': 1, 'oldest_age_seconds': 109.999}
    notice = snapshot['notices']['ReportNotice']
    notice['due'] = {'count': 1, 'oldest_age_seconds': 7200, 'oldest_due_wait_seconds': 1}
    notice['scheduled'] = {'count': 1, 'oldest_age_seconds': 7200}
    assert 'publication_backlog_old' not in codes(assess(snapshot, window()))
    assert 'notice_due_wait_old' not in codes(assess(snapshot, window()))
    snapshot['publication']['oldest_age_seconds'] = 110
    notice['due']['oldest_due_wait_seconds'] = 120
    result = assess(snapshot, window())
    assert {'publication_backlog_old', 'notice_due_wait_old'} <= codes(result)
    assert result['status'] == 'attention_required'
    assert 'snapshot_collection_slow' not in codes(assess(snapshot, window(), collection_seconds=.999))
    assert 'snapshot_collection_slow' in codes(assess(snapshot, window(), collection_seconds=1.0))


def test_failed_tasks_retry_delivery_and_transport_loss_are_distinct_without_payload_echo():
    rows = [
        {'event': 'task_result', 'task': 'other', 'outcome': 'failed'},
        {'event': 'task_result', 'task': NOTICE_TASK, 'outcome': 'succeeded',
         'delivery_counts': {'processed': 1, 'simulated': 0, 'retry': 1, 'failed': None},
         'processor_disabled': False},
        {'event': 'transport_gap', 'dropped_events': 7, 'write_errors': 0,
         'counter_scope': 'process_local_cumulative'},
        {'event': 'publication_read', 'route': 'fallback', 'reason': 'invalid_search', 'status_class': '2xx'},
        {'event': 'task_result', 'task': 'SYNTHETIC_PRIVATE@example.invalid', 'outcome': 'failed'},
    ]
    result = assess(collect_snapshot(), window(rows))
    assert result['status'] == 'action_required'
    assert {'task_failed_observed', 'delivery_retry_observed', 'event_transport_loss_observed',
            'delivery_counts_unknown', 'event_input_unrecognized', 'fallback_observed'} <= codes(result)
    assert 'publication_fallback_limit_observed' not in codes(result)
    assert 'SYNTHETIC_PRIVATE' not in json.dumps(result)


def test_schedule_unknown_and_stale_or_future_windows_remain_visible(settings):
    snapshot = collect_snapshot()
    settings.CELERY_BEAT_SCHEDULE = {}
    result = assess(snapshot, window())
    assert 'schedule_policy_unknown' in codes(result)
    assert result['policy']['publication_warning_age_seconds'] is None
    for offset in (-62, 2):
        observed = window()
        observed['end_exclusive'] = int(timezone.now().timestamp()) + offset
        assert 'event_window_not_current' in codes(assess(snapshot, observed))


def test_failed_jobs_purge_eligibility_and_disabled_processor_have_fixed_responses(settings):
    snapshot = collect_snapshot()
    snapshot['notice_processor'] = 'disabled'
    snapshot['notices']['RightsNotice']['failed']['count'] = 1
    snapshot['export_jobs']['missing_lease']['count'] = 1
    snapshot['expired_temporaries']['RightsExport'] = {'count': 1, 'oldest_age_seconds': 120}
    snapshot['unissued_final_drafts'] = {'count': 1, 'oldest_age_seconds': 86400 + 119}
    result = assess(snapshot, window())
    assert {'notice_failed', 'notice_processor_disabled', 'export_missing_lease', 'temporary_purge_late'} <= codes(result)
    assert 'unissued_final_draft_purge_late' not in codes(result)
    snapshot['unissued_final_drafts']['oldest_age_seconds'] += 1
    assert 'unissued_final_draft_purge_late' in codes(assess(snapshot, window()))
    schedule = deepcopy(settings.CELERY_BEAT_SCHEDULE)
    schedule['purge-expired-access-response-drafts']['schedule'] = 120
    schedule['purge-expired-private-copies']['schedule'] = 600
    settings.CELERY_BEAT_SCHEDULE = schedule
    snapshot['unissued_final_drafts']['oldest_age_seconds'] = 86400 + 239
    assert 'unissued_final_draft_purge_late' not in codes(assess(snapshot, window()))
    snapshot['unissued_final_drafts']['oldest_age_seconds'] += 1
    changed = assess(snapshot, window())
    assert changed['policy']['unissued_final_draft_warning_age_seconds'] == 86400 + 240
    assert 'unissued_final_draft_purge_late' in codes(changed)
    # Worker and sampler can disagree: an observed disabled backend must remain visible.
    current = collect_snapshot()
    current['notice_processor'] = 'simulator'
    row = {'event': 'task_result', 'task': NOTICE_TASK, 'outcome': 'succeeded',
           'delivery_counts': {'processed': 0, 'simulated': 0, 'retry': 0, 'failed': 0},
           'processor_disabled': True}
    observed = assess(current, window([row]))
    assert 'notice_processor_disabled_observed' in codes(observed)
    assert observed['status'] == 'unknown'  # Explicit disabled state with no pending work.
    current['notices']['ReportNotice']['due'].update(
        count=1, oldest_age_seconds=1, oldest_due_wait_seconds=1)
    assert assess(current, window([row]))['status'] == 'action_required'
    row['processor_disabled'] = None
    unknown = assess(current, window([row]))
    assert 'notice_processor_state_unknown_observed' in codes(unknown)
    assert unknown['status'] == 'attention_required'
    protected = collect_snapshot()
    preparation = protected['media']['physical_jobs']['MediaPreparationCleanup']
    preparation['retained']['count'] = 1
    retained = assess(protected, window())
    assert 'media_retained_protected' in codes(retained)
    assert not {'media_physical_failure', 'media_physical_wait_old'} & codes(retained)
    preparation['retained_due'] = {'count': 1, 'oldest_age_seconds': 120}
    review = assess(protected, window())
    assert 'media_retention_review_late' in codes(review)
    assert 'media_physical_failure' not in codes(review)
    preparation['failed']['count'] = 1
    preparation['due'] = {'count': 1, 'oldest_age_seconds': 120}
    failure = assess(protected, window())
    assert {'media_physical_failure', 'media_physical_wait_old'} <= codes(failure)
    assert failure['status'] == 'action_required'
    protected['expired_account_confirmation_delivery'] = {'count': 1, 'oldest_age_seconds': 119.999}
    assert 'account_confirmation_payload_purge_late' not in codes(assess(protected, window()))
    protected['expired_account_confirmation_delivery']['oldest_age_seconds'] = 120
    assert 'account_confirmation_payload_purge_late' in codes(assess(protected, window()))


def test_command_observes_real_durable_delay_read_only_and_never_echoes_paths(tmp_path):
    marker = uuid4()
    PublicationDirty.objects.create(listing_id=marker, generation=1,
                                    marked_at=timezone.now() - timedelta(minutes=5))
    path = tmp_path / 'SYNTHETIC_PRIVATE_EVENTS.jsonl'
    path.write_bytes(b'')
    now = int(timezone.now().timestamp())
    output = io.StringIO()
    with CaptureQueriesContext(connection) as queries:
        call_command('operational_assessment', input=str(path), start=now - 59, end=now + 1, stdout=output)
    result = json.loads(output.getvalue())
    assert 'publication_backlog_old' in codes(result)
    assert result['status'] == 'attention_required'
    assert all(row['sql'].startswith(('SELECT ', 'BEGIN', 'COMMIT', 'SET ')) for row in queries)
    assert PublicationDirty.objects.filter(pk=marker).exists()
    assert str(marker) not in output.getvalue() and 'SYNTHETIC_PRIVATE' not in output.getvalue()
    output = io.StringIO()
    with pytest.raises(CommandError) as error:
        call_command('operational_assessment', input=str(tmp_path / 'SYNTHETIC_PRIVATE_MISSING'),
                     start=now - 59, end=now + 1, stdout=output)
    assert output.getvalue() == '' and 'SYNTHETIC_PRIVATE' not in str(error.value)
    with pytest.raises(CommandError, match='both integer window bounds'):
        call_command('operational_assessment', input=str(path), stdout=output)


def test_database_failure_never_returns_partial_assessment():
    def fail(execute, sql, params, many, context):
        if sql.startswith('SELECT'):
            raise DatabaseError('SYNTHETIC_PRIVATE_DATABASE')
        return execute(sql, params, many, context)
    output = io.StringIO()
    with connection.execute_wrapper(fail), pytest.raises(CommandError) as error:
        call_command('operational_assessment', stdout=output)
    assert str(error.value) == 'Operational snapshot database read failed'
    assert output.getvalue() == ''


def test_inconsistent_internal_metric_is_fixed_error_without_value_echo():
    snapshot = collect_snapshot()
    snapshot['publication']['count'] = 'SYNTHETIC_PRIVATE_COUNT'
    with pytest.raises(AssessmentUnavailable) as error:
        assess(snapshot, window())
    assert str(error.value) == 'Operational observations are inconsistent'


def test_private_delivery_expiry_boundary_and_invalidation_have_distinct_responses():
    snapshot = collect_snapshot()
    expired = snapshot['private_delivery_cache']['expired']
    expired.update(count=1, oldest_age_seconds=19.999)
    assert 'private_delivery_cache_purge_late' not in codes(assess(snapshot))
    expired['oldest_age_seconds'] = 20
    assert 'private_delivery_cache_purge_late' in codes(assess(snapshot))
    expired.update(count=0, oldest_age_seconds=None)
    snapshot['private_delivery_cache']['invalidated'].update(count=1, oldest_age_seconds=0)
    result = assess(snapshot)
    assert 'private_delivery_cache_invalidated' in codes(result)
    assert 'private_delivery_cache_purge_late' not in codes(result)
    assert result['health'] == 'unknown'


def test_optional_object_inventory_never_becomes_an_absence_claim(settings, monkeypatch):
    from apps.safety.object_storage import factory
    def no_provider(*args, **kwargs):
        raise AssertionError('Snapshot must not contact object storage')
    monkeypatch.setattr(factory, 'repository', no_provider)
    for enabled, recovery in ((False, False), (True, False), (True, True)):
        settings.RIGHTS_OBJECT_STORAGE_ENABLED = enabled
        settings.RECOVERY_MODE = recovery
        snapshot = collect_snapshot()
        assert snapshot['object_storage'] == {
            'enabled': enabled, 'recovery_mode': recovery, 'orphan_inventory': 'unmeasured'}
        assert 'export_orphan_inventory' in snapshot['not_measured']
        result = assess(snapshot)
        assert ('object_orphan_inventory_unmeasured' in codes(result)) is enabled
        assert ('object_orphan_cleanup_suspended' in codes(result)) is (enabled and recovery)
        assert result['health'] == 'unknown'
