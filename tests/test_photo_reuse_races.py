"""Real PostgreSQL blocking; synthetic review authority, actual scoped media redaction."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.db import connection, connections, transaction
from django.test import Client
from test_erasure_execution import payload
from test_photo_disposition_authority import ledger
from test_reports import directory, photo_environment  # noqa: F401
from test_shared_media_redaction import prepared

from apps.core.models import User
from apps.listings.models import Revision
from apps.mediafiles.models import Photo
from apps.safety import models, photo_reintroduction_views
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record
from apps.safety.photo_reintroduction import detect
from apps.safety.photo_reintroduction_review import decide, inspect
from apps.safety.rights_scope import locked_case

pytestmark = pytest.mark.django_db(transaction=True)


def setup_review(request, settings, monkeypatch):
    case, actor, _, person, plan, shared, peer_photo, _ = prepared(request, settings, monkeypatch)
    original = person.listing.approved_revision.photos.filter(blob=shared).first()
    authority = ledger(person)
    authority.proof.status = "passed"  # Synthetic review authority; no provider claim.
    authority.proof.save(update_fields=["status"])
    models.RightsRectificationPhotoDisposition.objects.create(
        execution=authority,
        source_photo=original,
        blob=shared,
        outcome="withdrawn",
    )
    revision = Revision.objects.create(
        listing=person.listing, manager_version=person.manager_version, status="draft"
    )
    photo = Photo.objects.create(revision=revision, blob=shared)
    detect(photo.pk)
    candidate = models.RightsPhotoReintroduction.objects.get(photo=photo)
    actor.user_permissions.add(Permission.objects.get(codename="review_photo_reintroduction"))
    actor = User.objects.get(pk=actor.pk)
    read = inspect(
        actor, candidate.pk, uuid4(), 1, "Independently inspect current protected reuse evidence"
    )
    return case, actor, person, plan, shared, peer_photo, authority, candidate, read


def observe_blocked(pid, holder_pid):
    pause = Event()
    deadline = monotonic() + 5
    while monotonic() < deadline:
        with connection.cursor() as cursor:
            cursor.execute(
                """WITH RECURSIVE blockers(pid, visited) AS (
                    SELECT blocker, ARRAY[%s, blocker]
                    FROM unnest(pg_blocking_pids(%s)) AS blocker
                    UNION ALL
                    SELECT blocker, visited || blocker FROM blockers
                    CROSS JOIN LATERAL unnest(pg_blocking_pids(blockers.pid)) AS blocker
                    WHERE NOT blocker = ANY(visited)
                ) SELECT EXISTS(SELECT 1 FROM blockers WHERE pid = %s)""",
                [pid, pid, holder_pid],
            )
            if cursor.fetchone()[0]:
                return
        pause.wait(0.01)
    pytest.fail("PostgreSQL holder was not observed blocking the actual request")


def test_waiting_scoped_image_rechecks_after_actual_media_redaction(request, settings, monkeypatch):
    case, actor, person, plan, shared, peer, authority, candidate, read = setup_review(
        request, settings, monkeypatch
    )
    inventory = prepare(
        actor,
        case.pk,
        uuid4(),
        case.version,
        "Review new private reuse dependencies before media redaction",
    )
    plan = record(
        actor,
        case.pk,
        inventory.pk,
        uuid4(),
        case.version,
        unseal(plan.encrypted_decisions)["decisions"],
    )
    client = Client()
    client.force_login(actor)
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    path = f"/en/moderation/photo-reuse/{candidate.pk}/reads/{read.pk}/uploaded/"
    first = client.get(path)
    assert first.status_code == 200 and b"".join(first.streaming_content)
    first.close()
    pids = Queue()
    original_allowed = photo_reintroduction_views.allowed

    def observed(request):
        original_allowed(request)
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            pids.put(cursor.fetchone()[0])

    def reading():
        connections.close_all()
        try:
            return client.get(path)
        finally:
            connections.close_all()

    with monkeypatch.context() as patch:
        patch.setattr(photo_reintroduction_views, "allowed", observed)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                locked_case(
                    authority.action.request_id, lock_listing=True, allow_version_change=True
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                future = pool.submit(reading)
                observe_blocked(pids.get(timeout=5), holder)
                assert not future.done()
                execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
            response = future.result(timeout=10)
    assert response.status_code == 404 and not response.streaming
    peer.refresh_from_db()
    assert peer.blob_id == shared.pk and shared.derivative.storage.exists(shared.derivative.name)


def test_two_independent_decisions_block_then_resolve_one_version(request, settings, monkeypatch):
    from django.core.exceptions import ValidationError

    _, actor, _, _, _, _, authority, candidate, first_read = setup_review(
        request, settings, monkeypatch
    )
    second = User.objects.create_user(
        username="second-independent-reuse-reviewer", mfa_enabled=True
    )
    second.user_permissions.add(Permission.objects.get(codename="review_photo_reintroduction"))
    second_read = inspect(
        second,
        candidate.pk,
        uuid4(),
        1,
        "Independently inspect current evidence before concurrent decision",
    )
    pids = Queue()

    def deciding(actor_id, read_id, outcome):
        connections.close_all()
        try:
            user = User.objects.get(pk=actor_id)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                decide(
                    user,
                    candidate.pk,
                    read_id,
                    uuid4(),
                    1,
                    outcome,
                    "Independent current photo authority and evidence assessed",
                    "synthetic-race-ref",
                )
                return "recorded"
            except ValidationError:
                return "changed"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        with transaction.atomic():
            locked_case(authority.action.request_id, lock_listing=True, allow_version_change=True)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            futures = [
                pool.submit(deciding, actor.pk, first_read.pk, "authorize"),
                pool.submit(deciding, second.pk, second_read.pk, "maintain"),
            ]
            for _ in futures:
                observe_blocked(pids.get(timeout=5), holder)
            assert all(not future.done() for future in futures)
        assert sorted(future.result(timeout=10) for future in futures) == ["changed", "recorded"]
    assert candidate.decisions.count() == 1
    candidate.refresh_from_db()
    assert candidate.review_version == 2


def test_waiting_inspection_rechecks_original_proof_after_scope_lock(
    request, settings, monkeypatch
):
    from django.core.exceptions import PermissionDenied

    _, actor, _, _, _, _, authority, candidate, _ = setup_review(request, settings, monkeypatch)
    pids = Queue()
    audit_key = uuid4()

    def inspecting():
        connections.close_all()
        try:
            user = User.objects.get(pk=actor.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])
            try:
                inspect(
                    user,
                    candidate.pk,
                    audit_key,
                    1,
                    "Inspect current evidence after waiting for the authority lock",
                )
                return "recorded"
            except PermissionDenied:
                return "denied"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            locked_case(authority.action.request_id, lock_listing=True, allow_version_change=True)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(inspecting)
            observe_blocked(pids.get(timeout=5), holder)
            assert not future.done()
            # Synthetic authority mutation under the same scope lock as proof writers.
            models.RightsProof.objects.filter(pk=authority.proof_id).update(status="pending")
        assert future.result(timeout=10) == "denied"
    assert not models.RightsPhotoReintroductionRead.objects.filter(key=audit_key).exists()
