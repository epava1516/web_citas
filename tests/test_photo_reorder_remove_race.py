"""A queued reorder must recheck a photo removed while waiting for its manager lock."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic

import pytest
from django.db import connection, connections, transaction
from django.test import Client
from test_photos import photo_environment, raw_image, scenario, upload  # noqa: F401

from apps.core.verification import locked_manager_person
from apps.listings.models import Revision
from apps.mediafiles import views
from apps.mediafiles.models import Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_reorder_rechecks_photo_removed_while_waiting(
    request, photo_environment, monkeypatch, language, record_property  # noqa: F811 - pytest fixture binding
):
    assert connection.vendor == "postgresql"
    user, person, manager = request.getfixturevalue("scenario")
    assert manager.post(f"/{language}/person/{person.pk}/listing/start/").status_code == 302
    revision = Revision.objects.get()
    for seed in (9011, 9012):
        assert upload(manager, revision, raw_image(seed)).status_code == 302
    photos = list(revision.photos.order_by("position", "created_at"))
    assert len(photos) == 2
    target, peer = photos[-1], photos[0]
    before_positions = dict(Photo.objects.filter(revision=revision).values_list("pk", "position"))
    revision.refresh_from_db()
    before_version = revision.edit_version
    reorder_client = Client(raise_request_exception=False)
    reorder_client.force_login(user)
    waiting_pid, pause = Queue(), Event()
    original = views.locked_manager_person

    def observed(*args, **kwargs):
        # Pass through the real guard; only expose the backend identity to prove blocking.
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            waiting_pid.put(cursor.fetchone()[0])
        return original(*args, **kwargs)

    def reorder():
        connections.close_all()
        try:
            return reorder_client.post(
                f"/{language}/photos/{target.pk}/reorder/", {"direction": "up"}
            )
        finally:
            connections.close_all()

    with monkeypatch.context() as patch:
        patch.setattr(views, "locked_manager_person", observed)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with transaction.atomic():
                locked_manager_person(user, person.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder_pid = cursor.fetchone()[0]
                pending = pool.submit(reorder)
                pid = waiting_pid.get(timeout=5)
                deadline, blockers = monotonic() + 10, []
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_blocking_pids(%s)", [pid])
                        blockers = cursor.fetchone()[0]
                    if holder_pid in blockers:
                        break
                    pause.wait(.01)
                assert holder_pid in blockers and not pending.done()
                assert manager.post(f"/{language}/photos/{target.pk}/remove/").status_code == 302
            response = pending.result(timeout=15)
    target.refresh_from_db()
    peer.refresh_from_db()
    revision.refresh_from_db()
    assert target.removed_at is not None and peer.removed_at is None
    assert revision.edit_version == before_version + 1  # Removal only; failed reorder adds no edit.
    assert dict(Photo.objects.filter(revision=revision).values_list("pk", "position")) == before_positions
    assert response.status_code == 404 and not response.streaming
    assert manager.get(f"/{language}/photos/{target.pk}/private/").status_code == 404
    record_property("n07_reorder_remove_race", {
        "language": language, "actual_postgresql_blocking": True,
        "removed_after_initial_lookup": True, "reorder_status": response.status_code,
        "removal_only_version_increment": True, "positions_preserved": True,
        "guard_observer": "Pass-through PID observation only; actual authority and mutations unchanged",
    })
