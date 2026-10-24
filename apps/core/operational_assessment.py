"""Local attention policy over durable work and observed windows; never all-clear."""
import inspect
import math

from django.conf import settings
from django.utils import timezone

from .operational_snapshot import EXPIRING_MODELS

SAMPLE_SECONDS = 60
SNAPSHOT_WARNING_SECONDS = 1.0


class AssessmentUnavailable(Exception):
    """Fixed diagnostic for inconsistent internal observations."""


def _number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Invalid numeric observation')
    return value


def _count(value):
    if type(value) is not int or value < 0:
        raise ValueError('Invalid count')
    return value


def _cadence(task):
    entries = [entry for entry in settings.CELERY_BEAT_SCHEDULE.values() if entry.get('task') == task]
    if len(entries) != 1 or entries[0].get('args') or entries[0].get('kwargs'):
        return None
    value = entries[0].get('schedule')
    return float(value) if type(value) in (int, float) and math.isfinite(value) and 0 < value <= 86400 else None


def assess(snapshot, window=None, collection_seconds=None):
    try:
        return _assess(snapshot, window, collection_seconds)
    except (KeyError, TypeError, ValueError, AttributeError):
        raise AssessmentUnavailable('Operational observations are inconsistent') from None


def _assess(snapshot, window, collection_seconds):
    from apps.listings.tasks import refresh_publication_state

    findings = []

    def add(code, severity, scope, response, count=None, age=None, threshold=None):
        findings.append({'code': code, 'severity': severity, 'scope': scope, 'response': response,
                         'count': count, 'age_seconds': age, 'threshold_seconds': threshold})

    def count_issue(metric, code, scope, response, severity='error'):
        value = _count(metric['count'])
        if value:
            add(code, severity, scope, response, count=value)

    def lag(metric, code, scope, threshold, response, age_key='oldest_age_seconds'):
        value = _count(metric['count'])
        if threshold is None:
            add('schedule_policy_unknown', 'warning', scope, 'inspect_schedule')
        if value:
            age = metric.get(age_key)
            if age is None:
                add('metric_age_unknown', 'warning', scope, 'inspect_observation', count=value)
            elif threshold is not None and _number(age) >= threshold:
                add(code, 'warning', scope, response, value, age, threshold)

    if collection_seconds is not None and _number(collection_seconds) >= SNAPSHOT_WARNING_SECONDS:
        add('snapshot_collection_slow', 'warning', 'monitor', 'inspect_sampler_before_increasing_frequency',
            age=collection_seconds, threshold=SNAPSHOT_WARNING_SECONDS)

    publication_interval = _cadence('apps.listings.tasks.refresh_publication_state')
    loop_seconds = inspect.signature(refresh_publication_state.run).parameters['seconds'].default
    publication_threshold = (2 * publication_interval + _number(loop_seconds)
                             if publication_interval is not None else None)
    notice_interval = _cadence('apps.safety.tasks.deliver_safety_notices')
    notice_threshold = 2 * notice_interval if notice_interval is not None else None
    purge_thresholds = {}
    lag(snapshot['publication'], 'publication_backlog_old', 'publication', publication_threshold,
        'inspect_worker_then_reconcile_publication')
    pending = 0
    for name in ('ReportNotice', 'ComplaintNotice', 'RightsNotice'):
        group = snapshot['notices'][name]
        pending += sum(_count(group[state]['count']) for state in ('due', 'scheduled', 'exhausted', 'failed'))
        lag(group['due'], 'notice_due_wait_old', name, notice_threshold,
            'inspect_outbox_worker_and_backend', age_key='oldest_due_wait_seconds')
        for state in ('failed', 'exhausted'):
            count_issue(group[state], 'notice_' + state, name, 'inspect_outbox_without_forcing_delivery')
    if snapshot['notice_processor'] == 'disabled':
        add('notice_processor_disabled', 'error' if pending else 'info', 'notices',
            'keep_simulator_disabled_in_production', count=pending)
    elif snapshot['notice_processor'] != 'simulator':
        raise ValueError('Unknown processor')
    jobs = snapshot['export_jobs']
    for state in ('failed', 'missing_lease', 'expired_lease'):
        count_issue(jobs[state], 'export_' + state, 'exports', 'inspect_export_authority_and_lease',
                    'warning' if state == 'expired_lease' else 'error')
    for name, task in EXPIRING_MODELS:
        interval = _cadence('apps.safety.tasks.' + task)
        threshold = 2 * interval if interval is not None else None
        purge_thresholds[name] = threshold
        lag(snapshot['expired_temporaries'][name], 'temporary_purge_late', name, threshold,
            'inspect_purge_and_physical_storage_separately')
    final_interval = _cadence('apps.safety.tasks.purge_expired_access_response_drafts')
    final_threshold = 86400 + 2 * final_interval if final_interval is not None else None
    lag(snapshot['unissued_final_drafts'], 'unissued_final_draft_purge_late', 'final_drafts',
        final_threshold,
        'inspect_purge_and_physical_storage_separately')
    confirmation_interval = _cadence('apps.safety.tasks.purge_expired_account_confirmation_delivery')
    confirmation_threshold = 2 * confirmation_interval if confirmation_interval is not None else None
    lag(snapshot['expired_account_confirmation_delivery'], 'account_confirmation_payload_purge_late',
        'account_confirmation', confirmation_threshold, 'inspect_confirmation_delivery_retention')

    delivery_interval = _cadence('apps.safety.rights_object_delivery.purge_object_deliveries')
    delivery_threshold = 2 * delivery_interval if delivery_interval is not None else None
    lag(snapshot['private_delivery_cache']['expired'], 'private_delivery_cache_purge_late',
        'private_delivery_cache', delivery_threshold, 'inspect_delivery_cache_cleanup')
    count_issue(snapshot['private_delivery_cache']['invalidated'], 'private_delivery_cache_invalidated',
                'private_delivery_cache', 'inspect_delivery_cache_cleanup', 'warning')

    objects = snapshot['object_storage']
    if (type(objects['enabled']) is not bool or type(objects['recovery_mode']) is not bool
            or objects['orphan_inventory'] != 'unmeasured'):
        raise ValueError('Unknown object inventory state')
    if objects['enabled']:
        add('object_orphan_inventory_unmeasured', 'warning', 'object_storage',
            'inspect_object_inventory_in_authorized_storage')
        if objects['recovery_mode']:
            add('object_orphan_cleanup_suspended', 'info', 'object_storage',
                'keep_recovery_isolation_until_reconciled')

    media = snapshot['media']
    recovery_interval = _cadence('apps.mediafiles.tasks.recover_media_jobs')
    lag(media['processing']['queued'], 'media_processing_queue_old', 'media',
        2 * recovery_interval if recovery_interval is not None else None, 'inspect_media_processing')
    for state, code, severity in (('failed', 'media_processing_failed', 'error'),
                                   ('missing_start', 'media_processing_start_unknown', 'error'),
                                   ('stale', 'media_processing_stale', 'warning')):
        count_issue(media['processing'][state], code, 'media', 'inspect_media_processing', severity)
    cleanup_interval = _cadence('apps.mediafiles.tasks.cleanup_prepared_media')
    media_thresholds = {'processing': 2 * recovery_interval if recovery_interval is not None else None}
    lag(media['preparation_candidates'], 'media_preparation_review_old', 'media_preparations',
        2 * cleanup_interval if cleanup_interval is not None else None,
        'inspect_retention_before_physical_cleanup')
    for name, task in (('MediaErasure', 'erase_media_files'), ('MediaPreparationCleanup', 'cleanup_prepared_media')):
        group = media['physical_jobs'][name]
        interval = _cadence('apps.mediafiles.tasks.' + task)
        media_thresholds[name] = 2 * interval if interval is not None else None
        lag(group['due'], 'media_physical_wait_old', name, media_thresholds[name],
            'inspect_physical_media_job_without_forcing_delete')
        count_issue(group['failed'], 'media_physical_failure', name,
                    'inspect_physical_media_job_without_forcing_delete')
        if name == 'MediaErasure':
            count_issue(group['exhausted'], 'media_physical_exhausted', name,
                        'inspect_physical_media_job_without_forcing_delete')
        else:
            count_issue(group['retained'], 'media_retained_protected', name,
                        'inspect_retention_before_physical_cleanup', severity='info')
            lag(group['retained_due'], 'media_retention_review_late', name, media_thresholds[name],
                'inspect_retention_before_physical_cleanup')

    if window is None:
        add('event_window_missing', 'warning', 'events', 'inspect_receiver_and_collect_new_window')
    else:
        counts = window['counts']
        for metric, code, severity, response in (
            ('malformed_or_unrecognized', 'event_input_unrecognized', 'warning', 'inspect_receiver_schema'),
            ('transport_gap_markers_observed', 'event_transport_loss_observed', 'warning', 'inspect_sink_and_mark_window_incomplete'),
            ('publication_unclassified_observed', 'event_route_unknown', 'warning', 'inspect_receiver_schema'),
            ('http_5xx_observed', 'http_5xx_observed', 'error', 'inspect_application_errors'),
            ('fallback_observed', 'fallback_observed', 'info', 'inspect_fallback_reasons'),
        ):
            value = _count(counts[metric])
            if value:
                add(code, severity, 'events', response, count=value)
        for reason in ('state_dirty_over_limit', 'state_unknown_over_limit'):
            value = _count(window['publication_reasons_observed'].get(reason, 0))
            if value:
                add('publication_fallback_limit_observed', 'warning', 'publication',
                    'inspect_worker_then_reconcile_publication', count=value)
        for outcome, severity in (('failed', 'error'), ('retry', 'warning'), ('ignored', 'info')):
            value = sum(_count(row.get(outcome, 0)) for row in window['task_outcomes_observed'].values())
            if value:
                add('task_' + outcome + '_observed', severity, 'tasks', 'inspect_task_without_blind_replay', count=value)
        for metric, severity in (('failed', 'error'), ('retry', 'warning')):
            value = _count(window['delivery_known_totals_observed'][metric])
            if value:
                add('delivery_' + metric + '_observed', severity, 'notices', 'inspect_outbox_worker_and_backend', count=value)
        unknown = sum(_count(value) for value in window['delivery_unknown_samples'].values())
        if unknown:
            add('delivery_counts_unknown', 'warning', 'events', 'inspect_receiver_schema', count=unknown)
        disabled = _count(window['processor_disabled_samples']['true'])
        if disabled:
            add('notice_processor_disabled_observed', 'error' if pending else 'info', 'notices',
                'inspect_outbox_worker_and_backend', count=disabled)
        unknown_processor = _count(window['processor_disabled_samples']['unknown'])
        if unknown_processor:
            add('notice_processor_state_unknown_observed', 'warning', 'events',
                'inspect_receiver_schema', count=unknown_processor)
        now = int(timezone.now().timestamp())
        end = _count(window['end_exclusive'])
        if now - end > SAMPLE_SECONDS or end > now + 1:
            add('event_window_not_current', 'warning', 'events', 'collect_new_window')
    status = ('action_required' if any(row['severity'] == 'error' for row in findings)
              else 'attention_required' if any(row['severity'] == 'warning' for row in findings)
              else 'unknown')
    return {'schema_version': 1, 'policy_version': 'local-attention-v1', 'status': status,
            'health': 'unknown', 'coverage': 'unverified', 'findings': findings,
            'snapshot_collection_seconds': collection_seconds,
            'policy': {'sampling_interval_seconds': SAMPLE_SECONDS,
                       'snapshot_warning_duration_seconds': SNAPSHOT_WARNING_SECONDS,
                       'publication_warning_age_seconds': publication_threshold,
                       'notice_due_warning_age_seconds': notice_threshold,
                       'unissued_final_draft_warning_age_seconds': final_threshold,
                       'account_confirmation_warning_age_seconds': confirmation_threshold,
                       'private_delivery_cache_warning_age_seconds': delivery_threshold,
                       'temporary_warning_age_seconds': purge_thresholds,
                       'media_warning_age_seconds': media_thresholds,
                       'kind': 'local_attention_not_contractual_slo'},
            'limitations': ['Manual administrative evaluation, no automatic scheduler or alert delivery',
                           'Absence of findings does not establish health or complete coverage',
                           'No broker/worker liveness or physical purge proof',
                           'No automatic replays, authority changes or external provider calls']}
