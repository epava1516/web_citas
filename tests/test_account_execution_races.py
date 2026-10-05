"""Actual concurrent PostgreSQL execution with simulated delivery and identity."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Barrier
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction
from django.test import Client
from test_account_email_confirmation import prepared
from test_photo_reuse_races import observe_blocked
from test_privacy_release import fresh
from test_rectification_review import REASON
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccountEmailConfirmation, RightsRectificationExecution
from apps.safety.rectification_execution import execute, notify
from apps.safety.rectification_review import inspect
from apps.safety.rights_rectification import preview

pytestmark = pytest.mark.django_db(transaction=True)


def execution_ready(request, settings, monkeypatch, *, email=False, mixed=False):
    changes = {"account": {"first_name": "Concurrent synthetic correction"}}
    if email:
        changes["account"]["email"] = "concurrent-destination@example.invalid"
    if mixed:
        changes["title"] = "Corrected listing with confirmed account destination"
    case, actor, staff, person, proposal, path, data, client, receipt = prepared(
        request, settings, monkeypatch, with_receipt=True, changes=changes
    )
    actor.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    actor = User.objects.get(pk=actor.pk)
    if email:
        assert staff.post(path, data).status_code == 302
        token = RightsAccountEmailConfirmation.objects.get()
        destination = Client()
        exchange = destination.get(urlsplit(unseal(token.encrypted_delivery)["url"]).path)
        assert destination.post(exchange["Location"], {"confirmed": "on"}).status_code == 200
    original = proposal.action.actor
    verifier = Client()
    verifier.force_login(original)
    session = verifier.session
    session["mfa_version"] = original.mfa_version
    session.save()
    fresh(case, actor, staff, original, verifier)
    preview(
        actor, case.pk, case.version, "Inspect source before concurrent correction communication"
    )
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Inspect approved changes before concurrent correction communication",
    )
    notice = notify(actor, case.pk, proposal.pk, uuid4(), case.version, REASON)
    assert (
        client.post(
            receipt + f"response/{notice.response_id}/acknowledge/", {"received": "yes"}
        ).status_code
        == 302
    )
    fresh(case, actor, staff, original, verifier)
    preview(actor, case.pk, case.version, "Inspect source before concurrent correction execution")
    inspect(
        actor,
        case.pk,
        proposal.pk,
        case.version,
        "Inspect received approved changes before concurrent execution",
    )
    return case, actor, person, proposal


def test_two_simultaneous_executors_apply_one_correction_and_replay(request, settings, monkeypatch):
    case, actor, person, proposal = execution_ready(request, settings, monkeypatch)
    key, version = uuid4(), case.version
    before_rights = person.rights_version
    barrier = Barrier(2)

    def applying():
        connections.close_all()
        try:
            reviewer = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=10)
            return execute(reviewer, case.pk, proposal.pk, key, version, REASON).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(applying), pool.submit(applying)
        first_id, second_id = first.result(timeout=20), second.result(timeout=20)
    person.refresh_from_db()
    assert first_id == second_id
    assert RightsRectificationExecution.objects.count() == 1
    assert person.rights_version == before_rights + 1
    assert person.subject.first_name == "Concurrent synthetic correction"


def test_email_reserved_during_unique_index_wait_rolls_back_entire_execution(
    request, settings, monkeypatch
):
    case, actor, person, proposal = execution_ready(request, settings, monkeypatch, email=True)
    token = RightsAccountEmailConfirmation.objects.get()
    other = User.objects.create_user(
        username="synthetic-competing-account", email="other-race@example.invalid"
    )
    before = person.subject.email, person.subject.first_name, person.subject.session_version
    rights_version = person.rights_version
    responses = case.responses.count()
    pids = Queue()
    key, version = uuid4(), case.version

    def applying():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                execute(User.objects.get(pk=actor.pk), case.pk, proposal.pk, key, version, REASON)
            except ValidationError:
                return "conflict"
            return "applied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            User.objects.filter(pk=other.pk).update(email="CONCURRENT-DESTINATION@example.invalid")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(applying)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
        assert future.result(timeout=10) == "conflict"
    person.refresh_from_db()
    person.subject.refresh_from_db()
    token.refresh_from_db()
    case.refresh_from_db()
    assert (
        person.subject.email,
        person.subject.first_name,
        person.subject.session_version,
    ) == before
    assert person.rights_version == rights_version
    assert case.version == version and case.responses.count() == responses
    assert token.consumed_at is None and token.confirmed_at is not None
    assert not RightsRectificationExecution.objects.exists()
    assert not case.actions.filter(key=key).exists()


def test_email_and_listing_correction_share_atomic_execution(request, settings, monkeypatch):
    case, actor, person, proposal = execution_ready(
        request, settings, monkeypatch, email=True, mixed=True
    )
    listing = person.listing
    approved = listing.approved_revision
    before_title = approved.title
    before_session = person.subject.session_version
    before_count = listing.revisions.count()
    result = execute(actor, case.pk, proposal.pk, uuid4(), case.version, REASON)
    person.subject.refresh_from_db()
    listing.refresh_from_db()
    approved.refresh_from_db()
    token = RightsAccountEmailConfirmation.objects.get()
    assert person.subject.email == "concurrent-destination@example.invalid"
    assert person.subject.session_version == before_session + 1
    assert token.consumed_at and person.subject.email_verified_at == token.confirmed_at
    assert result.corrected_revision.title == "Corrected listing with confirmed account destination"
    assert result.corrected_revision.status == "draft"
    assert result.corrected_revision.publisher_acceptance_id is None
    assert listing.status == "paused" and listing.revisions.count() == before_count + 1
    assert listing.approved_revision_id == approved.pk and approved.title == before_title


def test_expired_delivery_cleanup_rechecks_expiry_after_observed_user_wait(
    request, settings, monkeypatch
):
    from datetime import timedelta

    from django.utils import timezone

    from apps.safety.account_email_confirmation import purge_expired_delivery

    _, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    original_content = token.encrypted_delivery
    RightsAccountEmailConfirmation.objects.filter(pk=token.pk).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    pids = Queue()

    def purging():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            return purge_expired_delivery()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            User.objects.select_for_update().get(pk=person.subject_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(purging)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            RightsAccountEmailConfirmation.objects.filter(pk=token.pk).update(
                expires_at=timezone.now() + timedelta(hours=1)
            )
        assert future.result(timeout=10) == 0
    token.refresh_from_db()
    assert token.encrypted_delivery == original_content
    assert token.confirmed_at is None and token.consumed_at is None


def test_execution_rechecks_scoped_proof_after_observed_user_wait(request, settings, monkeypatch):
    case, actor, person, proposal = execution_ready(request, settings, monkeypatch)
    proof = case.proofs.order_by("-created_at", "-pk").first()
    pids = Queue()
    key, version = uuid4(), case.version
    before_name = person.subject.first_name

    def applying():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                execute(User.objects.get(pk=actor.pk), case.pk, proposal.pk, key, version, REASON)
            except ValidationError:
                return "denied"
            return "applied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            User.objects.select_for_update().get(pk=person.subject_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(applying)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            type(proof).objects.filter(pk=proof.pk).update(status="pending")
        assert future.result(timeout=10) == "denied"
    person.subject.refresh_from_db()
    assert person.subject.first_name == before_name
    assert not RightsRectificationExecution.objects.exists()
