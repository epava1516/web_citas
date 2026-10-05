"""Follow-up dates never authorize retention or reactivate an expired erasure plan."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_account_erasure_execution import prepared_erasure
from test_erasure_plans import BASIS, REASON
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.models import Person, User
from apps.safety.crypto import seal, unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RetentionReview, RetentionReviewEvent
from apps.safety.retention_reviews import record
from apps.safety.tasks import reconcile_retention_reviews

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch):
    case, creator, staff, subject, public, receipt, plan, purposes, stored, acceptance = (
        prepared_erasure(request, settings, monkeypatch)
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_rights_request", "review_retention"])
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    read(client, case)
    return case, creator, reviewer, client, staff, subject, plan, purposes


def values(case, review, operation="inspect", **changes):
    return {
        "key": uuid4(),
        "version": review.version,
        "case_version": case.version,
        "operation": operation,
        "reason": REASON,
        **(
            {"next_review_on": timezone.localdate() + timedelta(days=7)}
            if operation == "follow_up"
            else {}
        ),
    } | changes


def test_plan_schedules_all_retained_purposes_and_reconciliation_is_idempotent(
    request, settings, monkeypatch
):
    case, _, _, _, _, _, plan, _ = prepared(request, settings, monkeypatch)
    expected = {
        row["purpose"]
        for row in unseal(plan.encrypted_decisions)["decisions"]
        if row["operation"] in {"retain", "review"}
    }
    rows = RetentionReview.objects.filter(plan=plan)
    assert set(rows.values_list("purpose", flat=True)) == expected
    assert all(
        row.initial_review_on == row.next_review_on == plan.review_on
        and row.responsible_id == plan.action.actor_id
        for row in rows
    )
    assert reconcile_retention_reviews() == {"plans": 0, "scheduled": 0, "failed": 0}
    rows.delete()
    assert reconcile_retention_reviews() == {"plans": 1, "scheduled": len(expected), "failed": 0}
    assert reconcile_retention_reviews() == {"plans": 0, "scheduled": 0, "failed": 0}
    assert not RetentionReviewEvent.objects.exists()
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_private_audited_independent_followup_preserves_original_plan_and_deadlines(
    request, settings, monkeypatch
):
    case, creator, reviewer, client, staff, subject, plan, _ = prepared(
        request, settings, monkeypatch
    )
    review = RetentionReview.objects.filter(plan=plan).first()
    path = reverse("retention_review", kwargs={"review_id": review.pk})
    original = (
        plan.encrypted_decisions,
        plan.review_on,
        case.version,
        case.initial_due_at,
        subject.email,
        subject.session_version,
    )
    assert Client().get(path).status_code == 302
    assert client.get(path).status_code == 200 and BASIS.encode() not in client.get(path).content
    assert client.get(path)["Cache-Control"] == "private, no-store"
    assert Client(enforce_csrf_checks=True).post(path, values(case, review)).status_code == 403
    with pytest.raises(ValidationError, match="Inspect the current purpose"):
        record(reviewer, review.pk, **values(case, review, "follow_up"))
    inspected = values(case, review)
    response = client.post(path, inspected)
    assert response.status_code == 200 and response.context["decision"]["basis"] == BASIS
    assert client.post(path, inspected).status_code == 200
    assert RetentionReviewEvent.objects.filter(operation="inspect").count() == 1
    followup = values(case, review, "follow_up")
    assert client.post(path, followup).status_code == client.post(path, followup).status_code == 200
    review.refresh_from_db()
    assert review.version == 2 and review.responsible_id == reviewer.pk and review.last_reviewed_at
    assert (
        review.next_review_on == followup["next_review_on"]
        and review.initial_review_on == original[1]
    )
    assert RetentionReviewEvent.objects.filter(operation="follow_up").count() == 1
    assert (
        BASIS.encode() not in client.get(path).content
        and REASON.encode() not in client.get(path).content
    )
    plan.refresh_from_db()
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (
        plan.encrypted_decisions,
        plan.review_on,
        case.version,
        case.initial_due_at,
        subject.email,
        subject.session_version,
    ) == original
    creator.user_permissions.add(Permission.objects.get(codename="review_retention"))
    creator = User.objects.get(pk=creator.pk)
    read(staff, case)
    record(creator, review.pk, **values(case, review))
    with pytest.raises(PermissionDenied, match="Independent reviewer"):
        record(creator, review.pk, **values(case, review, "follow_up"))
    with pytest.raises(ValidationError):
        record(reviewer, review.pk, **values(case, review, "follow_up", version=1))


def test_calendar_and_followup_survive_erased_account_without_mutating_data(
    request, settings, monkeypatch
):
    case, creator, reviewer, client, _, subject, plan, purposes = prepared(
        request, settings, monkeypatch
    )
    # Read added to the expanded source; rebuild inventory/plan before execution.
    from apps.safety.erasure_inventory import prepare as inventory
    from apps.safety.erasure_plans import record as record_plan

    snapshot = inventory(creator, case.pk, uuid4(), case.version, REASON)
    plan = record_plan(
        creator,
        case.pk,
        snapshot.pk,
        uuid4(),
        case.version,
        unseal(plan.encrypted_decisions)["decisions"],
    )
    execute(creator, case.pk, plan.pk, uuid4(), case.version, purposes, REASON, True)
    case.refresh_from_db()
    subject.refresh_from_db()
    assert subject.account_erased_at
    read(client, case)
    profiles = list(Person.objects.order_by("pk").values())
    original = (
        subject.email,
        subject.password,
        subject.session_version,
        case.version,
        case.initial_due_at,
    )
    review = RetentionReview.objects.filter(plan=plan).first()
    record(reviewer, review.pk, **values(case, review))
    record(reviewer, review.pk, **values(case, review, "follow_up"))
    path = reverse("retention_queue")
    page = client.get(path, {"attention": "all"})
    assert page.status_code == 200 and len(page.context["page"]) > 0
    assert subject.email.encode() not in page.content and BASIS.encode() not in page.content
    subject.refresh_from_db()
    case.refresh_from_db()
    assert (
        subject.email,
        subject.password,
        subject.session_version,
        case.version,
        case.initial_due_at,
    ) == original
    assert list(Person.objects.order_by("pk").values()) == profiles


def test_tampered_plan_is_not_displayed_or_scheduled(request, settings, monkeypatch):
    case, _, reviewer, client, _, _, plan, _ = prepared(request, settings, monkeypatch)
    review = RetentionReview.objects.filter(plan=plan).first()
    plan.encrypted_decisions = seal({"schema": "erasure-plan-v1", "decisions": []})
    plan.save(update_fields=["encrypted_decisions"])
    path = reverse("retention_review", kwargs={"review_id": review.pk})
    assert client.post(path, values(case, review)).status_code == 409
    assert not RetentionReviewEvent.objects.exists()
    RetentionReview.objects.filter(plan=plan).delete()
    assert reconcile_retention_reviews() == {"plans": 1, "scheduled": 0, "failed": 1}


def test_history_pages_are_required_and_inspection_replay_keeps_its_original_snapshot(
    request, settings, monkeypatch
):
    from apps.safety.rights import fingerprint

    case, _, reviewer, _, _, _, plan, _ = prepared(request, settings, monkeypatch)
    review = RetentionReview.objects.filter(plan=plan).first()
    for index in range(51):
        RetentionReviewEvent.objects.create(
            key=uuid4(),
            review=review,
            actor=reviewer,
            expected_version=index + 1,
            case_version=case.version,
            operation="follow_up",
            plan_digest=fingerprint(plan.encrypted_decisions),
            payload_digest="0" * 64,
            encrypted_reason=seal(
                {"reason": "Synthetic historical follow-up awaiting further work"}
            ),
            next_review_on=timezone.localdate() + timedelta(days=7),
        )
    review.version = 52
    review.save(update_fields=["version"])
    first_values = values(case, review)
    _, first = record(reviewer, review.pk, **first_values)
    assert len(first["follow_up_history"]) == 50 and first["next_history_before"]
    with pytest.raises(ValidationError, match="Inspect the current purpose"):
        record(reviewer, review.pk, **values(case, review, "follow_up"))
    _, second = record(
        reviewer, review.pk, **values(case, review, history_before=first["next_history_before"])
    )
    assert len(second["follow_up_history"]) == 1 and second["next_history_before"] is None
    newer_reason = "A newer independent operational review still requires a fresh plan"
    record(reviewer, review.pk, **values(case, review, "follow_up", reason=newer_reason))
    _, replayed = record(reviewer, review.pk, **first_values)
    assert replayed == first and newer_reason not in str(replayed)
    review.refresh_from_db()
    assert review.version == 53
    assert RetentionReviewEvent.objects.filter(review=review, operation="inspect").count() == 2


def test_reconciliation_repairs_partial_calendar_without_overwriting_existing_followup(
    request, settings, monkeypatch
):
    case, _, reviewer, _, _, _, plan, _ = prepared(request, settings, monkeypatch)
    retained = RetentionReview.objects.filter(plan=plan).first()
    record(reviewer, retained.pk, **values(case, retained))
    record(reviewer, retained.pk, **values(case, retained, "follow_up"))
    retained.refresh_from_db()
    original = (
        retained.next_review_on,
        retained.version,
        retained.responsible_id,
        retained.last_reviewed_at,
    )
    RetentionReview.objects.filter(plan=plan).exclude(pk=retained.pk).first().delete()
    assert reconcile_retention_reviews() == {"plans": 1, "scheduled": 1, "failed": 0}
    retained.refresh_from_db()
    assert (
        retained.next_review_on,
        retained.version,
        retained.responsible_id,
        retained.last_reviewed_at,
    ) == original
    assert RetentionReview.objects.filter(plan=plan).count() == plan.retention_purpose_count
    assert reconcile_retention_reviews() == {"plans": 0, "scheduled": 0, "failed": 0}
