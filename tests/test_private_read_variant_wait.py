"""Eight native variant regressions; counts cover only the declared target ciphertext.

A replay can process authorized evidence before reaching its final row lock.
These cases make no HTTP transport or universal serialization claim.
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
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, connection, connections, transaction
from test_operational_recovery_authority_wait import _snapshot
from test_private_read_authority_wait import _prepare as _prepare_field
from test_private_read_authority_wait import _queries as _domain_queries
from test_private_read_authority_wait import _state
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_response_draft import operator
from test_rights_verification import read as read_case

from apps.core.models import User
from apps.safety import rights_access_field_decision as field_service
from apps.safety import rights_access_field_read as read_service
from apps.safety.models import RightsAccessFieldDecision, RightsAction

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


def _queries(actor, key=None):
    queries = _domain_queries(actor, key)
    if key is not None:
        queries['safety.RightsAccessFieldDecision'] = (
            RightsAccessFieldDecision.objects.exclude(action__key=key)
        )
    return queries


def _prepare(request, settings, monkeypatch, variant):
    case, reviewer, decision, _, _, _, _, _, _ = _prepare_field(
        request, settings, monkeypatch, 'field',
    )
    # Obtain validated original preparation through the independent public service.
    inspected, body, inspection = field_service.inspect_decision(
        reviewer, case.pk, case.version, decision.pk, uuid4(), REASON,
    )
    assert inspected.pk == decision.pk
    data = body['preparation']
    expected_value = body['value']
    author = User.objects.get(pk=decision.action.actor_id)
    assert author.pk != reviewer.pk
    read_case(operator(author), case)
    assert author.has_perm('safety.respond_rights_request')
    replay_key = None
    if variant == 'consume_approved_decision':
        approved = field_service.review(
            reviewer, case.pk, case.version, decision.pk, inspection.pk,
            uuid4(), REASON, 'approved',
        )
        assert approved.pk == decision.pk and approved.outcome == 'approved'
        decision.refresh_from_db()

        def invoke(actor, key):
            row, result, action = field_service.consume(
                actor, case.pk, case.version, case.response_version,
                decision.pk, key, REASON,
            )
            content_matches = result['value'] == expected_value
            assert content_matches
            assert row.pk == decision.pk and row.outcome == 'approved' and action.key == key
            return row.pk

        held = decision
        module, attribute, ciphertext = field_service, 'checked_body', decision.encrypted_body
        operation = 'access_field_use'
    elif variant == 'field_read_inventory':
        held = decision.inventory
        module, attribute = read_service, 'checked_body'
        ciphertext = held.action.encrypted_reason

        def invoke(actor, key):
            result, action = read_service.read(
                actor, case.pk, case.version, case.response_version, held.pk,
                data['model'], data['reference'], data['field'], key, REASON,
            )
            content_matches = result['value'] == expected_value
            assert content_matches
            assert result['inventory'] == held.pk and action.key == key
            return action.pk

        operation = 'access_field_read'
    else:
        def invoke(actor, key):
            row, result = field_service.propose(
                actor, case.pk, data['version'], data['responses'], decision.inventory_id,
                decision.read_action_id, data['model'], data['reference'], data['field'],
                key, data['reason'], data['outcome'], data['redacted'],
            )
            content_matches = result['value'] == expected_value
            assert content_matches
            assert row.action.key == key and row.inventory_id == decision.inventory_id
            if variant == 'propose_replay_decision':
                assert row.pk == decision.pk
            else:
                assert row.pk != decision.pk
            return row.pk

        module, attribute = field_service, 'checked_body'
        if variant == 'propose_inventory':
            held = decision.inventory
            ciphertext = decision.read_action.encrypted_reason
        else:
            held = decision
            ciphertext = decision.encrypted_body
            replay_key = decision.action.key
        operation = 'access_field_decide'
    # Ciphertexts and expected values remain local closure state, never properties.
    author = User.objects.get(pk=author.pk)
    return (case, author, held, module, attribute, ciphertext,
            'safety.respond_rights_request', operation, invoke, replay_key, variant)


def _exercise(prepared, change, monkeypatch, observed):
    (case, operator_user, row, module, attribute, ciphertext, permission_name,
     operation, invoke, replay_key, variant) = prepared
    permission = Permission.objects.get(
        content_type__app_label='safety', codename=permission_name.split('.')[1],
    )
    assert operator_user.user_permissions.filter(pk=permission.pk).exists()
    key = replay_key or uuid4()
    before = _snapshot(_queries(operator_user))
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
            if 'FOR UPDATE' in text and target in text and not target_statement.is_set():
                raw = context['connection'].connection
                runtime.update(pid=raw.info.backend_pid, raw=raw)
                observed['statement_seconds'] = time.monotonic() - observed['_started']
                target_statement.set()
            return execute(sql, params, many, context)

        try:
            actor = User.objects.get(pk=operator_user.pk)
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
                    operator_user.user_permissions.remove(permission)
                    observed['permission_revoked'] = not User.objects.get(pk=operator_user.pk).has_perm(permission_name)
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
        after = _snapshot(_queries(operator_user))
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
            assert RightsAction.objects.filter(key=key, operation=operation, actor=operator_user).count() == 1
            if replay_key is not None:
                assert after == before
            else:
                assert _snapshot(_queries(operator_user, key)) == before
                expected_additions = {'safety.RightsAction': 1}
                if variant == 'propose_inventory':
                    expected_additions['safety.RightsAccessFieldDecision'] = 1
                    assert RightsAccessFieldDecision.objects.filter(action__key=key).count() == 1
                for label, table in after['tables'].items():
                    assert table['count'] == before['tables'][label]['count'] + expected_additions.get(label, 0)
    finally:
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed['thread_finished'] = future is None or future.done()
        observed['domain_after'] = _snapshot(_queries(operator_user))
        observed['minimal_after'] = _state(case)
    assert observed['thread_finished'] and observed['connections_closed'] and observed['holder_released']


@pytest.mark.parametrize('variant', [
    'propose_inventory', 'propose_replay_decision',
    'consume_approved_decision', 'field_read_inventory',
])
@pytest.mark.parametrize('change', ['valid', 'permission'])
def test_native_private_read_variant_after_owned_evidence_wait(
    request, settings, monkeypatch, record_property, variant, change,
):
    observed = {'label': variant + ':' + change, 'status': 'not_started',
                'actual_wait': False, 'blocker_pids': [], 'permission_revoked': False,
                'target_decrypt_calls': 0, 'target_decrypt_successful_returns': 0,
                'thread_finished': True, 'connections_closed': True, 'holder_released': True,
                'counter_scope': 'Declared target ciphertext only; earlier authorized processing may occur.',
                '_started': time.monotonic()}
    try:
        _owned_serial(request, settings)
        prepared = _prepare(request, settings, monkeypatch, variant)
        _exercise(prepared, change, monkeypatch, observed)
    finally:
        if sys.exc_info()[0] is not None:
            observed['failure_type'] = sys.exc_info()[0].__name__
        observed['elapsed_seconds_including_wait_and_cleanup'] = time.monotonic() - observed.pop('_started')
        record_property('private_read_variant_wait', json.dumps(observed, allow_nan=False, sort_keys=True))
