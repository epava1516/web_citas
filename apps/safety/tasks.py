from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import RightsExport, RightsExportImage, RightsExportPart


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
        from .rights_object_content import purge_export_objects

        purge_export_objects(RightsExport.objects.filter(pk__in=ids))
        RightsExportImage.objects.filter(export_id__in=ids).update(encrypted_content="")
        RightsExportPart.objects.filter(export_id__in=ids).update(encrypted_content="")
        return RightsExport.objects.filter(pk__in=ids).update(encrypted_payload="", purged_at=now)


@shared_task
def purge_expired_account_confirmation_delivery():
    from .account_email_confirmation import purge_expired_delivery

    return purge_expired_delivery()


@shared_task
def reconcile_retention_reviews():
    from .retention_reviews import reconcile

    return reconcile()


@shared_task
def purge_expired_copy_page_reviews():
    """Clear temporary reviewed content; preserve scoped minimal decision metadata."""
    from .models import RightsCopyPageReview

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsCopyPageReview.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsCopyPageReview.objects.filter(pk__in=ids).update(
            encrypted_entries="", purged_at=now
        )


@shared_task
def purge_expired_copy_information():
    """Empty temporary information drafts, preserving minimal version metadata."""
    from .models import RightsCopyInformation

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsCopyInformation.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsCopyInformation.objects.filter(pk__in=ids).update(
            encrypted_information="", purged_at=now
        )


@shared_task
def purge_expired_portability_assessments():
    """Remove expired draft bodies in bounded batches while preserving audit links."""
    from .models import RightsPortabilityAssessment

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsPortabilityAssessment.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsPortabilityAssessment.objects.filter(pk__in=ids).update(
            encrypted_assessment="", purged_at=now
        )


@shared_task
def purge_expired_portability_selections():
    """Clear expired selected-field drafts while preserving their audit records."""
    from .models import RightsPortabilitySelection

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsPortabilitySelection.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsPortabilitySelection.objects.filter(pk__in=ids).update(
            encrypted_selection="", purged_at=now
        )


@shared_task
def purge_expired_portability_coverage():
    """Clear transient coverage bodies while preserving signed audit metadata."""
    from .models import RightsPortabilityCoverage

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsPortabilityCoverage.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsPortabilityCoverage.objects.filter(pk__in=ids).update(
            encrypted_coverage="", purged_at=now
        )


@shared_task
def purge_expired_portability_response_drafts():
    """Clear expired final draft text; preserve protected audit references."""
    from .models import RightsPortabilityResponseDraft

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsPortabilityResponseDraft.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsPortabilityResponseDraft.objects.filter(pk__in=ids).update(
            encrypted_response="", purged_at=now
        )


@shared_task
def purge_expired_access_response_drafts():
    """Clear expired final draft text; preserve protected audit references."""
    from .models import RightsAccessResponseDraft

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsAccessResponseDraft.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        cleared = RightsAccessResponseDraft.objects.filter(pk__in=ids).update(
            encrypted_response="", purged_at=now
        )

    from .rights_final_response import purge_unissued_drafts

    return cleared + purge_unissued_drafts()


@shared_task
def purge_expired_access_coverage():
    """Clear expired final draft text; preserve protected audit references."""
    from .models import RightsAccessCoverage

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsAccessCoverage.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsAccessCoverage.objects.filter(pk__in=ids).update(
            encrypted_coverage="", purged_at=now
        )


@shared_task
def purge_expired_access_scope_inventory():
    """Clear expired final draft text; preserve protected audit references."""
    from .models import RightsAccessScopeInventory

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsAccessScopeInventory.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsAccessScopeInventory.objects.filter(pk__in=ids).update(
            encrypted_inventory="", purged_at=now
        )


@shared_task
def purge_expired_access_field_decision():
    """Clear expired proposed field values; preserve protected audit references."""
    from .models import RightsAccessFieldDecision

    with transaction.atomic():
        now = timezone.now()
        ids = list(
            RightsAccessFieldDecision.objects.select_for_update(skip_locked=True)
            .filter(expires_at__lte=now, purged_at__isnull=True)
            .order_by("pk")
            .values_list("pk", flat=True)[:100]
        )
        return RightsAccessFieldDecision.objects.filter(pk__in=ids).update(
            encrypted_body="", purged_at=now
        )


@shared_task(
    ignore_result=True,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=240,
    time_limit=300,
)
def generate_portability_export(job_id):
    from .rights_portability_jobs import run

    run(job_id)


@shared_task(ignore_result=True)
def reconcile_portability_export_jobs():
    from .rights_portability_jobs import reconcile

    reconcile()
