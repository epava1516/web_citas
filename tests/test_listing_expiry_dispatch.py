"""Periodic expiry selects eligible rows and preserves other lifecycle states."""
from datetime import timedelta

import pytest
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings.models import LifecycleAction, Listing
from apps.listings.tasks import expire_listings

pytestmark = pytest.mark.django_db(transaction=True)


def test_periodic_expiry_preserves_unexpired_and_paused_and_is_idempotent(request):
    request.getfixturevalue('directory')
    listings = list(Listing.objects.order_by('pk')[:3])
    assert len(listings) == 3
    now = timezone.now()
    Listing.objects.filter(status='published').update(expires_at=now + timedelta(days=1))
    due, future, paused = listings
    Listing.objects.filter(pk=due.pk).update(status='published', expires_at=now - timedelta(days=1))
    Listing.objects.filter(pk=future.pk).update(status='published', expires_at=now + timedelta(days=1))
    Listing.objects.filter(pk=paused.pk).update(status='paused', expires_at=now - timedelta(days=1))
    before = dict(Listing.objects.values_list('pk', 'lifecycle_version'))
    actions_before = LifecycleAction.objects.count()
    assert expire_listings() == 1
    due.refresh_from_db()
    future.refresh_from_db()
    paused.refresh_from_db()
    assert due.status == 'expired' and due.lifecycle_version == before[due.pk] + 1
    assert future.status == 'published' and future.lifecycle_version == before[future.pk]
    assert paused.status == 'paused' and paused.lifecycle_version == before[paused.pk]
    action = LifecycleAction.objects.get(listing=due, operation='expire')
    assert action.actor_id is None
    assert action.approved_revision_id == due.approved_revision_id
    assert action.expected_version == before[due.pk]
    assert action.previous_status == 'published' and action.resulting_status == 'expired'
    assert LifecycleAction.objects.count() == actions_before + 1
    assert expire_listings() == 0
    assert LifecycleAction.objects.count() == actions_before + 1
