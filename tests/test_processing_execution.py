"""Reviewed preferences are preserved and blocked across ordinary and erasure routes."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_processing_plans import REASON, decisions
from test_processing_review import prepared as prepared_review
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.accounts import docs
from apps.core.models import LegalAcceptance, User
from apps.listings.models import Favorite, Listing
from apps.listings.moderation import publicly_visible
from apps.safety.crypto import unseal
from apps.safety.models import ProcessingExecution, PurposeRestriction
from apps.safety.processing_execution import execute
from apps.safety.processing_plans import prepare
from apps.safety.processing_review import record
from apps.safety.purpose_restrictions import restricted

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch):
    import test_account_copy_races

    request.getfixturevalue("directory")

    def account():
        user = User.objects.create_user(
            username="restricted-account",
            email="restricted@example.invalid",
            password="Synthetic-private-setup-123",
            email_verified_at=timezone.now(),
        )
        for document in docs("en"):
            LegalAcceptance.objects.create(user=user, document=document, action="account")
        return user

    monkeypatch.setattr(test_account_copy_races, "account", account)
    case, actor, subject, _, reviewer, client = prepared_review(request, settings, monkeypatch)
    listing = next(row for row in Listing.objects.order_by("pk") if publicly_visible(row))
    favorite = Favorite.objects.create(user=subject, listing=listing)
    values = decisions(case)
    for item in values:
        item["operation"] = "restrict" if item["purpose"] == "account_preferences" else "continue"
    plan = prepare(actor, case.pk, uuid4(), case.version, REASON, values)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
    return case, actor, subject, plan, favorite, client


def test_http_execution_preserves_favorites_blocks_ordinary_use_and_keeps_rights(
    request, settings, monkeypatch
):
    case, actor, subject, plan, favorite, reviewer = prepared(request, settings, monkeypatch)
    staff = Client()
    staff.force_login(actor)
    session = staff.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    own = Client()
    own.force_login(subject)
    assert own.get(reverse("favorites")).status_code == 200
    original = (case.initial_due_at, subject.email, subject.is_active, subject.session_version)
    path = reverse("processing_execute", kwargs={"case_id": case.pk, "plan_id": plan.pk})
    payload = dict(
        key=uuid4(),
        version=case.version,
        purposes=["account_preferences"],
        reason=REASON,
        confirmed=True,
    )
    assert Client(enforce_csrf_checks=True).post(path, payload).status_code == 403
    assert (
        staff.post(path, payload).status_code == 200
        and staff.post(path, payload).status_code == 200
    )
    assert ProcessingExecution.objects.count() == PurposeRestriction.objects.count() == 1
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert own.get(reverse("favorites")).status_code == 409
    assert (
        own.post(reverse("favorite_add", kwargs={"listing_id": favorite.listing_id})).status_code
        == 409
    )
    assert (
        own.post(reverse("favorite_remove", kwargs={"favorite_id": favorite.pk})).status_code == 409
    )
    assert reviewer.get(reverse("favorites")).status_code == 200
    assert own.get(reverse("rights_create")).status_code == 200
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (
        case.initial_due_at,
        subject.email,
        subject.is_active,
        subject.session_version,
    ) == original
    assert case.status == "reviewing" and case.scope_status == "unverified"
    result = unseal(ProcessingExecution.objects.get().encrypted_result)
    assert result["data_deleted"] is False and result["partial"] is True
    PurposeRestriction.objects.update(review_on=timezone.localdate() - timedelta(days=1))
    with transaction.atomic():
        assert restricted(subject, "account_preferences")
    assert own.get(reverse("favorites")).status_code == 409


def test_unsupported_purpose_rolls_back_without_restrictions(request, settings, monkeypatch):
    case, actor, _, plan, _, _ = prepared(request, settings, monkeypatch)
    with pytest.raises(ValidationError):
        execute(
            actor,
            case.pk,
            plan.pk,
            uuid4(),
            case.version,
            ["account_preferences", "authentication"],
            REASON,
            True,
        )
    assert not ProcessingExecution.objects.exists() and not PurposeRestriction.objects.exists()


def test_new_erasure_cannot_delete_restricted_preferences(request, settings, monkeypatch):
    from test_rights_intake import data
    from test_rights_verification import read

    from apps.safety.erasure_execution import execute as erase
    from apps.safety.erasure_inventory import prepare as inventory
    from apps.safety.erasure_plans import record as erasure_plan
    from apps.safety.models import ErasureExecution, RightsRequest
    from apps.safety.rights_actions import act
    from apps.safety.rights_verification import receive_event, simulate_event, start

    case, actor, subject, plan, favorite, independent = prepared(request, settings, monkeypatch)
    execute(actor, case.pk, plan.pk, uuid4(), case.version, ["account_preferences"], REASON, True)
    before = set(RightsRequest.objects.values_list("pk", flat=True))
    public = Client()
    assert public.post("/en/safety/rights/", data(public, kind="erase")).status_code == 302
    erase_case = RightsRequest.objects.exclude(pk__in=before).get()
    executor = User.objects.get(pk=actor.pk)
    staff = Client()
    staff.force_login(executor)
    session = staff.session
    session["mfa_version"] = executor.mfa_version
    session.save()
    erase_case = act(executor, erase_case.pk, uuid4(), erase_case.version, "claim", REASON)
    read(staff, erase_case)
    erase_case = act(
        executor,
        erase_case.pk,
        uuid4(),
        erase_case.version,
        "link",
        REASON,
        link_account_id=subject.pk,
    )
    read(staff, erase_case)
    proof = start(executor, erase_case.pk, uuid4(), erase_case.version, REASON)
    erase_case.refresh_from_db()
    verifier = User.objects.get(username="fixture-v1-visitor")
    read(independent, erase_case)
    receive_event(verifier, simulate_event(proof.pk, uuid4(), erase_case.version, "passed", REASON))
    erase_case.refresh_from_db()
    read(staff, erase_case)
    snapshot = inventory(executor, erase_case.pk, uuid4(), erase_case.version, REASON)
    values = [
        dict(
            purpose=p,
            operation="erase" if p == "account_preferences" else "retain",
            basis=REASON,
            reason=REASON,
            scope=REASON,
            review_on=None
            if p == "account_preferences"
            else (timezone.localdate() + timedelta(days=7)).isoformat(),
        )
        for p in sorted({row["purpose"] for row in unseal(snapshot.encrypted_manifest)["entries"]})
    ]
    prepared_plan = erasure_plan(
        executor, erase_case.pk, snapshot.pk, uuid4(), erase_case.version, values
    )
    with pytest.raises(ValidationError, match="Purpose restricted"):
        erase(
            executor,
            erase_case.pk,
            prepared_plan.pk,
            uuid4(),
            erase_case.version,
            ["account_preferences"],
            REASON,
            True,
        )
    assert (
        not ErasureExecution.objects.exists() and Favorite.objects.filter(pk=favorite.pk).exists()
    )
