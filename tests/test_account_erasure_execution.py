"""Own-account erasure preserves profiles, organization ownership and the rights channel."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_erasure_plans import BASIS, REASON, SCOPE
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import values
from test_rights_verification import read

from apps.core.models import (
    AccountToken,
    Agency,
    LegalAcceptance,
    LegalDocument,
    Person,
    RecoveryCode,
)
from apps.listings.models import Favorite, Listing
from apps.safety.crypto import seal, unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record
from apps.safety.models import ErasureExecution, RightsAction, RightsExport
from apps.safety.rights_verification import start

pytestmark = pytest.mark.django_db(transaction=True)


def prepared_erasure(request, settings, monkeypatch, agency=False):
    case, actor, staff, subject, public, receipt = prepared_account(
        request, settings, monkeypatch, "erase"
    )
    if agency:
        owned = Agency.objects.first()
        owned.owner = subject
        owned.save(update_fields=["owner"])
    AccountToken.objects.create(
        user=subject,
        purpose="reset",
        digest="0" * 64,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    RecoveryCode.objects.create(user=subject, digest="1" * 64)
    Favorite.objects.create(user=subject, listing=Listing.objects.first())
    acceptance = LegalAcceptance.objects.create(
        user=subject, document=LegalDocument.objects.first(), action="synthetic_erasure_fixture"
    )
    action = RightsAction.objects.create(
        key=uuid4(),
        request=case,
        actor=actor,
        expected_version=case.version,
        operation="export",
        payload_digest="2" * 64,
        encrypted_reason=seal({"reason": "Synthetic snapshot, not an authorized access delivery"}),
    )
    copy = RightsExport.objects.create(
        action=action,
        proof=case.proofs.latest("created_at"),
        account_subject=subject,
        case_version=case.version,
        manager_version=None,
        subject_snapshot=str(subject.pk),
        channel_digest=case.receipt_digest,
        encrypted_payload=seal({"synthetic_snapshot": True}),
        expires_at=timezone.now() + timedelta(hours=1),
    )
    snapshot = prepare(actor, case.pk, uuid4(), case.version, REASON)
    purposes = ["authentication", "account_preferences", "transient_copy"] + (
        [] if agency else ["account"]
    )
    decisions = [
        {
            "purpose": purpose,
            "operation": "erase" if purpose in purposes else "retain",
            "basis": BASIS,
            "reason": REASON,
            "scope": SCOPE,
            "review_on": None
            if purpose in purposes
            else (timezone.localdate() + timedelta(days=30)).isoformat(),
        }
        for purpose in sorted(
            {row["purpose"] for row in unseal(snapshot.encrypted_manifest)["entries"]}
        )
    ]
    plan = record(actor, case.pk, snapshot.pk, uuid4(), case.version, decisions)
    return case, actor, staff, subject, public, receipt, plan, purposes, copy, acceptance


@pytest.mark.parametrize("agency", [False, True])
def test_account_scoped_execution_preserves_evidence_and_procedural_channel(
    request, settings, monkeypatch, agency
):
    case, actor, staff, subject, public, receipt, plan, purposes, copy, acceptance = (
        prepared_erasure(request, settings, monkeypatch, agency)
    )
    profiles = list(Person.objects.order_by("pk").values())
    agencies = list(Agency.objects.order_by("pk").values())
    from django.urls import reverse

    path = reverse("erasure_execute", kwargs={"case_id": case.pk, "plan_id": plan.pk})
    data = {
        "key": uuid4(),
        "version": case.version,
        "purposes": purposes,
        "reason": REASON,
        "confirmed": True,
    }
    before = subject.email, subject.password, subject.session_version, subject.mfa_version
    assert staff.get(path).status_code == 200
    assert "publication" not in {
        value for value, _ in staff.get(path).context["form"].fields["purposes"].choices
    }
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    response = staff.post(path, data)
    assert response.status_code == 200
    assert staff.post(path, data).status_code == 200
    execution = ErasureExecution.objects.get(plan=plan)
    assert execution.person_id is None and execution.account_subject_id == subject.pk
    result = unseal(execution.encrypted_result)
    assert result["schema"] == "account-erasure-execution-v1" and result["partial"]
    assert (
        result["tokens_deleted"]
        == result["recovery_codes_deleted"]
        == result["favorites_deleted"]
        == result["copies_cleared"]
        == 1
    )
    assert not AccountToken.objects.filter(user=subject).exists()
    assert not RecoveryCode.objects.filter(user=subject).exists()
    assert not Favorite.objects.filter(user=subject).exists()
    copy.refresh_from_db()
    assert copy.encrypted_payload == "" and copy.purged_at
    assert LegalAcceptance.objects.filter(pk=acceptance.pk).exists()
    assert list(Person.objects.order_by("pk").values()) == profiles
    assert list(Agency.objects.order_by("pk").values()) == agencies
    subject.refresh_from_db()
    assert (subject.session_version, subject.mfa_version) == (before[2] + 1, before[3] + 1)
    if agency:
        assert (subject.email, subject.password) == before[:2] and not subject.account_erased_at
    else:
        assert (
            subject.account_erased_at
            and not subject.is_active
            and not subject.has_usable_password()
        )
        assert subject.email != before[0] and not subject.first_name and not subject.last_name
    case.refresh_from_db()
    assert (
        case.version == data["version"] + 1
        and case.status == "reviewing"
        and case.scope_status == "unverified"
    )
    read(staff, case)
    assert staff.post(f"/en/moderation/rights/{case.pk}/response/", values(case)).status_code == 302
    assert public.get(receipt).status_code == 200
    if agency:
        fresh = start(actor, case.pk, uuid4(), case.version, REASON)
        assert fresh.account_subject_id == subject.pk and fresh.status == "pending"
    else:
        with pytest.raises(ValidationError):
            start(actor, case.pk, uuid4(), case.version, REASON)
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)


def test_account_execution_denies_unreviewed_editorial_stale_and_production_scopes(
    request, settings, monkeypatch
):
    from django.core.exceptions import PermissionDenied

    case, actor, _, subject, _, _, plan, purposes, stored, _ = prepared_erasure(
        request, settings, monkeypatch
    )
    original = subject.email, subject.password, subject.session_version, subject.mfa_version
    attempts = [
        (case.version, purposes, False),
        (case.version, ["publication"], True),
        (case.version, ["account"], True),
        (case.version - 1, purposes, True),
        (case.version, ["evidence"], True),
    ]
    for version, selected, confirmed in attempts:
        with pytest.raises(ValidationError):
            execute(actor, case.pk, plan.pk, uuid4(), version, selected, REASON, confirmed)
    with pytest.raises(PermissionDenied):
        execute(subject, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    settings.PRODUCTION = True
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    settings.PRODUCTION = False
    Favorite.objects.create(
        user=subject, listing=Listing.objects.exclude(pk=Listing.objects.first().pk).first()
    )
    with pytest.raises(ValidationError, match="Resources changed"):
        execute(actor, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    assert not ErasureExecution.objects.exists()
    assert not RightsAction.objects.filter(operation="erasure_execute").exists()
    subject.refresh_from_db()
    stored.refresh_from_db()
    assert (
        subject.email,
        subject.password,
        subject.session_version,
        subject.mfa_version,
    ) == original
    assert stored.encrypted_payload and not stored.purged_at
    assert (
        AccountToken.objects.filter(user=subject).count()
        == RecoveryCode.objects.filter(user=subject).count()
        == 1
    )
