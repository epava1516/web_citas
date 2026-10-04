from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic

import pytest
from django.db import connection, connections, transaction
from django.test import Client
from test_erasure_execution import payload
from test_reports import directory, photo_environment  # noqa: F401
from test_shared_media_redaction import prepared

from apps.core.verification import locked_manager_person
from apps.mediafiles import views
from apps.safety.erasure_execution import execute

pytestmark = pytest.mark.django_db(transaction=True)


def test_waiting_private_read_rechecks_reference_after_actual_rights_redaction(
    request, settings, monkeypatch
):
    case, actor, _, person, plan, shared, peer_photo, _ = prepared(request, settings, monkeypatch)
    own_photo = person.listing.approved_revision.photos.filter(blob=shared).first()
    manager = person.agency.owner
    manager.mfa_enabled = True
    manager.save(update_fields=["mfa_enabled"])
    client = Client()
    client.force_login(manager)
    session = client.session
    session["mfa_version"] = manager.mfa_version
    session.save()
    path = f"/en/photos/{own_photo.pk}/private/"
    allowed = client.get(path)
    assert allowed.status_code == 200 and b"".join(allowed.streaming_content)
    allowed.close()
    waiting_pid = Queue()
    pause = Event()
    original = views.locked_manager_person

    def observed(user, person_id):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            waiting_pid.put(cursor.fetchone()[0])
        return original(user, person_id)

    def reading():
        connections.close_all()
        try:
            return client.get(path)
        finally:
            connections.close_all()

    with monkeypatch.context() as patch:
        patch.setattr(views, "locked_manager_person", observed)
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
    response = client.get(f"/en/photos/{peer_photo.pk}/private/")
    assert response.status_code == 200 and b"".join(response.streaming_content)
    response.close()
