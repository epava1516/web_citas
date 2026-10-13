"""Publication refresh must defer a batch whose FK references are locked."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.db import connections, transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("reference", ["listing", "revision"])
def test_locked_reference_defers_refresh_without_losing_dirty_generation(request, monkeypatch, reference):
    request.getfixturevalue("directory")
    from apps.listings.tasks import refresh_publication_state

    monkeypatch.setattr(refresh_publication_state, "delay", lambda: None)
    while publication_state.refresh(500):
        pass
    listing = Listing.objects.filter(status="published", approved_revision__isnull=False).first()
    assert listing is not None
    PublicationState.objects.filter(listing=listing).delete()
    publication_state.mark([listing.pk])
    generation = PublicationDirty.objects.get(listing_id=listing.pk).generation
    locked, refreshed = Event(), Event()

    def write():
        try:
            with transaction.atomic():
                model, pk = (Listing, listing.pk) if reference == "listing" else (Revision, listing.approved_revision_id)
                model.objects.select_for_update().get(pk=pk)
                locked.set()
                assert refreshed.wait(10), "Refresh waited for a reference while holding dirty"
                publication_state.mark([listing.pk])
            return True
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as executor:
        writing = executor.submit(write)
        try:
            assert locked.wait(10)
            assert publication_state.refresh(1) == 0
            assert PublicationDirty.objects.get(listing_id=listing.pk).generation == generation
            assert not PublicationState.objects.filter(listing=listing).exists()
        finally:
            refreshed.set()
        assert writing.result(timeout=15)
    assert PublicationDirty.objects.get(listing_id=listing.pk).generation > generation
    assert publication_state.refresh(1) == 1
    assert not PublicationDirty.objects.filter(listing_id=listing.pk).exists()
    assert PublicationState.objects.filter(listing=listing).exists()
