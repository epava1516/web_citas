"""Publication refresh and a domain writer must finish without a lock cycle."""

from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event

import pytest
from django.db import connection, connections, transaction
from test_discovery import directory  # noqa: F401
from test_photo_reuse_races import observe_blocked
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState

pytestmark = pytest.mark.django_db(transaction=True)


def test_refresh_insert_and_locked_listing_writer_finish_without_deadlock(request, monkeypatch):
    request.getfixturevalue("directory")
    from apps.listings.tasks import refresh_publication_state

    monkeypatch.setattr(refresh_publication_state, "delay", lambda: None)
    while publication_state.refresh(500):
        pass
    listing = Listing.objects.filter(status="published", approved_revision__isnull=False).first()
    assert listing is not None
    # Force a fresh state INSERT so deferred FK checking participates at commit.
    PublicationState.objects.filter(listing=listing).delete()
    publication_state.mark([listing.pk])
    stored, release = Event(), Event()
    refresh_pid, writer_pid = Queue(), Queue()
    original_store = publication_state.store

    def paused_store(states):
        original_store(states)
        stored.set()
        assert release.wait(15), "Observer did not release the refresh transaction"

    monkeypatch.setattr(publication_state, "store", paused_store)

    def refresh():
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                refresh_pid.put(cursor.fetchone()[0])
            return publication_state.refresh(1)
        finally:
            connections.close_all()

    def write():
        try:
            assert stored.wait(15), "Refresh did not reach its state INSERT"
            with transaction.atomic():
                Listing.objects.select_for_update().get(pk=listing.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    writer_pid.put(cursor.fetchone()[0])
                publication_state.mark([listing.pk])
            return True
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        refreshing = executor.submit(refresh)
        writing = executor.submit(write)
        try:
            # Inspect precisely these two synthetic participants before release.
            observe_blocked(writer_pid.get(timeout=15), refresh_pid.get(timeout=15))
        finally:
            release.set()
        assert refreshing.result(timeout=30) == 1
        assert writing.result(timeout=30)
    assert PublicationDirty.objects.filter(listing=listing).exists()
