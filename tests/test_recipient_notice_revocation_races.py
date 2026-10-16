"""Recipient authority must be fresh after an observed PostgreSQL lock wait."""
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_erasure_execution import PURPOSES, REASON, plan_fixture
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read as read_case

from apps.core.models import Person, User
from apps.safety import rights_communications as communications
from apps.safety.communication_notices import acknowledge, deliver, inspect_notice
from apps.safety.erasure_execution import execute
from apps.safety.models import RightsAction, RightsRecipientNotice
from apps.safety.recipient_assessments import targets

pytestmark = pytest.mark.django_db(transaction=True)


def delivered(request, settings, monkeypatch):
    case, actor, staff, _, _, person, plan, _, _, _ = plan_fixture(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, PURPOSES, REASON, True)
    case.refresh_from_db()
    read_case(staff, case)
    reviewer = User.objects.get(username='fixture-v1-visitor')
    reviewer.mfa_enabled, reviewer.mfa_version = True, 1
    reviewer.save(update_fields=['mfa_enabled', 'mfa_version'])
    reviewer.user_permissions.add(*Permission.objects.filter(codename__in=[
        'review_rights_request', 'execute_rights_request', 'respond_rights_request',
        'review_recipient_assessment']))
    from django.test import Client
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session['mfa_version'] = reviewer.mfa_version
    session.save()
    read_case(client, case)
    common = case.pk, case.version, case.response_version
    _, source = communications.inspect_source(actor, *common, execution.pk, REASON)
    decisions = {token: {'outcome':'pending', 'reason':REASON, 'evidence':REASON}
                 for token in targets(source)}
    proposal = communications.propose(actor, *common, execution.pk, uuid4(), REASON, decisions)
    audit, _ = communications.inspect(reviewer, *common, proposal.pk, REASON)
    approval = communications.review(reviewer, *common, proposal.pk, audit.pk, uuid4(), 'approved', REASON)
    deliver(actor, *common, approval.pk, uuid4())
    notice = RightsRecipientNotice.objects.filter(request=case).first()
    recipient = User.objects.get(pk=notice.recipient_id)
    recipient.mfa_enabled, recipient.mfa_version = True, 1
    recipient.save(update_fields=['mfa_enabled', 'mfa_version'])
    read, payload = inspect_notice(recipient, notice.pk, REASON)
    assert payload['execution'] == notice.execution_key
    return case, person, notice, recipient, read


@pytest.mark.parametrize('operation', ['inspect', 'acknowledge'])
@pytest.mark.parametrize('change', ['session', 'mfa', 'disabled', 'mfa_disabled', 'erased'])
def test_recipient_rechecks_authority_after_observed_wait(request, settings, monkeypatch, operation, change):
    case, person, notice, recipient, read = delivered(request, settings, monkeypatch)
    def forbidden_decrypt(*args, **kwargs):
        raise AssertionError('Revoked recipient must be denied before payload decryption')
    monkeypatch.setattr('apps.safety.communication_notices.checked_body', forbidden_decrypt)
    before = RightsAction.objects.filter(request=case, operation__in=['rights_notice_read', 'rights_notice_ack']).count()
    encrypted = notice.encrypted_payload
    pids = Queue()
    def attempt():
        connections.close_all()
        try:
            stale = User.objects.get(pk=recipient.pk)
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                pids.put(cursor.fetchone()[0])
            try:
                if operation == 'inspect':
                    inspect_notice(stale, notice.pk, REASON)
                else:
                    acknowledge(stale, notice.pk, read.pk)
                return 'allowed'
            except (PermissionDenied, ValidationError):
                return 'denied'
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Person.objects.select_for_update().get(pk=person.pk)
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            pid = pids.get(timeout=5)
            assert pid != holder
            observe_blocked(pid, holder)
            updates = {'session':{'session_version':recipient.session_version+1},
                       'mfa':{'mfa_version':recipient.mfa_version+1},
                       'disabled':{'is_active':False}, 'mfa_disabled':{'mfa_enabled':False},
                       'erased':{'account_erased_at':timezone.now()}}
            User.objects.filter(pk=recipient.pk).update(**updates[change])
        assert future.result(timeout=15) == 'denied'
    notice.refresh_from_db()
    assert not notice.acknowledged_at and notice.encrypted_payload == encrypted
    assert RightsAction.objects.filter(request=case, operation__in=['rights_notice_read', 'rights_notice_ack']).count() == before
