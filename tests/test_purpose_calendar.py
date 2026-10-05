"""Calendar follows up operational dates without changing processing authority."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from test_processing_plans import REASON
from test_purpose_release import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import PurposeCalendarEvent
from apps.safety.purpose_calendar import record

pytestmark = pytest.mark.django_db(transaction=True)


def setup_calendar(request, settings, monkeypatch):
    result = prepared(request, settings, monkeypatch)
    reviewer = result[2]
    reviewer.user_permissions.add(Permission.objects.get(codename="review_purpose_calendar"))
    return (*result[:2], User.objects.get(pk=reviewer.pk), *result[3:])


def test_follow_up_preserves_authority_and_replay_snapshot(request, settings, monkeypatch):
    case, _, reviewer, _, subject, favorite, restriction = setup_calendar(
        request, settings, monkeypatch
    )
    before = (
        case.version,
        case.scope_status,
        case.initial_due_at,
        case.status,
        restriction.review_on,
    )
    next_date = timezone.localdate() + timedelta(days=7)
    key = uuid4()
    args = (
        reviewer,
        restriction.pk,
        key,
        restriction.version,
        case.version,
        "follow_up",
        REASON,
        next_date,
    )
    event, snapshot = record(*args)
    replay, original = record(*args)
    assert event.pk == replay.pk and snapshot == original
    restriction.refresh_from_db()
    case.refresh_from_db()
    assert restriction.active and restriction.version == 2 and restriction.review_on == next_date
    assert restriction.initial_review_on == before[-1]
    assert (case.version, case.scope_status, case.initial_due_at, case.status) == before[:-1]
    own = Client()
    own.force_login(subject)
    assert own.get(reverse("favorites")).status_code == 409
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()
    _, history = record(reviewer, restriction.pk, uuid4(), 2, case.version, "inspect", REASON)
    assert history["history"][0]["reason"] == REASON
    assert PurposeCalendarEvent.objects.count() == 2


def test_invalid_date_version_and_original_executor_do_not_change_measure(
    request, settings, monkeypatch
):
    case, creator, reviewer, _, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    for next_date in [timezone.localdate(), timezone.localdate() + timedelta(days=91)]:
        with pytest.raises(ValidationError):
            record(
                reviewer,
                restriction.pk,
                uuid4(),
                restriction.version,
                case.version,
                "follow_up",
                REASON,
                next_date,
            )
    with pytest.raises(ValidationError):
        record(reviewer, restriction.pk, uuid4(), 999, case.version, "inspect", REASON)
    creator.user_permissions.add(Permission.objects.get(codename="review_purpose_calendar"))
    with pytest.raises(PermissionDenied):
        record(
            User.objects.get(pk=creator.pk),
            restriction.pk,
            uuid4(),
            restriction.version,
            case.version,
            "inspect",
            REASON,
        )
    assert not PurposeCalendarEvent.objects.exists()
    restriction.refresh_from_db()
    assert restriction.active and restriction.version == 1


def test_http_follow_up_history_is_hidden_on_get_and_audited_on_post(
    request, settings, monkeypatch
):
    case, _, reviewer, client, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    path = reverse("purpose_calendar_detail", kwargs={"restriction_id": restriction.pk})
    assert client.get(path).status_code == 200
    reason = "Private synthetic operational follow-up after independent assessment"
    response = client.post(
        path,
        {
            "key": uuid4(),
            "version": restriction.version,
            "case_version": case.version,
            "operation": "follow_up",
            "reason": reason,
            "next_review_on": timezone.localdate() + timedelta(days=7),
        },
    )
    assert response.status_code == 200 and response.context["recorded"]
    response = client.get(path)
    assert (
        reason not in response.content.decode() and response["Cache-Control"] == "private, no-store"
    )
    restriction.refresh_from_db()
    response = client.post(
        path,
        {
            "key": uuid4(),
            "version": restriction.version,
            "case_version": case.version,
            "operation": "inspect",
            "reason": REASON,
        },
    )
    assert response.status_code == 200 and reason in response.content.decode()
    assert PurposeCalendarEvent.objects.count() == 2
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_purpose_calendar"))
    assert client.get(path).status_code == 403


def test_corrupt_replay_snapshot_is_rejected_without_mutation(request, settings, monkeypatch):
    case, _, reviewer, _, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    args = (reviewer, restriction.pk, uuid4(), restriction.version, case.version, "inspect", REASON)
    event, _ = record(*args)
    PurposeCalendarEvent.objects.filter(pk=event.pk).update(encrypted_snapshot="invalid-ciphertext")
    with pytest.raises(ValidationError, match="Calendar record unavailable"):
        record(*args)
    restriction.refresh_from_db()
    assert restriction.version == 1 and restriction.active
    assert PurposeCalendarEvent.objects.count() == 1


def test_global_queue_filters_current_authority_and_invalid_cursor(request, settings, monkeypatch):
    case, creator, _, client, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    path = reverse("purpose_calendar_queue")
    response = client.get(path, {"attention": "all"})
    assert response.status_code == 200
    assert [row.pk for row in response.context["restrictions"]] == [restriction.pk]
    assert REASON not in response.content.decode()
    assert response["Cache-Control"] == "private, no-store"
    assert client.get(path, {"attention": "all", "mode": "cease"}).context["restrictions"] == []
    assert client.get(path, {"attention": "unknown"}).status_code == 400
    assert client.get(path, {"attention": "all", "cursor": "invalid-ciphertext"}).status_code == 400
    assert client.post(path).status_code == 405
    creator.user_permissions.add(Permission.objects.get(codename="review_purpose_calendar"))
    other = Client()
    other.force_login(creator)
    session = other.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    response = other.get(path, {"attention": "all"})
    assert response.status_code == 200 and response.context["restrictions"] == []


def test_encrypted_cursor_advances_past_a_fully_excluded_batch(request, settings, monkeypatch):
    from apps.safety.models import ProcessingExecution, PurposeRestriction, RightsAction

    case, _, reviewer, client, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    # Synthetic pre-existing measures exercise queue pagination, not their creation workflow.
    original = restriction.execution
    action = RightsAction.objects.create(
        key=uuid4(),
        request=case,
        actor=reviewer,
        expected_version=case.version,
        operation="processing_execute",
        payload_digest=original.action.payload_digest,
        encrypted_reason=original.action.encrypted_reason,
    )
    execution = ProcessingExecution.objects.create(
        action=action,
        review=original.review,
        proof=original.proof,
        account_subject=original.account_subject,
        source_digest=original.source_digest,
        encrypted_result=original.encrypted_result,
    )
    day = timezone.localdate()
    PurposeRestriction.objects.bulk_create(
        [
            PurposeRestriction(
                execution=execution,
                subject_id=restriction.subject_id,
                purpose=f"synthetic-calendar-{index}",
                mode="restrict",
                review_on=day,
                initial_review_on=day,
            )
            for index in range(100)
        ]
    )
    PurposeRestriction.objects.filter(pk=restriction.pk).update(review_on=day + timedelta(days=1))
    path = reverse("purpose_calendar_queue")
    response = client.get(path, {"attention": "all"})
    assert response.status_code == 200 and response.context["restrictions"] == []
    cursor = response.context["next_cursor"]
    assert cursor and "synthetic-calendar" not in cursor
    response = client.get(path, {"attention": "all", "cursor": cursor})
    assert [row.pk for row in response.context["restrictions"]] == [restriction.pk]
    assert response.context["next_cursor"] is None
    assert client.get(path, {"attention": "soon", "cursor": cursor}).status_code == 400
    reviewer.user_permissions.remove(Permission.objects.get(codename="review_purpose_calendar"))
    assert client.get(path, {"attention": "all", "cursor": cursor}).status_code == 403


def test_history_pages_cover_all_follow_ups_and_replay_stays_historical(
    request, settings, monkeypatch
):
    case, _, reviewer, _, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    next_date = timezone.localdate() + timedelta(days=7)
    followups = []
    for index in range(52):
        event, _ = record(
            reviewer,
            restriction.pk,
            uuid4(),
            index + 1,
            case.version,
            "follow_up",
            f"Synthetic independent operational follow-up number {index:02}",
            next_date,
        )
        followups.append(event.pk)
    key = uuid4()
    args = (reviewer, restriction.pk, key, 53, case.version, "inspect", REASON)
    reading, first = record(*args)
    assert len(first["history"]) == 50 and first["next_cursor"]
    _, second = record(
        reviewer,
        restriction.pk,
        uuid4(),
        53,
        case.version,
        "inspect",
        REASON,
        history_before=first["next_cursor"],
    )
    assert len(second["history"]) == 2 and second["next_cursor"] is None
    ids = [row["id"] for row in first["history"] + second["history"]]
    assert len(set(ids)) == 52 and set(ids) == set(followups)
    before = PurposeCalendarEvent.objects.count()
    with pytest.raises(ValidationError, match="Invalid history cursor"):
        record(
            reviewer,
            restriction.pk,
            uuid4(),
            53,
            case.version,
            "inspect",
            REASON,
            history_before=9223372036854775807,
        )
    assert PurposeCalendarEvent.objects.count() == before
    record(reviewer, restriction.pk, uuid4(), 53, case.version, "follow_up", REASON, next_date)
    replay, snapshot = record(*args)
    assert replay.pk == reading.pk and snapshot == first
    restriction.refresh_from_db()
    assert restriction.version == 54 and restriction.active
    assert PurposeCalendarEvent.objects.count() == before + 1
