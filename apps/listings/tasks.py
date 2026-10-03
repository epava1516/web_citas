from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Listing


def expire_one(listing_id):
    with transaction.atomic():
        listing = Listing.objects.select_for_update(skip_locked=True).filter(pk=listing_id).first()
        now = timezone.now()
        if (
            not listing
            or listing.status != "published"
            or not listing.expires_at
            or listing.expires_at > now
        ):
            return False
        listing.status = "expired"
        listing.available_until = None
        listing.lifecycle_version += 1
        listing.save(update_fields=["status", "available_until", "lifecycle_version"])
        return True


@shared_task
def expire_listings():
    ids = list(
        Listing.objects.filter(status="published", expires_at__lte=timezone.now())
        .order_by("pk")
        .values_list("pk", flat=True)[:1000]
    )
    return sum(expire_one(listing_id) for listing_id in ids)
