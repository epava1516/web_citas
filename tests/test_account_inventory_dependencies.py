"""Account dependency metadata does not expose bodies or invalidate its own procedure."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_erasure_plans import BASIS, REASON, SCOPE
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.account_erasure_inventory import source
from apps.safety.crypto import seal, unseal
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record
from apps.safety.models import ErasureInventory, ErasurePlan, RightsAction, RightsMessage
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def test_dependency_change_invalidates_plan_without_reading_body_or_circular_artifacts(
    request, settings, monkeypatch
):
    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch, "erase")
    snapshot = prepare(actor, case.pk, uuid4(), case.version, REASON)
    manifest = unseal(snapshot.encrypted_manifest)
    rows = {row["model"]: row for row in manifest["entries"]}
    assert manifest["schema"] == "account-erasure-inventory-v2"
    assert rows["safety.RightsAccess"]["count"] > 0
    assert rows["safety.RightsProofEvent"]["count"] == 1
    assert (
        rows["safety.ErasureInventory"]["count"]
        == rows["safety.ErasurePlan"]["count"]
        == rows["safety.ErasureExecution"]["count"]
        == 0
    )
    decisions = [
        {
            "purpose": purpose,
            "operation": "retain",
            "basis": BASIS,
            "reason": REASON,
            "scope": SCOPE,
            "review_on": (timezone.localdate() + timedelta(days=30)).isoformat(),
        }
        for purpose in sorted({row["purpose"] for row in manifest["entries"]})
    ]
    plan = record(actor, case.pk, snapshot.pk, uuid4(), case.version, decisions)
    with transaction.atomic():
        current, _, _ = locked_case(case.pk)
        assert source(current) == manifest
    assert (
        record(actor, case.pk, snapshot.pk, plan.action.key, case.version, decisions).pk == plan.pk
    )
    secret_text = "Synthetic requester text containing unrelated private details"
    message = RightsMessage.objects.create(
        key=uuid4(),
        request=case,
        actor=subject,
        expected_version=case.version,
        payload_digest="0" * 64,
        encrypted_payload=seal({"text": secret_text}),
    )
    with transaction.atomic():
        current, _, _ = locked_case(case.pk)
        changed = source(current)
    changed_rows = {row["model"]: row for row in changed["entries"]}
    assert changed_rows["safety.RightsMessage"]["count"] == 1
    assert (
        changed_rows["safety.RightsMessage"]["state_digest"]
        != rows["safety.RightsMessage"]["state_digest"]
    )
    assert secret_text not in str(changed) and message.encrypted_payload not in str(changed)
    original = (
        RightsAction.objects.count(),
        ErasureInventory.objects.count(),
        ErasurePlan.objects.count(),
    )
    with pytest.raises(ValidationError, match="Resources changed"):
        record(actor, case.pk, snapshot.pk, uuid4(), case.version, decisions)
    assert (
        RightsAction.objects.count(),
        ErasureInventory.objects.count(),
        ErasurePlan.objects.count(),
    ) == original


def test_legacy_inventory_requires_fresh_review_and_keeps_original_ciphertext(
    request, settings, monkeypatch
):
    from apps.safety import account_erasure_inventory

    case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch, "erase")
    current_source = account_erasure_inventory.source

    def legacy_source(current):
        manifest = current_source(current)
        manifest["schema"] = "account-erasure-inventory-v1"
        manifest["entries"] = manifest["entries"][:14]
        manifest["pending"].remove("current_procedure_audit_excluded")
        return manifest

    with monkeypatch.context() as patch:
        patch.setattr(account_erasure_inventory, "source", legacy_source)
        legacy = prepare(actor, case.pk, uuid4(), case.version, REASON)
    ciphertext, digest = legacy.encrypted_manifest, legacy.source_digest
    decisions = [
        {
            "purpose": purpose,
            "operation": "retain",
            "basis": BASIS,
            "reason": REASON,
            "scope": SCOPE,
            "review_on": (timezone.localdate() + timedelta(days=30)).isoformat(),
        }
        for purpose in sorted({row["purpose"] for row in unseal(ciphertext)["entries"]})
    ]
    with pytest.raises(ValidationError, match="Resources changed"):
        record(actor, case.pk, legacy.pk, uuid4(), case.version, decisions)
    legacy.refresh_from_db()
    assert (legacy.encrypted_manifest, legacy.source_digest) == (ciphertext, digest)
    assert not ErasurePlan.objects.exists()
    fresh = prepare(actor, case.pk, uuid4(), case.version, REASON)
    plan = record(actor, case.pk, fresh.pk, uuid4(), case.version, decisions)
    assert plan.inventory_id == fresh.pk and fresh.pk != legacy.pk
    assert unseal(fresh.encrypted_manifest)["schema"] == "account-erasure-inventory-v2"
    assert legacy.source_digest != fresh.source_digest
    subject.refresh_from_db()
    assert not subject.account_erased_at
