"""Person NULL never grants an account erasure plan access to another account copy."""

from copy import copy
from uuid import uuid4

import pytest
from test_account_erasure_execution import prepared_erasure
from test_erasure_plans import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.crypto import seal
from apps.safety.erasure_execution import execute
from apps.safety.models import ErasureExecution

pytestmark = pytest.mark.django_db(transaction=True)


def test_account_copy_erasure_preserves_another_account_ciphertext_and_metadata(
    request, settings, monkeypatch
):
    case, actor, _, _, _, _, plan, purposes, stored, _ = prepared_erasure(
        request, settings, monkeypatch
    )
    other = User.objects.create_user(
        username="other-account-copy", email="other-account-copy@example.invalid"
    )
    # Stored fixtures with pending identity checks; none is an authorized delivery.
    foreign_case = copy(case)
    foreign_case.pk = uuid4()
    foreign_case.submission_key = uuid4()
    foreign_case.kind = "access"
    foreign_case.account_subject = other
    foreign_case.actor = other
    foreign_case.reported_subject = other
    foreign_case.receipt_digest = "3" * 64
    foreign_case.save(force_insert=True)
    foreign_proof = copy(stored.proof)
    foreign_proof.pk = uuid4()
    foreign_proof.key = uuid4()
    foreign_proof.request = foreign_case
    foreign_proof.account_subject = other
    foreign_proof.subject_id_snapshot = str(other.pk)
    foreign_proof.status = "pending"
    foreign_proof.scope = "access"
    foreign_proof.channel_digest = foreign_case.receipt_digest
    foreign_proof.account_source_digest = ""
    foreign_proof.save(force_insert=True)
    foreign_action = copy(stored.action)
    foreign_action.pk = None
    foreign_action.key = uuid4()
    foreign_action.request = foreign_case
    foreign_action.save(force_insert=True)
    foreign_copy = copy(stored)
    foreign_copy.pk = uuid4()
    foreign_copy.action = foreign_action
    foreign_copy.proof = foreign_proof
    foreign_copy.account_subject = other
    foreign_copy.subject_snapshot = str(other.pk)
    foreign_copy.channel_digest = foreign_case.receipt_digest
    foreign_copy.encrypted_payload = seal({"synthetic_foreign_snapshot": True})
    foreign_copy.save(force_insert=True)
    original = (
        foreign_copy.encrypted_payload,
        foreign_copy.purged_at,
        other.email,
        other.session_version,
    )
    execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    foreign_copy.refresh_from_db()
    other.refresh_from_db()
    stored.refresh_from_db()
    assert (
        foreign_copy.encrypted_payload,
        foreign_copy.purged_at,
        other.email,
        other.session_version,
    ) == original
    assert stored.encrypted_payload == "" and stored.purged_at
    assert not ErasureExecution.objects.filter(account_subject=other).exists()
