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
from test_reports import directory, photo_environment  # noqa: F401
from test_shared_media_redaction import prepared

from apps.core.verification import locked_manager_person
from apps.listings import match_views, moderation_views
from apps.mediafiles import views
from apps.mediafiles.models import Match
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("endpoint", ["manager", "listing", "match"])
def test_waiting_private_read_rechecks_reference_after_actual_rights_redaction(
    request, settings, monkeypatch, endpoint
):
    case, actor, _, person, plan, shared, peer_photo, _ = prepared(request, settings, monkeypatch)
    own_photo = person.listing.approved_revision.photos.filter(blob=shared).first()
    manager = person.agency.owner
    manager.mfa_enabled = True
    manager.save(update_fields=["mfa_enabled"])
    client = Client()
    user = manager
    path = f"/en/photos/{own_photo.pk}/private/"
    if endpoint != "manager":
        actor.user_permissions.add(Permission.objects.get(codename="review_listing"))
        user = actor
        if endpoint == "listing":
            path = f"/en/moderation/photos/{own_photo.pk}/"
        else:
            match, _ = Match.objects.get_or_create(
                photo=own_photo, candidate=peer_photo, defaults={"method": "sha"}
            )
            inventory = prepare(actor, case.pk, uuid4(), case.version, "Review new match reference")
            plan = record(
                actor,
                case.pk,
                inventory.pk,
                uuid4(),
                case.version,
                unseal(plan.encrypted_decisions)["decisions"],
            )
            path = f"/en/moderation/matches/{match.pk}/photo/image/"
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    allowed = client.get(path)
    assert allowed.status_code == 200 and b"".join(allowed.streaming_content)
    allowed.close()
    waiting_pid = Queue()
    pause = Event()
    module = {"manager": views, "listing": moderation_views, "match": match_views}[endpoint]
    name = "locked_manager_person" if endpoint == "manager" else "reviewer_allowed"
    original = getattr(module, name)

    def observed(*args):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            waiting_pid.put(cursor.fetchone()[0])
        return original(*args)

    def reading():
        connections.close_all()
        try:
            return client.get(path)
        finally:
            connections.close_all()

    with monkeypatch.context() as patch:
        patch.setattr(module, name, observed)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                locked_manager_person(manager, person.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder_pid = cursor.fetchone()[0]
                pending = pool.submit(reading)
                pid = waiting_pid.get(timeout=5)
                blockers = []
                deadline = monotonic() + 5
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_blocking_pids(%s)", [pid])
                        blockers = cursor.fetchone()[0]
                    if holder_pid in blockers:
                        break
                    pause.wait(0.01)
                assert holder_pid in blockers and not pending.done()
                execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
            denied = pending.result(timeout=10)
    assert denied.status_code == 404 and not denied.streaming
    own_photo.refresh_from_db()
    assert own_photo.removed_at and own_photo.blob_id != shared.pk
    peer_photo.refresh_from_db()
    assert peer_photo.blob_id == shared.pk and shared.derivative.storage.exists(
        shared.derivative.name
    )
    client.force_login(manager)
    session = client.session
    session["mfa_version"] = manager.mfa_version
    session.save()
    response = client.get(f"/en/photos/{peer_photo.pk}/private/")
    assert response.status_code == 200 and b"".join(response.streaming_content)
    response.close()
