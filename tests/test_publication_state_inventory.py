"""Check that MOD05 subject-linked derived records enter the rights census."""
import pytest
from test_discovery import directory  # noqa: F401, F811
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState
from apps.safety.erasure_inventory import canonical, source_manifest
from apps.safety.rights import fingerprint

pytestmark = pytest.mark.django_db(transaction=True)


def test_publication_derived_records_are_scoped_and_change_inventory(directory):  # noqa: F811
    while publication_state.refresh(500):
        pass
    listing = Listing.objects.filter(status="published").select_related("person").first()
    assert listing is not None
    assert PublicationState.objects.filter(listing=listing).exists()
    before = source_manifest(listing.person)
    entries = {entry["model"]: entry for entry in before["entries"]}
    assert "listings.PublicationState" in entries, "subject-linked MOD05 state missing from census"
    assert entries["listings.PublicationState"]["count"] == 1
    before_digest = fingerprint(canonical(before))
    state = PublicationState.objects.get(listing=listing)
    PublicationState.objects.filter(listing=listing).update(eligible=not state.eligible)
    assert fingerprint(canonical(source_manifest(listing.person))) != before_digest
    after_state_digest = fingerprint(canonical(source_manifest(listing.person)))
    peer = PublicationState.objects.exclude(listing=listing).first()
    assert peer is not None
    PublicationState.objects.filter(listing_id=peer.listing_id).update(eligible=not peer.eligible)
    assert fingerprint(canonical(source_manifest(listing.person))) == after_state_digest
    assert "listings.PublicationDirty" in entries
    assert entries["listings.PublicationDirty"]["count"] == 0
    Listing.objects.filter(pk=listing.pk).update(status="paused")
    assert PublicationDirty.objects.filter(listing_id=listing.pk).exists()
    after_dirty = source_manifest(listing.person)
    dirty_entries = {entry["model"]: entry for entry in after_dirty["entries"]}
    assert dirty_entries["listings.PublicationDirty"]["count"] == 1
    assert fingerprint(canonical(after_dirty)) != after_state_digest
