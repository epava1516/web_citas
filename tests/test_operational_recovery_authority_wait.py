"""Two explicit real PostgreSQL HTTP waits; stale recovery authority must be denied."""

import hashlib
import json
import os
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from threading import Event

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connection, connections, transaction
from django.test import Client
from test_media_operations import REASON, exhausted
from test_notice_operations import data, failed_report
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.mediafiles.models import Blob, MediaErasure, MediaErasureRecovery
from apps.safety.models import NoticeRecovery, Report, ReportNotice, RightsAction, RightsRequest
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip('Explicit serial owned PostgreSQL recovery wait diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'].startswith('test_')
    _owned_database()


def _snapshot(queries):
    # Full scalar row material remains local. Only digests/counts leave this helper.
    snapshot = {}
    for label, query in queries.items():
        fields = [field.attname for field in query.model._meta.concrete_fields]
        rows = list(query.order_by('pk').values(*fields))
        canonical = json.dumps(rows, sort_keys=True, separators=(',', ':'), default=str)
        snapshot[label] = {'count': len(rows), 'sha256': hashlib.sha256(canonical.encode()).hexdigest()}
    canonical = json.dumps(snapshot, sort_keys=True, separators=(',', ':'))
    return {'tables': snapshot, 'sha256': hashlib.sha256(canonical.encode()).hexdigest()}


def _observe_wait_and_revoke(
    *, actor, client, route, payload, permission_name, held_model, held_pk,
    queries, minimal_state, case_label, record_property
):
    permission = Permission.objects.get(
        content_type__app_label=permission_name.split('.')[0],
        codename=permission_name.split('.')[1],
    )
    fresh = User.objects.get(pk=actor.pk)
    assert fresh.mfa_enabled and fresh.is_active and fresh.has_perm(permission_name)
    assert actor.user_permissions.filter(pk=permission.pk).exists()
    # Session writes and auth setup complete before any business lock is acquired.
    session = client.session
    session['mfa_version'] = actor.mfa_version
    session['account_version'] = actor.session_version
    session.save()
    before = _snapshot(queries)
    before_state = minimal_state()
    observed = {'case': case_label, 'route': route, 'initial_permission': True,
                'initial_mfa': True, 'actual_wait': False, 'permission_revoked': False,
                'status': None, 'thread_connections_closed': False,
                'domain_before': before, 'minimal_before': before_state,
                'timing_scope': 'Induced PostgreSQL wait diagnostic, not application latency or performance comparison.'}
    target_statement = Event()
    runtime = {}
    pool = ThreadPoolExecutor(max_workers=1)
    future = None
    started = time.monotonic()

    def worker():
        close_old_connections()

        def observe(execute, sql, params, many, context):
            text = str(sql).upper()
            target = 'FROM "' + held_model._meta.db_table.upper() + '"'
            if 'FOR UPDATE' in text and target in text:
                effective = context['connection'].connection
                runtime['pid'] = effective.info.backend_pid
                runtime['raw_connection'] = effective
                runtime['statement_monotonic'] = time.monotonic()
                target_statement.set()
            return execute(sql, params, many, context)

        try:
            with connection.execute_wrapper(observe):
                response = client.post(route, payload)
                observed['status'] = response.status_code
                return response.status_code
        except Exception as exc:
            observed['request_exception_type'] = type(exc).__name__
            raise
        finally:
            try:
                connections.close_all()
            finally:
                observed['thread_connections_closed'] = all(
                    alias.connection is None for alias in connections.all()
                )
                observed['request_elapsed_seconds_including_wait'] = time.monotonic() - started

    try:
        try:
            with transaction.atomic():
                held_model.objects.select_for_update().get(pk=held_pk)
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    holder_pid = cursor.fetchone()[0]
                future = pool.submit(worker)
                deadline = time.monotonic() + 15
                while True:
                    assert not future.done(), 'Request finished before confirmed PostgreSQL wait'
                    if target_statement.is_set():
                        pid = runtime['pid']
                        assert pid != holder_pid
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT pg_stat_clear_snapshot()')
                            cursor.execute(
                                'SELECT wait_event_type, pg_blocking_pids(pid) '
                                'FROM pg_stat_activity WHERE pid=%s', [pid],
                            )
                            waiting = cursor.fetchone()
                        if waiting and waiting[0] == 'Lock' and holder_pid in waiting[1]:
                            observed['actual_wait'] = True
                            observed['effective_request_backend_pid'] = pid
                            observed['holder_backend_pid'] = holder_pid
                            observed['lock_observed_seconds'] = time.monotonic() - started
                            break
                    assert time.monotonic() < deadline, 'Real PostgreSQL lock wait not observed in15s'
                    time.sleep(.02)
                # This authority change commits together with release of the owned row lock.
                actor.user_permissions.remove(permission)
                observed['permission_revoked'] = (
                    not actor.user_permissions.filter(pk=permission.pk).exists()
                    and not User.objects.get(pk=actor.pk).has_perm(permission_name)
                )
                assert observed['permission_revoked']
        finally:
            # Leaving atomic releases the owned lock on every path, including observation failure.
            observed['holder_transaction_released'] = not connection.in_atomic_block
            if future is not None:
                try:
                    observed['status'] = future.result(timeout=45)
                except FutureTimeoutError:
                    observed['request_timeout'] = True
                    # Cleanup only: cancel the actual owned connection captured in this request.
                    # Never changes a successful/failed business outcome into a PASS.
                    raw = runtime.get('raw_connection')
                    if raw is not None and not raw.closed and raw.info.backend_pid == runtime.get('pid'):
                        raw.cancel()
                        observed['owned_request_cancelled_for_cleanup'] = True
                    try:
                        future.result(timeout=5)
                    except Exception as exc:
                        observed['timeout_cleanup_exception_type'] = type(exc).__name__
                    raise
        assert observed['actual_wait'] and observed['permission_revoked']
        assert observed['status'] == 403
        assert _snapshot(queries) == before
        assert minimal_state() == before_state
    finally:
        if sys.exc_info()[0] is not None:
            observed['failure_type'] = sys.exc_info()[0].__name__
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed['thread_finished'] = future is None or future.done()
        observed['elapsed_seconds_including_wait_and_cleanup'] = time.monotonic() - started
        try:
            observed['domain_after'] = _snapshot(queries)
            observed['minimal_after'] = minimal_state()
            observed['domain_unchanged'] = observed['domain_after'] == before
        except Exception as exc:
            observed['final_snapshot_exception_type'] = type(exc).__name__
        record_property('operational_recovery_authority_wait', json.dumps(
            observed, allow_nan=False, sort_keys=True,
        ))
    assert observed['thread_finished'] and observed['thread_connections_closed']


def test_notice_recovery_denies_permission_revoked_during_actual_report_wait(
    request, settings, record_property
):
    _owned_serial(request, settings)
    notice, actor, client = failed_report(request)
    assert celery_app.conf.task_always_eager
    assert notice.status == 'failed' and notice.attempts == 5
    assert actor.mfa_enabled and User.objects.get(pk=actor.pk).has_perm('safety.review_report')
    assert notice.report.actor_id != actor.pk
    route = f'/en/moderation/notices/report/{notice.pk}/'
    queries = {
        'report': Report.objects.filter(pk=notice.report_id),
        'notice': ReportNotice.objects.filter(pk=notice.pk),
        'notice_recovery': NoticeRecovery.objects.all(),
        'rights_action': RightsAction.objects.all(),
    }

    def minimal_state():
        return ReportNotice.objects.filter(pk=notice.pk).values(
            'status', 'attempts', 'recovery_version', 'error_code',
        ).get()

    _observe_wait_and_revoke(
        actor=actor, client=client, route=route, payload=data(notice.recovery_version),
        permission_name='safety.manage_notice_delivery', held_model=Report,
        held_pk=notice.report_id, queries=queries, minimal_state=minimal_state,
        case_label='report_notice_recovery', record_property=record_property,
    )


def test_media_recovery_denies_permission_revoked_during_actual_blob_wait(
    request, settings, monkeypatch, record_property
):
    _owned_serial(request, settings)
    case, actor, person, job = exhausted(request, settings, monkeypatch)
    job.refresh_from_db()  # The native fixture updates this row via QuerySet.update.
    assert celery_app.conf.task_always_eager
    assert job.status == 'failed' and job.attempts == 5 and job.blob.status == 'erasing'
    assert job.encrypted_paths and actor.mfa_enabled
    assert User.objects.get(pk=actor.pk).has_perm('safety.review_rights_request')
    assert actor.pk not in (case.actor_id, person.subject_id, person.agency.owner_id)
    client = Client()
    client.force_login(actor)
    route = f'/en/moderation/rights/{case.pk}/media-jobs/{job.pk}/'
    queries = {
        'case': RightsRequest.objects.filter(pk=case.pk),
        'blob': Blob.objects.filter(pk=job.blob_id),
        'job': MediaErasure.objects.filter(pk=job.pk),
        'execution': type(job.execution).objects.filter(pk=job.execution_id),
        'media_recovery': MediaErasureRecovery.objects.all(),
        'rights_action': RightsAction.objects.all(),
    }

    def minimal_state():
        return MediaErasure.objects.filter(pk=job.pk).values(
            'status', 'attempts', 'recovery_version', 'error_code',
        ).get()

    _observe_wait_and_revoke(
        actor=actor, client=client, route=route,
        payload={'key': uuid.uuid4(), 'version': job.recovery_version, 'reason': REASON},
        permission_name='mediafiles.manage_media_erasure', held_model=Blob,
        held_pk=job.blob_id, queries=queries, minimal_state=minimal_state,
        case_label='media_erasure_recovery', record_property=record_property,
    )
