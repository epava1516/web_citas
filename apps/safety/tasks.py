from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import RightsExport


@shared_task
def deliver_safety_notices():
    from .notice_delivery import process_outbox

    return process_outbox()


@shared_task
def purge_expired_exports():
    """Remove transient copy content only; keep audit and source data separate."""
    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsExport.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:1000]
        )
        return RightsExport.objects.filter(pk__in=ids).update(encrypted_payload="", purged_at=now)
