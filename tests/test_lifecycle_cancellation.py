"""Manual availability cancellation keeps publication and exact old retries harmless."""

import json

import pytest
from django.db import connection
from django.test import Client
from test_discovery import directory  # noqa: F401
from test_lifecycle import own, payload
from test_photos import photo_environment  # noqa: F401

from apps.listings.models import LifecycleAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_cancel_availability_preserves_publication_and_old_retry_keeps_new_window(
    request, settings, language, record_property
):
    assert connection.vendor == "postgresql" and not settings.PRODUCTION
    assert connection.settings_dict["NAME"].startswith("test_")
    request.getfixturevalue("directory")
    person, listing, client = own()
    listing.refresh_from_db()
    editorial = (listing.published_at, listing.expires_at, listing.approved_revision_id)
    before_version = listing.lifecycle_version
    before_events = LifecycleAction.objects.filter(listing=listing).count()
    path = f"/{language}/listing/{listing.pk}/manage/"

    def available_count():
        response = Client().get(f"/{language}/", {"available": "on"})
        assert response.status_code == 200
        return response.context["page"].paginator.count

    assert client.post(path, payload(listing, "available")).status_code == 302
    assert available_count() == 1
    cancel = payload(listing, "unavailable")
    response = client.post(path, cancel)
    assert response.status_code == 302 and response["Cache-Control"] == "private, no-store"
    listing.refresh_from_db()
    assert listing.available_until is None and listing.status == "published"
    assert available_count() == 0
    event = LifecycleAction.objects.get(listing=listing, operation="unavailable")
    assert event.actor_id == person.individual_id and event.manager_version == person.manager_version
    assert event.expected_version == cancel["version"] and event.resulting_status == "published"
    assert event.approved_revision_id == editorial[2]
    cancelled_version = listing.lifecycle_version
    cancelled_events = LifecycleAction.objects.filter(listing=listing).count()
    assert client.post(path, cancel).status_code == 302
    listing.refresh_from_db()
    assert listing.lifecycle_version == cancelled_version and listing.available_until is None
    assert LifecycleAction.objects.filter(listing=listing).count() == cancelled_events
    assert client.post(path, payload(listing, "available")).status_code == 302
    listing.refresh_from_db()
    fresh_window, fresh_version = listing.available_until, listing.lifecycle_version
    assert fresh_window is not None and available_count() == 1
    assert client.post(path, cancel).status_code == 302  # An old acknowledged key adds no new effect.
    listing.refresh_from_db()
    assert listing.available_until == fresh_window and listing.lifecycle_version == fresh_version
    assert available_count() == 1
    assert client.post(path, payload(listing, "unavailable")).status_code == 302
    listing.refresh_from_db()
    assert listing.available_until is None and listing.status == "published"
    assert listing.lifecycle_version == before_version + 4 and available_count() == 0
    assert LifecycleAction.objects.filter(listing=listing).count() == before_events + 4
    assert LifecycleAction.objects.filter(listing=listing, operation="unavailable").count() == 2
    assert (listing.published_at, listing.expires_at, listing.approved_revision_id) == editorial
    assert Client().get(f"/{language}/listing/{listing.pk}/").status_code == 200
    record_property("availability_cancellation", json.dumps({
        "language": language, "manual_cancel": True, "exact_retry_no_extra_event": True,
        "old_retry_preserves_new_window": True, "public_availability_counts": [1, 0, 1, 1, 0],
        "editorial_snapshot_unchanged": True, "new_events": 4,
        "scope": "Real PG/Client and native guards; eager fixture, no worker/browser/provider or latency gain claim",
    }, sort_keys=True))
