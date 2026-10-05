"""Independent review cannot bypass live source, proof or audited inspection."""

from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse
from test_account_copy_races import prepared_account
from test_processing_plans import REASON, decisions
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import User
from apps.listings.models import Favorite, Listing
from apps.safety.crypto import seal, unseal
from apps.safety.models import ProcessingPlanRead, ProcessingPlanReview
from apps.safety.processing_plans import prepare
from apps.safety.processing_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch):
    case, actor, staff, subject, _, _ = prepared_account(
        request, settings, monkeypatch, "restriction"
    )
    values = decisions(case)
    for item in values:
        item["operation"] = "continue"
    plan = prepare(actor, case.pk, uuid4(), case.version, REASON, values)
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_processing_plan",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    return case, actor, subject, plan, reviewer, client


def test_independent_http_read_review_replay_and_reload(request, settings, monkeypatch):
    case, actor, subject, plan, reviewer, client = prepared(request, settings, monkeypatch)
    original = (
        case.version,
        case.status,
        case.initial_due_at,
        subject.email,
        subject.session_version,
    )
    path = reverse("processing_review", kwargs={"case_id": case.pk, "plan_id": plan.pk})
    assert client.get(path).status_code == 200 and REASON not in client.get(path).content.decode()
    data = {
        "key": uuid4(),
        "version": case.version,
        "operation": "review",
        "reason": REASON,
        "outcome": "approved",
    }
    assert client.post(path, data).status_code == 409
    inspected = {
        "key": uuid4(),
        "version": case.version,
        "operation": "inspect",
        "reason": REASON,
        "outcome": "",
    }
    response = client.post(path, inspected)
    assert response.status_code == 200 and response.context["body"]["enforced"] is False
    assert (
        client.post(path, inspected).status_code == 200 and ProcessingPlanRead.objects.count() == 1
    )
    assert client.post(path, data).status_code == 200 and client.post(path, data).status_code == 200
    assert (
        ProcessingPlanReview.objects.count() == 1
        and REASON not in client.get(path).content.decode()
    )
    actor.user_permissions.add(Permission.objects.get(codename="review_processing_plan"))
    actor = User.objects.get(pk=actor.pk)
    with pytest.raises(PermissionDenied):
        record(actor, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "rejected")
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (
        case.version,
        case.status,
        case.initial_due_at,
        subject.email,
        subject.session_version,
    ) == original


def test_mutated_ciphertext_and_live_source_cannot_be_reviewed(request, settings, monkeypatch):
    case, _, subject, plan, reviewer, _ = prepared(request, settings, monkeypatch)
    body = unseal(plan.encrypted_plan)
    original_ciphertext = plan.encrypted_plan
    body["decisions"][0]["operation"] = "cease"
    plan.encrypted_plan = seal(body)
    plan.save(update_fields=["encrypted_plan"])
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    assert not ProcessingPlanRead.objects.exists()
    plan.encrypted_plan = original_ciphertext
    plan.save(update_fields=["encrypted_plan"])
    Favorite.objects.create(user=subject, listing=Listing.objects.first())
    with pytest.raises(ValidationError):
        record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
    assert not ProcessingPlanReview.objects.exists()


def test_pending_purpose_cannot_be_approved_but_can_be_rejected(request, settings, monkeypatch):
    case, actor, subject, _, reviewer, client = prepared(request, settings, monkeypatch)
    plan = prepare(actor, case.pk, uuid4(), case.version, REASON, decisions(case))
    record(reviewer, case.pk, plan.pk, uuid4(), case.version, "inspect", REASON)
    with pytest.raises(ValidationError, match="Unresolved purposes"):
        record(reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "approved")
    assert not ProcessingPlanReview.objects.filter(plan=plan).exists()
    result, _ = record(
        reviewer, case.pk, plan.pk, uuid4(), case.version, "review", REASON, "rejected"
    )
    assert result.outcome == "rejected"
