import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup

from apps.catalog.promotion_exposure import bump_one, ranked
from apps.catalog.promotion_order_models import PromotionBumpExecution
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event

pytestmark = pytest.mark.django_db(transaction=True)


def purchased(request, settings, kind="premium"):
    user, listing, version, credentials = setup(request, settings)
    version.product.kind = kind
    version.product.save(update_fields=["kind"])
    if kind == "autobump":
        version.bump_interval_minutes = 10
        version.daily_bump_limit = 2
        version.save(update_fields=["bump_interval_minutes", "daily_bump_limit"])
    order = create_order(user, listing.pk, version.pk, uuid.uuid4(), **credentials)
    payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid.uuid4())
    receive_event(user, payload, signature, **credentials)
    return user, listing, order.entitlement


def test_sponsorship_uses_filtered_visible_set_and_never_reintroduces_withdrawn_listing(
    request, settings
):
    _, listing, entitlement = purchased(request, settings)
    visible, labels = ranked([listing])
    assert visible == [listing] and labels == {listing.pk: "premium"}
    assert ranked([]) == ([], {})
    client = request.getfixturevalue("directory")
    assert b"Patrocinado" in client.get("/es/").content
    assert b"Sponsored" in client.get("/en/").content
    assert b"Patrocinado" not in client.get("/es/", {"q": "nonexistent-phrase-8293"}).content
    listing.status = "withdrawn"
    listing.save(update_fields=["status"])
    assert not ranked([listing])[1]
    assert b"Patrocinado" not in client.get("/es/").content
    listing.status = "published"
    listing.save(update_fields=["status"])
    entitlement.ends_at = timezone.now() - timedelta(seconds=1)
    entitlement.save(update_fields=["ends_at"])
    assert not ranked([listing])[1]


def test_bump_window_quota_replay_and_editorial_state_preserved(request, settings):
    _, listing, entitlement = purchased(request, settings, "autobump")
    before = (
        listing.published_at,
        listing.lifecycle_version,
        listing.approved_revision_id,
        listing.revisions.count(),
    )
    now = entitlement.starts_at + timedelta(minutes=11)
    assert bump_one(entitlement.pk, now=now)
    assert not bump_one(entitlement.pk, now=now)
    assert bump_one(entitlement.pk, now=now + timedelta(minutes=10))
    assert not bump_one(entitlement.pk, now=now + timedelta(minutes=20))
    assert PromotionBumpExecution.objects.filter(entitlement=entitlement).count() == 2
    listing.refresh_from_db()
    assert (
        listing.published_at,
        listing.lifecycle_version,
        listing.approved_revision_id,
        listing.revisions.count(),
    ) == before
    listing.status = "withdrawn"
    listing.save(update_fields=["status"])
    assert not bump_one(entitlement.pk, now=now + timedelta(days=1))
    settings.RECOVERY_MODE = True
    assert not bump_one(entitlement.pk, now=now)
