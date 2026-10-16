"""Live editor accounts still lose notice authority when representation changes."""
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from test_erasure_execution import REASON
from test_photo_reuse_races import observe_blocked
from test_recipient_notice_revocation_races import delivered
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AgencyMember, Person, User
from apps.safety.communication_notices import acknowledge, inspect_notice
from apps.safety.models import RightsAction, RightsRecipientNotice

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('operation', ['inspect', 'acknowledge'])
@pytest.mark.parametrize('change', ['unassigned', 'membership', 'manager_version'])
def test_live_editor_loses_notice_authority_after_observed_wait(request, settings, monkeypatch,
                                                               operation, change):
    case, person, _, _, _ = delivered(request, settings, monkeypatch)
    notice = RightsRecipientNotice.objects.get(request=case, recipient__username='fixture-v1-editor')
    recipient = User.objects.get(pk=notice.recipient_id)
    recipient.mfa_enabled, recipient.mfa_version = True, 1
    recipient.save(update_fields=['mfa_enabled', 'mfa_version'])
    read, payload = inspect_notice(recipient, notice.pk, REASON)
    assert payload['execution'] == notice.execution_key
    assert person.assigned_editor_id == recipient.pk
    assert AgencyMember.objects.filter(agency_id=person.agency_id, user=recipient, active=True).exists()
    before_user = (recipient.is_active, recipient.account_erased_at, recipient.session_version,
                   recipient.mfa_enabled, recipient.mfa_version)
    def forbidden_decrypt(*args, **kwargs):
        raise AssertionError('Editor without current representation must be denied before decryption')
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
            if change == 'unassigned':
                assert Person.objects.filter(pk=person.pk).update(assigned_editor_id=None) == 1
            elif change == 'membership':
                assert AgencyMember.objects.filter(agency_id=person.agency_id, user=recipient).update(active=False) == 1
            else:
                assert Person.objects.filter(pk=person.pk).update(manager_version=person.manager_version+1) == 1
        assert future.result(timeout=15) == 'denied'
    recipient.refresh_from_db()
    assert (recipient.is_active, recipient.account_erased_at, recipient.session_version,
            recipient.mfa_enabled, recipient.mfa_version) == before_user
    notice.refresh_from_db()
    assert not notice.acknowledged_at and notice.encrypted_payload == encrypted
    assert RightsAction.objects.filter(request=case, operation__in=['rights_notice_read', 'rights_notice_ack']).count() == before
