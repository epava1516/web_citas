"""Observed PostgreSQL waits exercise follow-up versioning and authority refresh."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from queue import Queue
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, connections, transaction
from django.utils import timezone
from test_photo_reuse_races import observe_blocked
from test_processing_plans import REASON
from test_purpose_calendar import setup_calendar
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import PurposeCalendarEvent, PurposeRestriction
from apps.safety.purpose_calendar import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("scenario", ["replay", "conflict", "revoked", "inactive"])
def test_waiting_follow_ups_are_atomic_and_refresh_authority(
    request, settings, monkeypatch, scenario
):
    case, _, reviewer, _, _, favorite, restriction = setup_calendar(request, settings, monkeypatch)
    original = (case.version, case.scope_status, case.initial_due_at, restriction.review_on)
    first_key = uuid4()
    second_key = uuid4() if scenario == "conflict" else first_key
    next_date = timezone.localdate() + timedelta(days=7)
    pids = Queue()

    def attempt(key):
        connections.close_all()
        try:
            user = User.objects.get(pk=reviewer.pk)
            assert user.has_perm("safety.review_purpose_calendar")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                event, _ = record(
                    user, restriction.pk, key, 1, case.version, "follow_up", REASON, next_date
                )
                return event.pk
            except (PermissionDenied, ValidationError):
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            PurposeRestriction.objects.select_for_update().get(pk=restriction.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt, first_key)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt, second_key)
            observe_blocked(pids.get(timeout=5), holder)
            assert not first.done() and not second.done()
            if scenario == "revoked":
                reviewer.user_permissions.remove(
                    Permission.objects.get(codename="review_purpose_calendar")
                )
            elif scenario == "inactive":
                # Concurrent ledger change tests the inactive guard; no release workflow is simulated.
                PurposeRestriction.objects.filter(pk=restriction.pk).update(active=False)
        results = [first.result(timeout=20), second.result(timeout=20)]
    restriction.refresh_from_db()
    case.refresh_from_db()
    assert (case.version, case.scope_status, case.initial_due_at) == original[:3]
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()
    if scenario in {"revoked", "inactive"}:
        assert results == ["denied", "denied"]
        assert not PurposeCalendarEvent.objects.exists()
        assert restriction.version == 1 and restriction.review_on == original[3]
    else:
        assert PurposeCalendarEvent.objects.count() == 1
        assert (
            restriction.version == 2 and restriction.review_on == next_date and restriction.active
        )
        if scenario == "replay":
            assert results[0] == results[1]
        else:
            assert results.count("denied") == 1


@pytest.mark.parametrize("winner", ["follow_up", "release"])
def test_actual_release_and_calendar_follow_up_observe_each_other_after_wait(
    request, settings, monkeypatch, winner
):
    from django.test import Client
    from test_rights_verification import read

    from apps.safety.models import RightsRequest
    from apps.safety.purpose_release import execute as release
    from apps.safety.purpose_release import inspect, propose
    from apps.safety.rights_verification import receive_event, simulate_event, start

    case, creator, reviewer, client, _, favorite, restriction = setup_calendar(
        request, settings, monkeypatch
    )
    inspect(reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON)
    proposal = propose(
        reviewer, case.pk, restriction.pk, uuid4(), case.version, REASON, "restriction_resolved"
    )
    case.refresh_from_db()
    read(client, case)
    assert (
        Client()
        .post(
            case._receipt_path + f"response/{proposal.response_id}/acknowledge/",
            {"received": "yes"},
        )
        .status_code
        == 302
    )
    proof = start(reviewer, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    verifier = Client()
    verifier.force_login(creator)
    session = verifier.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    read(verifier, case)
    receive_event(creator, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(client, case)
    version = case.version
    next_date = timezone.localdate() + timedelta(days=7)
    pids = Queue()

    def operation(user, kind):
        if kind == "follow_up":
            return record(
                user, restriction.pk, uuid4(), 1, version, "follow_up", REASON, next_date
            )[0].pk
        return release(user, case.pk, restriction.pk, uuid4(), version, proposal.pk, REASON).pk

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                operation(
                    User.objects.get(pk=reviewer.pk),
                    "release" if winner == "follow_up" else "follow_up",
                )
            except ValidationError:
                return "denied"
            return "unexpected execution"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            waiting = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            operation(reviewer, winner)
        assert waiting.result(timeout=20) == "denied"
    restriction.refresh_from_db()
    proposal.refresh_from_db()
    case.refresh_from_db()
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()
    if winner == "follow_up":
        assert restriction.active and restriction.version == 2 and proposal.released_at is None
        assert PurposeCalendarEvent.objects.count() == 1 and case.version == version
    else:
        assert not restriction.active and proposal.released_at and restriction.version == 1
        assert not PurposeCalendarEvent.objects.exists() and case.version == version + 1


def test_changed_case_reference_after_scope_wait_is_denied(request, settings, monkeypatch):
    from apps.safety.models import RightsAction, RightsRequest

    case, _, reviewer, _, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    # Synthetic destination tests scope integrity; it is not a case-transfer workflow.
    destination = RightsRequest.objects.create(
        submission_key=uuid4(),
        receipt_digest="synthetic-other-channel",
        payload_digest=case.payload_digest,
        encrypted_payload=case.encrypted_payload,
        actor=reviewer,
        account_subject_id=case.account_subject_id,
        kind=case.kind,
        status="reviewing",
        received_at=case.received_at,
        initial_due_at=case.initial_due_at,
        receipt_expires_at=case.receipt_expires_at,
    )
    pids = Queue()

    def attempt():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                record(
                    User.objects.get(pk=reviewer.pk),
                    restriction.pk,
                    uuid4(),
                    1,
                    case.version,
                    "follow_up",
                    REASON,
                    timezone.localdate() + timedelta(days=7),
                )
            except PermissionDenied:
                return "denied"
            return "unexpected execution"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(attempt)
            observe_blocked(pids.get(timeout=5), holder)
            RightsAction.objects.filter(pk=restriction.execution.action_id).update(
                request=destination
            )
        assert future.result(timeout=20) == "denied"
    restriction.refresh_from_db()
    assert restriction.version == 1 and restriction.active
    assert not PurposeCalendarEvent.objects.exists()


def test_shared_key_between_measures_keeps_losing_measure_unchanged(request, settings, monkeypatch):
    case, _, reviewer, _, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    # Synthetic second ledger row isolates the cross-measure key invariant.
    other = PurposeRestriction.objects.create(
        execution=restriction.execution,
        subject_id=restriction.subject_id,
        purpose="synthetic-calendar-secondary",
        mode="restrict",
        review_on=restriction.review_on,
        initial_review_on=restriction.review_on,
    )
    key = uuid4()
    pids = Queue()

    def attempt(measure_id):
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                event, _ = record(
                    User.objects.get(pk=reviewer.pk),
                    measure_id,
                    key,
                    1,
                    case.version,
                    "follow_up",
                    REASON,
                    timezone.localdate() + timedelta(days=7),
                )
                return event.pk
            except ValidationError:
                return "denied"
        finally:
            connections.close_all()

    from apps.safety.models import RightsRequest

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            RightsRequest.objects.select_for_update().get(pk=case.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            first = pool.submit(attempt, restriction.pk)
            observe_blocked(pids.get(timeout=5), holder)
            second = pool.submit(attempt, other.pk)
            observe_blocked(pids.get(timeout=5), holder)
        results = [first.result(timeout=20), second.result(timeout=20)]
    assert results.count("denied") == 1 and PurposeCalendarEvent.objects.count() == 1
    restriction.refresh_from_db()
    other.refresh_from_db()
    assert sorted([restriction.version, other.version]) == [1, 2]
    assert restriction.active and other.active
