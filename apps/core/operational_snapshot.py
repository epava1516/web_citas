"""Private aggregate-only view of durable operational work, never broker health."""
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.db.models import Count, Min, Q
from django.db.models.functions import Coalesce, Least
from django.utils import timezone

# Explicit tasks, not every model that happens to have an expiry timestamp.
EXPIRING_MODELS = (
    ("RightsExport", "purge_expired_exports"),
    ("RightsCopyPageReview", "purge_expired_copy_page_reviews"),
    ("RightsCopyInformation", "purge_expired_copy_information"),
    ("RightsPortabilityAssessment", "purge_expired_portability_assessments"),
    ("RightsPortabilitySelection", "purge_expired_portability_selections"),
    ("RightsPortabilityCoverage", "purge_expired_portability_coverage"),
    ("RightsPortabilityResponseDraft", "purge_expired_portability_response_drafts"),
    ("RightsAccessResponseDraft", "purge_expired_access_response_drafts"),
    ("RightsAccessCoverage", "purge_expired_access_coverage"),
    ("RightsAccessScopeInventory", "purge_expired_access_scope_inventory"),
    ("RightsAccessFieldDecision", "purge_expired_access_field_decision"),
)


class SnapshotUnavailable(Exception):
    """Fixed public diagnostic: database exceptions must not expose row values."""


def _measure(query, field, now, due_wait=False, distinct=False):
    aggregates = {"count": Count("pk", distinct=distinct), "oldest": Min(field)}
    if due_wait:
        aggregates["due_since"] = Min(Coalesce("next_attempt_at", "created_at"))
    values = query.aggregate(**aggregates)
    oldest = values["oldest"]
    result = {
        "count": values["count"],
        "oldest_age_seconds": max(0, (now - oldest).total_seconds()) if oldest else None,
    }
    if due_wait:
        since = values["due_since"]
        result["oldest_due_wait_seconds"] = max(0, (now - since).total_seconds()) if since else None
    return result


def collect_snapshot():
    """Use an owned read-only snapshot; reject inherited transactions unchanged."""
    if connection.vendor != "postgresql" or connection.in_atomic_block:
        raise SnapshotUnavailable("Operational snapshot requires its own PostgreSQL transaction")
    try:
        if not connection.get_autocommit():
            raise SnapshotUnavailable("Operational snapshot requires autocommit on entry")
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
                cursor.execute("SET LOCAL statement_timeout = '5s'")
            now = timezone.now()
            dirty = apps.get_model("listings", "PublicationDirty")
            notices = {}
            for name in ("ReportNotice", "ComplaintNotice", "RightsNotice"):
                query = apps.get_model("safety", name).objects.all()
                due = Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now)
                pending = query.filter(status__in=("queued", "retry"))
                notices[name] = {
                    "due": _measure(pending.filter(due, attempts__lt=5), "created_at", now, due_wait=True),
                    "scheduled": _measure(pending.filter(next_attempt_at__gt=now, attempts__lt=5), "created_at", now),
                    "exhausted": _measure(pending.filter(attempts__gte=5), "created_at", now),
                    "failed": _measure(query.filter(status="failed"), "created_at", now),
                }
            jobs = apps.get_model("safety", "RightsPortabilityExportJob").objects.all()
            purges = {
                name: {
                    "task": f"apps.safety.tasks.{task}",
                    **_measure(apps.get_model("safety", name).objects.filter(
                        expires_at__lte=now, purged_at__isnull=True), "expires_at", now),
                }
                for name, task in EXPIRING_MODELS
            }
            # This task also removes unused final drafts with a relative 24h expiry.
            drafts = apps.get_model("safety", "RightsAction").objects.filter(
                operation__in=("erase_final_draft", "process_final_draft", "rectify_final_draft"),
                created_at__lte=now - timedelta(hours=24),
                purged_at__isnull=True, final_response__isnull=True,
            ).exclude(encrypted_reason="")
            confirmations = apps.get_model("safety", "RightsAccountEmailConfirmation").objects.filter(
                expires_at__lte=now).exclude(encrypted_delivery="")
            deliveries = apps.get_model("safety", "RightsObjectDelivery").objects.filter(purged_at__isnull=True)
            physical = {}
            for name in ("MediaErasure", "MediaPreparationCleanup"):
                query = apps.get_model("mediafiles", name).objects.all()
                pending = query.filter(status__in=("queued", "failed"))
                eligible = pending.filter(attempts__lt=5) if name == "MediaErasure" else pending
                physical[name] = {
                    "due": _measure(eligible.filter(next_attempt_at__lte=now), "next_attempt_at", now),
                    "scheduled": _measure(eligible.filter(next_attempt_at__gt=now), "created_at", now),
                    "failed": _measure(query.filter(status="failed"), "created_at", now),
                }
                if name == "MediaErasure":
                    physical[name]["exhausted"] = _measure(pending.filter(attempts__gte=5), "created_at", now)
                else:
                    retained = query.filter(status="retained")
                    physical[name]["retained"] = _measure(retained, "created_at", now)
                    physical[name]["retained_due"] = _measure(
                        retained.filter(next_attempt_at__lte=now), "next_attempt_at", now)
            blobs = apps.get_model("mediafiles", "Blob").objects.all()
            candidates = blobs.filter(
                Q(photos__rectification_upload__discarded_at__isnull=False)
                | Q(photos__rectification_upload__expires_at__lte=now),
                preparation_cleanup__isnull=True,
            )
            return {
                "schema_version": 1,
                "sampled_at": now.isoformat(),
                "scope": "durable_database_work_only",
                "export_job_semantics": "availability_only_not_authorization;expired_and_missing_leases_are_subsets_of_running",
                "publication": _measure(dirty.objects.all(), "marked_at", now),
                "notice_processor": "disabled" if settings.PRODUCTION or settings.SAFETY_NOTICE_BACKEND != "simulator" else "simulator",
                "notices": notices,
                "export_jobs": {
                    "available_queued": _measure(jobs.filter(state="queued", available_at__lte=now), "available_at", now),
                    "scheduled": _measure(jobs.filter(state="queued", available_at__gt=now), "created_at", now),
                    "running": _measure(jobs.filter(state="running"), "created_at", now),
                    "expired_lease": _measure(jobs.filter(state="running", lease_until__lte=now), "lease_until", now),
                    "missing_lease": _measure(jobs.filter(state="running", lease_until__isnull=True), "created_at", now),
                    "failed": _measure(jobs.filter(state="failed"), "created_at", now),
                },
                "expired_temporaries": purges,
                "unissued_final_drafts": _measure(drafts, "created_at", now),
                "expired_account_confirmation_delivery": _measure(confirmations, "expires_at", now),
                "object_storage": {
                    "enabled": bool(settings.RIGHTS_OBJECT_STORAGE_ENABLED),
                    "recovery_mode": bool(settings.RECOVERY_MODE),
                    "orphan_inventory": "unmeasured",
                },
                "private_delivery_cache": {
                    "semantics": "database_rows_not_file_inventory;groups_may_overlap;invalidated_age_is_creation_age",
                    "expired": _measure(deliveries.filter(
                        Q(expires_at__lte=now) | Q(download__export__expires_at__lte=now)),
                        Least("expires_at", "download__export__expires_at"), now),
                    "invalidated": _measure(deliveries.filter(
                        ~Q(generation=settings.RIGHTS_DELIVERY_GENERATION)
                        | Q(download__export__purged_at__isnull=False)), "created_at", now),
                },
                "media": {
                    "semantics": "durable_work_not_storage_absence;retained_is_not_failed;candidate_is_not_deletion_authority",
                    "physical_jobs": physical,
                    "processing": {
                        "queued": _measure(blobs.filter(status="queued"), "created_at", now),
                        "failed": _measure(blobs.filter(status="failed"), "created_at", now),
                        "stale": _measure(blobs.filter(status="processing", started_at__lt=now - timedelta(minutes=3)), "started_at", now),
                        "missing_start": _measure(blobs.filter(status="processing", started_at__isnull=True), "created_at", now),
                    },
                    "preparation_candidates": _measure(
                        candidates, Coalesce("photos__rectification_upload__discarded_at", "photos__rectification_upload__expires_at"),
                        now, distinct=True),
                },
                "not_measured": ["broker_depth", "worker_liveness", "fallback_frequency", "physical_object_absence", "media_orphan_inventory", "export_orphan_inventory"],
            }
    except DatabaseError:
        raise SnapshotUnavailable("Operational snapshot database read failed") from None
