"""Synthetic sponsorship and auto bump preserve public eligibility and editorial state."""

import hashlib
from datetime import UTC, datetime

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core.agencies import can_manage_person
from apps.core.models import Agency, Person, User
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible

from .promotion_order_models import PromotionBumpExecution, PromotionEntitlement


def enabled():
    return not settings.PRODUCTION and settings.PROMOTION_TEST_MODE and not settings.RECOVERY_MODE


def eligible(entitlement, listing, now):
    order = entitlement.order
    buyer = User.objects.get(pk=order.buyer_id)
    return bool(
        enabled()
        and order.synthetic
        and order.status == "paid"
        and entitlement.suspended_at is None
        and entitlement.starts_at <= now < entitlement.ends_at
        and listing.person.manager_version == order.manager_version
        and buyer.is_active
        and buyer.account_erased_at is None
        and can_manage_person(buyer, listing.person)
        and publicly_visible(listing)
    )


def ranked(visible, *, text_search=False, now=None):
    if not enabled() or not visible:
        return visible, {}
    now = now or timezone.now()
    by_listing = {row.pk: row for row in visible}
    promotions = {}
    bumps = {}
    priorities = {"premium": 0, "top": 1, "autobump": 2}
    rows = (
        PromotionEntitlement.objects.filter(
            order__listing_id__in=by_listing,
            starts_at__lte=now,
            ends_at__gt=now,
            suspended_at__isnull=True,
        )
        .select_related("order")
        .order_by("pk")
    )
    for entitlement in rows.iterator(chunk_size=100):
        listing = by_listing[entitlement.order.listing_id]
        if not eligible(entitlement, listing, now):
            continue
        kind = entitlement.order.kind
        if kind not in priorities:
            continue
        if kind == "autobump":
            if entitlement.last_bumped_at:
                bumps[listing.pk] = max(
                    bumps.get(listing.pk, entitlement.last_bumped_at), entitlement.last_bumped_at
                )
        elif listing.pk not in promotions or priorities[kind] < priorities[promotions[listing.pk]]:
            promotions[listing.pk] = kind
    # Same UTC day and listing have the same order on every page; no request-side mutation.
    day = now.astimezone(UTC).date().isoformat()

    def rotation(listing):
        return hashlib.sha256((day + ":" + str(listing.pk)).encode()).digest()

    sponsored = sorted(
        (row for row in visible if row.pk in promotions),
        key=lambda row: (priorities[promotions[row.pk]], rotation(row), str(row.pk)),
    )
    organic = [row for row in visible if row.pk not in promotions]
    if not text_search:
        original = {row.pk: i for i, row in enumerate(organic)}
        organic.sort(
            key=lambda row: (
                0 if row.pk in bumps else 1,
                -bumps[row.pk].timestamp() if row.pk in bumps else 0,
                original[row.pk],
            )
        )
    return sponsored + organic, promotions


@transaction.atomic
def bump_one(entitlement_id, *, now=None):
    if not enabled():
        return False
    now = now or timezone.now()
    initial = PromotionEntitlement.objects.select_related("order__listing__person").get(
        pk=entitlement_id
    )
    person = initial.order.listing.person
    if person.agency_id:
        Agency.objects.select_for_update().get(pk=person.agency_id)
    Person.objects.select_for_update().get(pk=person.pk)
    listing = (
        Listing.objects.select_for_update(of=("self",))
        .select_related("person", "approved_revision")
        .get(pk=initial.order.listing_id)
    )
    entitlement = (
        PromotionEntitlement.objects.select_for_update()
        .select_related("order")
        .get(pk=entitlement_id)
    )
    order = entitlement.order
    if (
        not eligible(entitlement, listing, now)
        or order.kind != "autobump"
        or not order.bump_interval_minutes
        or not order.daily_bump_limit
    ):
        return False
    interval = order.bump_interval_minutes * 60
    bucket = int(now.timestamp()) // interval * interval
    window = datetime.fromtimestamp(bucket, UTC)
    if window < entitlement.starts_at:
        return False
    if PromotionBumpExecution.objects.filter(entitlement=entitlement, window_start=window).exists():
        return False
    day_start = now.astimezone(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    if (
        PromotionBumpExecution.objects.filter(
            entitlement=entitlement, window_start__gte=day_start
        ).count()
        >= order.daily_bump_limit
    ):
        return False
    PromotionBumpExecution.objects.create(entitlement=entitlement, window_start=window)
    entitlement.last_bumped_at = now
    entitlement.save(update_fields=["last_bumped_at"])
    fresh = Listing.objects.select_related("person", "approved_revision").get(pk=listing.pk)
    if not eligible(entitlement, fresh, now):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("Promotion eligibility changed")
    return True
