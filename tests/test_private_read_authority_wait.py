"""Six opt-in native service diagnostics: private evidence after a real PG wait.

Counters observe processing, not HTTP disclosure. No application guards are replaced.
"""

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, connection, connections, transaction
from test_operational_recovery_authority_wait import _snapshot
from test_privacy_release import fresh
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_access_response_draft import TEXT
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read as read_case

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.safety import rights_access_field_decision as field_service
from apps.safety import rights_access_response_review as draft_service
from apps.safety import rights_information_review as information_service
from apps.safety.models import RightsAction, RightsCopyInformationRead, RightsRequest
from apps.safety.rights_access_field_read import read as read_field
from apps.safety.rights_access_response_draft import prepare
from apps.safety.rights_access_scope_store import inspect as inspect_scope
from apps.safety.rights_exports import generate, preview

pytestmark = pytest.mark.django_db(transaction=True)
REASON = 'Independently inspect synthetic private evidence after an owned row wait'


def _owned_serial(request, settings):
    explicit = any(
        Path(str(arg).split('::')[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip('Explicit serial owned PostgreSQL private read diagnostic only')
    assert not os.environ.get('PYTEST_XDIST_WORKER')
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == 'postgresql'
    assert connection.settings_dict['NAME'].startswith('test_')
    _owned_database()


def _grant(actor, codename):
    actor.user_permissions.add(Permission.objects.get(
        content_type__app_label='safety', codename=codename,
    ))
    return User.objects.get(pk=actor.pk)


def _prepare(request, settings, monkeypatch, family):
    case, author, staff, _, _, person, _, information, decision, _, value = (
        approved_information(request, settings, monkeypatch, False)
    )
    reviewer = User.objects.get(username='fixture-v1-visitor')
    assert person is not None and reviewer.pk != author.pk
    if family == 'information':
        permission = 'safety.review_copy_information'
        row, module, attribute = information, information_service, 'unseal'
        ciphertext = row.encrypted_information

        def invoke(actor, key):
            result, body = module.record(
                actor, case.pk, row.pk, key, case.version, 'inspect', REASON,
            )
            assert result.information_id == row.pk
            matches_expected = body['access'] == value['access']
            assert matches_expected
            return result.pk

        operation = 'copy_info_inspect'
    else:
        author = _grant(author, 'respond_rights_request')
        reviewer = _grant(reviewer, 'respond_rights_request')
        permission = 'safety.respond_rights_request'
        if family == 'field':
            inventory, manifest = inspect_scope(
                author, case.pk, case.version, case.response_version, uuid4(), REASON,
            )
            reference = next(
                entry for entry in manifest['entries'] if entry['model'] == 'core.User'
            )['records'][0]['reference']
            _, reading = read_field(
                author, case.pk, case.version, case.response_version, inventory.pk,
                'core.User', reference, 'email', uuid4(), REASON,
            )
            row, _ = field_service.propose(
                author, case.pk, case.version, case.response_version, inventory.pk,
                reading.pk, 'core.User', reference, 'email', uuid4(), REASON, 'included',
            )
            module, attribute, ciphertext = field_service, 'checked_body', row.encrypted_body

            def invoke(actor, key):
                result, body, action = module.inspect_decision(
                    actor, case.pk, case.version, row.pk, key, REASON,
                )
                assert result.pk == row.pk and action.key == key
                matches_expected = (body['original'] == person.subject.email
                                    and body['value'] == person.subject.email)
                assert matches_expected
                return result.pk

            operation = 'access_decision_read'
        else:
            export = generate(
                author, case.pk, uuid4(), case.version, REASON,
                preview(author, case.pk, case.version, REASON),
                information_review_id=decision.pk,
            )
            reviewer = _grant(reviewer, 'verify_rights_scope')
            fresh(case, author, staff, reviewer, operator(reviewer))
            row = prepare(
                author, case.pk, case.version, case.response_version, export.pk,
                uuid4(), REASON, TEXT, True,
            )
            module, attribute, ciphertext = draft_service, 'checked_body', row.encrypted_response

            def invoke(actor, key):
                result, body = module.inspect(actor, case.pk, case.version, row.pk, key, REASON)
                assert result.pk == row.pk
                matches_expected = (body['text'] == TEXT and body['simulation'] is True
                                    and body['export'] == str(export.pk))
                assert matches_expected
                return result.pk

            operation = 'access_draft_read'
    read_case(operator(reviewer), case)
    reviewer = User.objects.get(pk=reviewer.pk)
    assert reviewer.has_perm(permission) and reviewer.mfa_enabled and reviewer.is_active
    return case, reviewer, row, module, attribute, ciphertext, permission, operation, invoke


def _queries(reviewer, key=None):
    queries = {'core.User': User.objects.exclude(pk=reviewer.pk),
               'core.Person': Person.objects.all(), 'listings.Listing': Listing.objects.all(),
               'listings.Revision': Revision.objects.all()}
    for model in apps.get_app_config('safety').get_models():
        if model.__name__.startswith('Rights'):
            query = model.objects.all()
            if key is not None and model is RightsAction:
                query = query.exclude(key=key)
            if key is not None and model is RightsCopyInformationRead:
                query = query.exclude(action__key=key)
            queries[model._meta.label] = query
    return queries


def _state(case):
    return RightsRequest.objects.filter(pk=case.pk).values(
        'status', 'version', 'response_version',
    ).get()


def _exercise(prepared, change, monkeypatch, observed):
    case, reviewer, row, module, attribute, ciphertext, permission_name, operation, invoke = prepared
    permission = Permission.objects.get(
        content_type__app_label='safety', codename=permission_name.split('.')[1],
    )
    assert reviewer.user_permissions.filter(pk=permission.pk).exists()
    key = uuid4()
    before = _snapshot(_queries(reviewer))
    state = _state(case)
    observed.update(domain_before=before, minimal_before=state, initial_permission=True)
    original = getattr(module, attribute)

    def observe_decryption(value):
        target = value == ciphertext
        if target:
            observed['target_decrypt_calls'] += 1
        result = original(value)
        if target:
            observed['target_decrypt_successful_returns'] += 1
        return result

    monkeypatch.setattr(module, attribute, observe_decryption)
    target_statement = Event()
    runtime = {}
    pool = ThreadPoolExecutor(max_workers=1)
    future = None

    def worker():
        close_old_connections()

        def observe_statement(execute, sql, params, many, context):
            text = str(sql).upper()
            target = 'FROM "' + row._meta.db_table.upper() + '"'
            if 'FOR UPDATE' in text and target in text:
                raw = context['connection'].connection
                runtime.update(pid=raw.info.backend_pid, raw=raw)
                observed['statement_seconds'] = time.monotonic() - observed['_started']
                target_statement.set()
            return execute(sql, params, many, context)

        try:
            actor = User.objects.get(pk=reviewer.pk)
            assert actor.has_perm(permission_name)
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '35s'")
            with connection.execute_wrapper(observe_statement):
                try:
                    result = invoke(actor, key)
                except PermissionDenied:
                    observed['status'] = 'PermissionDenied'
                    return None
                observed['status'] = 'success'
                return result
        except Exception as error:
            observed['status'] = 'unexpected:' + type(error).__name__
            raise
        finally:
            connections.close_all()
            observed['connections_closed'] = all(alias.connection is None for alias in connections.all())

    try:
        try:
            with transaction.atomic():
                type(row).objects.select_for_update().get(pk=row.pk)
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    holder = cursor.fetchone()[0]
                observed['holder_pid'] = holder
                future = pool.submit(worker)
                deadline = time.monotonic() + 15
                while True:
                    assert not future.done(), 'Service finished before observed PostgreSQL wait'
                    if target_statement.is_set():
                        assert runtime['pid'] != holder
                        with connection.cursor() as cursor:
                            cursor.execute('SELECT pg_stat_clear_snapshot()')
                            cursor.execute(
                                'SELECT wait_event_type, pg_blocking_pids(pid) '
                                'FROM pg_stat_activity WHERE pid=%s', [runtime['pid']],
                            )
                            waiting = cursor.fetchone()
                        if waiting and waiting[0] == 'Lock' and holder in waiting[1]:
                            observed.update(actual_wait=True, worker_pid=runtime['pid'],
                                            blocker_pids=list(waiting[1]))
                            break
                    assert time.monotonic() < deadline, 'Owned PostgreSQL wait absent after15s'
                    time.sleep(.02)
                if change == 'permission':
                    reviewer.user_permissions.remove(permission)
                    observed['permission_revoked'] = not User.objects.get(pk=reviewer.pk).has_perm(permission_name)
                    assert observed['permission_revoked']
        finally:
            observed['holder_released'] = not connection.in_atomic_block
            if future is not None:
                try:
                    future.result(timeout=45)
                except FutureTimeoutError:
                    observed['worker_timeout'] = True
                    raw = runtime.get('raw')
                    if raw is not None and not raw.closed and raw.info.backend_pid == runtime.get('pid'):
                        raw.cancel()
                    try:
                        future.result(timeout=5)
                    except Exception as error:
                        observed['cleanup_exception_type'] = type(error).__name__
                    raise
        after = _snapshot(_queries(reviewer))
        observed.update(domain_after=after, minimal_after=_state(case))
        assert observed['actual_wait']
        assert _state(case) == state
        if change == 'permission':
            assert observed['status'] == 'PermissionDenied'
            assert after == before
            assert observed['target_decrypt_calls'] == 0
            assert observed['target_decrypt_successful_returns'] == 0
        else:
            assert observed['status'] == 'success'
            assert observed['target_decrypt_calls'] > 0
            assert observed['target_decrypt_successful_returns'] > 0
            assert RightsAction.objects.filter(key=key, operation=operation, actor=reviewer).count() == 1
            assert _snapshot(_queries(reviewer, key)) == before
            expected_additions = {'safety.RightsAction': 1}
            if operation == 'copy_info_inspect':
                expected_additions['safety.RightsCopyInformationRead'] = 1
                assert RightsCopyInformationRead.objects.filter(action__key=key, information=row).count() == 1
            for label, table in after['tables'].items():
                assert table['count'] == before['tables'][label]['count'] + expected_additions.get(label, 0)
    finally:
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed['thread_finished'] = future is None or future.done()
        observed['domain_after'] = _snapshot(_queries(reviewer))
        observed['minimal_after'] = _state(case)
    assert observed['thread_finished'] and observed['connections_closed'] and observed['holder_released']


@pytest.mark.parametrize('family', ['field', 'information', 'draft'])
@pytest.mark.parametrize('change', ['valid', 'permission'])
def test_native_private_read_authority_after_owned_evidence_wait(
    request, settings, monkeypatch, record_property, family, change,
):
    observed = {'label': family + ':' + change, 'status': 'not_started',
                'actual_wait': False, 'blocker_pids': [], 'permission_revoked': False,
                'target_decrypt_calls': 0, 'target_decrypt_successful_returns': 0,
                'thread_finished': True, 'connections_closed': True, 'holder_released': True,
                '_started': time.monotonic()}
    try:
        _owned_serial(request, settings)
        prepared = _prepare(request, settings, monkeypatch, family)
        _exercise(prepared, change, monkeypatch, observed)
    finally:
        if sys.exc_info()[0] is not None:
            observed['failure_type'] = sys.exc_info()[0].__name__
        observed['elapsed_seconds_including_wait_and_cleanup'] = time.monotonic() - observed.pop('_started')
        record_property('private_read_authority_wait', json.dumps(observed, allow_nan=False, sort_keys=True))
