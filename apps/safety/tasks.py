from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import RightsExport, RightsExportImage


@shared_task
def deliver_safety_notices():
    from .notice_delivery import process_outbox

    return process_outbox()


@shared_task
def reconcile_urgent_report_alerts():
    from .models import Report, UrgentReportAlert

    with transaction.atomic():
        reports = list(
            Report.objects.select_for_update(skip_locked=True, of=("self",))
            .filter(priority=0, urgent_alert__isnull=True)
            .order_by("created_at", "pk")[:100]
        )
        for report in reports:
            UrgentReportAlert.objects.get_or_create(report=report)
        return {"reconciled": len(reports)}


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
        RightsExportImage.objects.filter(export_id__in=ids).update(encrypted_content="")
        return RightsExport.objects.filter(pk__in=ids).update(encrypted_payload="", purged_at=now)
