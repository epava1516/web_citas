"""Notice census scope and opaque state, separate from actual delivery verification."""

from uuid import uuid4

import pytest
from django.db import transaction
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import Person, User
from apps.safety.crypto import seal
from apps.safety.erasure_inventory import source_manifest
from apps.safety.models import RightsAction, RightsRecipientNotice, RightsRequest
from apps.safety.rights_access_scope_inventory import source as access_source
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def notice(case, recipient, actor, **changes):
    # Synthetic ledger for census only: intentionally not an approved delivery.
    action = RightsAction.objects.create(
        key=uuid4(),
        request=case,
        actor=actor,
        expected_version=case.version,
        operation="inventory_fixture",
        payload_digest="0" * 64,
        encrypted_reason=seal({}),
    )
    return RightsRecipientNotice.objects.create(
        request=case,
        action=action,
        recipient=recipient,
        execution_key=str(uuid4()),
        authorization_version="account",
        encrypted_payload=seal({"private": "Synthetic private notice"}),
        payload_digest="1" * 64,
        **changes,
    )


def historical(case, **changes):
    fields = {
        "submission_key": uuid4(),
        "actor": case.actor,
        "kind": "erase",
        "receipt_digest": uuid4().hex,
        "payload_digest": "0" * 64,
        "encrypted_payload": seal({"synthetic_census_only": True}),
        "account_subject": case.account_subject,
        "person": case.person,
        "manager_version": case.manager_version,
        "received_at": case.received_at,
        "initial_due_at": case.initial_due_at,
        "receipt_expires_at": case.receipt_expires_at,
    }
    return RightsRequest.objects.create(**(fields | changes))


def inventory(case, *, access=False):
    with transaction.atomic():
        current, person, _ = locked_case(case.pk, lock_listing=True)
        body = access_source(current, person) if access else source_manifest(person, current)
        return next(
            row for row in body["entries"] if row["model"] == "safety.RightsRecipientNotice"
        )


@pytest.mark.parametrize("scope", ["profile", "account"])
def test_census_includes_owned_notice_evidence_and_opaque_changes_only(
    request, settings, monkeypatch, scope
):
    if scope == "account":
        case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, _, _, _, person = ready(request, settings, monkeypatch, "access")
        subject = person.subject
    outsider = User.objects.get(username="fixture-v1-visitor")
    history = historical(case)
    own = notice(history, subject, actor)
    current_notice = notice(case, subject, actor)
    other_person = Person.objects.exclude(pk=case.person_id).first()
    foreign_case = historical(
        case,
        actor=outsider,
        account_subject=None,
        person=other_person,
        manager_version=other_person.manager_version,
    )
    foreign = notice(foreign_case, outsider, outsider)
    initial = inventory(case)
    # Access scope removes current-case references automatically; conservation
    # keeps them for access cases but marks ongoing erase/process procedures separately.
    assert initial["count"] == 2
    access = inventory(case, access=True)
    assert access["count"] == 1
    assert "Synthetic private notice" not in str(access)
    assert own.encrypted_payload not in str(access)
    fields = access["records"][0]["fields"]
    assert {"encrypted_payload", "acknowledged_action_id", "acknowledged_read_id"} <= set(fields)
    own.encrypted_payload = "Malformed ciphertext census must not decrypt"
    own.save(update_fields=["encrypted_payload"])
    changed = inventory(case, access=True)
    assert changed["count"] == 1 and changed["digest"] != access["digest"]
    foreign.encrypted_payload = "Foreign ciphertext change"
    foreign.save(update_fields=["encrypted_payload"])
    assert inventory(case, access=True) == changed
    current_notice.encrypted_payload = "Current-procedure ciphertext change"
    current_notice.save(update_fields=["encrypted_payload"])
    assert inventory(case, access=True) == changed
    case.kind = "erase"
    case.save(update_fields=["kind"])
    assert inventory(case)["count"] == 1
