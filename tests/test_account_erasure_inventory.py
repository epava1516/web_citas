"""Audited account-purpose inventory and decisions preserve unrelated profiles."""

from copy import deepcopy
from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.test import Client
from django.utils import timezone
from test_account_copy_races import prepared_account
from test_erasure_plans import BASIS, REASON, SCOPE, form_payload
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import (
    AccountToken,
    Agency,
    LegalAcceptance,
    LegalDocument,
    Person,
    RecoveryCode,
)
from apps.listings.models import Favorite, Listing
from apps.safety.crypto import unseal
from apps.safety.erasure_plans import record
from apps.safety.models import ErasurePlan

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("agency", [False, True])
def test_account_inventory_and_reviewed_plan_http_are_scoped_and_non_destructive(
    request, settings, monkeypatch, agency
):
    case, actor, staff, subject, _, _ = prepared_account(request, settings, monkeypatch, "erase")
    if agency:
        owned = Agency.objects.first()
        owned.owner = subject
        owned.save(update_fields=["owner"])
    profiles = list(Person.objects.order_by("pk").values())
    AccountToken.objects.create(
        user=subject,
        digest="0" * 64,
        purpose="reset",
        expires_at=timezone.now() + timedelta(hours=1),
    )
    RecoveryCode.objects.create(user=subject, digest="1" * 64)
    Favorite.objects.create(user=subject, listing=Listing.objects.first())
    LegalAcceptance.objects.create(
        user=subject, document=LegalDocument.objects.first(), action="own_inventory_fixture"
    )
    before = subject.email, subject.password, subject.session_version
    from django.urls import reverse

    path = reverse("erasure_inventory", kwargs={"case_id": case.pk})
    page = staff.get(path)
    assert page.status_code == 200 and page.context["manifest"] is None
    assert subject.email.encode() not in page.content
    values = page.context["form"].initial | {
        "purpose": "Review own account resources before scoped erasure decisions"
    }
    assert Client(enforce_csrf_checks=True).post(path, values).status_code == 403
    response = staff.post(path, values)
    assert response.status_code == 200
    inventory = response.context["inventory"]
    manifest = response.context["manifest"]
    assert inventory.account_subject_id == subject.pk and inventory.person_id is None
    assert manifest["schema"] == "account-erasure-inventory-v1" and manifest["person"] is None
    assert manifest["account_has_other_responsibilities"] == agency
    assert subject.email not in str(manifest) and subject.password not in str(manifest)
    assert all("count" in row and len(row["state_digest"]) == 64 for row in manifest["entries"])
    assert manifest["media"] == [] and not manifest["execution_ready"]
    assert staff.post(path, values).context["inventory"].pk == inventory.pk
    decisions = [
        {
            "purpose": purpose,
            "operation": "review",
            "basis": BASIS,
            "reason": REASON,
            "scope": SCOPE,
            "review_on": (timezone.localdate() + timedelta(days=30)).isoformat(),
        }
        for purpose in sorted({row["purpose"] for row in manifest["entries"]})
    ]
    plan_path = f"/en/moderation/rights/{case.pk}/erasure-plan/{inventory.pk}/"
    data = form_payload(case, decisions)
    assert staff.post(plan_path, data).status_code == 200
    assert staff.post(plan_path, data).status_code == 200
    plan = ErasurePlan.objects.get(inventory=inventory)
    assert unseal(plan.encrypted_decisions)["decisions"] == decisions
    if agency:
        unsafe = deepcopy(decisions)
        for decision in unsafe:
            if decision["purpose"] == "account":
                decision.update(operation="erase", review_on=None)
        with pytest.raises(ValidationError, match="Shared resources"):
            record(actor, case.pk, inventory.pk, uuid4(), case.version, unsafe)
    Favorite.objects.create(
        user=subject, listing=Listing.objects.exclude(pk=Listing.objects.first().pk).first()
    )
    with pytest.raises(ValidationError, match="Resources changed"):
        record(actor, case.pk, inventory.pk, uuid4(), case.version, decisions)
    subject.refresh_from_db()
    assert (subject.email, subject.password, subject.session_version) == before
    assert (
        AccountToken.objects.filter(user=subject).count()
        == RecoveryCode.objects.filter(user=subject).count()
        == 1
    )
    assert list(Person.objects.order_by("pk").values()) == profiles
    assert not Person.objects.filter(subject=subject).exists()
