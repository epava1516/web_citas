from celery import shared_task
from django.utils import timezone

from .promotion_exposure import bump_one, enabled
from .promotion_order_models import PromotionEntitlement


@shared_task
def bump_promotions():
    if not enabled():
        return 0
    now = timezone.now()
    ids = list(
        PromotionEntitlement.objects.filter(
            order__kind="autobump", starts_at__lte=now, ends_at__gt=now, suspended_at__isnull=True
        )
        .order_by("last_bumped_at", "pk")
        .values_list("pk", flat=True)[:100]
    )
    return sum(bump_one(pk, now=now) for pk in ids)
