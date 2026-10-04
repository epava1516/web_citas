"""Retryable disposal of unused preparations without deleting shared evidence."""

import hashlib
import uuid
from datetime import timedelta

from django.db import connection, transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.safety.crypto import seal, unseal
from apps.safety.models import (
    RightsExportImage,
    RightsRectificationPhotoDisposition,
    RightsRectificationPhotoUpload,
    RightsRectificationProposal,
)

from .models import Blob, MatchResolution, MediaPreparationCleanup, Photo


def retention_reason(blob):
    # Call only under the Blob lock. All supported reference creation uses that lock.
    if Photo.objects.filter(blob=blob, rectification_upload__isnull=True).exists():
        return "shared_reference"
    if RightsRectificationPhotoDisposition.objects.filter(blob=blob).exists():
        return "rectification_evidence"
    paths = [name for name in [blob.original.name, blob.derivative.name] if name]
    if (
        paths
        and Blob.objects.exclude(pk=blob.pk)
        .filter(Q(original__in=paths) | Q(derivative__in=paths))
        .exists()
    ):
        return "shared_storage_path"
    uploads = RightsRectificationPhotoUpload.objects.filter(photo__blob=blob)
    if not uploads.exists():
        return "no_preparation"
    if uploads.filter(discarded_at__isnull=True, expires_at__gt=timezone.now()).exists():
        return "active_upload"
    # Proposals are encrypted. Conservatively retain every preparation in a case
    # with a proposal; do not decrypt private proposals from an unaudited worker.
    if RightsRectificationProposal.objects.filter(
        action__request_id__in=uploads.values("action__request_id")
    ).exists():
        return "case_evidence"
    if (
        MatchResolution.objects.filter(
            Q(match__photo__blob=blob) | Q(match__candidate__blob=blob)
        ).exists()
        or Photo.objects.filter(blob=blob, restrictions__isnull=False).exists()
    ):
        return "review_evidence"
    if RightsExportImage.objects.filter(photo__blob=blob).exists():
        return "export_reference"
    return ""


@transaction.atomic(durable=True)
@sensitive_variables()
def prepare_cleanup(job_id):
    initial = MediaPreparationCleanup.objects.get(pk=job_id)
    blob = Blob.objects.select_for_update().get(pk=initial.blob_id)
    job = MediaPreparationCleanup.objects.select_for_update().get(pk=job_id)
    now = timezone.now()
    if job.status == "completed" or job.next_attempt_at > now:
        return False
    if blob.status in {"erasing", "erased"}:
        # Juridical erasure owns those files and its own durable retry ledger.
        job.status = "retained"
        job.reason_code = "rights_erasure"
        job.next_attempt_at = now + timedelta(hours=1)
        job.save(update_fields=["status", "reason_code", "next_attempt_at"])
        return False
    reason = retention_reason(blob)
    if reason:
        job.status = "retained"
        job.reason_code = reason
        job.next_attempt_at = now + timedelta(hours=1)
        job.save(update_fields=["status", "reason_code", "next_attempt_at"])
        return False
    if blob.status != "purging":
        job.encrypted_paths = seal(
            {"original": blob.original.name, "derivative": blob.derivative.name}
        )
        blob.status = "purging"
        blob.save(update_fields=["status"])
    job.status = "queued"
    job.reason_code = ""
    job.save(update_fields=["encrypted_paths", "status", "reason_code"])
    return True


@transaction.atomic
@sensitive_variables()
def delete_prepared(job_id):
    initial = MediaPreparationCleanup.objects.get(pk=job_id)
    blob = Blob.objects.select_for_update().get(pk=initial.blob_id)
    job = MediaPreparationCleanup.objects.select_for_update().get(pk=job_id)
    now = timezone.now()
    if job.status != "queued" or blob.status != "purging" or job.next_attempt_at > now:
        return False
    reason = retention_reason(blob)
    if reason:
        job.status = "retained"
        job.reason_code = reason
        job.next_attempt_at = now + timedelta(hours=1)
        job.save(update_fields=["status", "reason_code", "next_attempt_at"])
        return False
    job.attempts += 1
    paths = unseal(job.encrypted_paths)
    try:
        for field in ["original", "derivative"]:
            if paths[field]:
                storage = Blob._meta.get_field(field).storage
                storage.delete(paths[field])
                if storage.exists(paths[field]):
                    raise OSError("Preparation deletion not confirmed")
    except OSError:
        job.status = "failed"
        job.reason_code = "storage_delete_failed"
        job.next_attempt_at = now + timedelta(seconds=min(3600, 60 * 2 ** min(job.attempts - 1, 6)))
        job.save(
            update_fields=[
                "encrypted_paths",
                "attempts",
                "status",
                "reason_code",
                "next_attempt_at",
            ]
        )
        return False
    # Release the original digest so a future legitimate upload creates a new
    # Blob. Old protected Photo rows keep pointing to this purged, empty object.
    blob.sha256 = hashlib.sha256(uuid.uuid4().bytes).hexdigest()
    blob.original = blob.derivative = ""
    blob.phash = ""
    blob.signature = {}
    blob.regional_hashes = []
    blob.width = blob.height = blob.attempts = 0
    blob.started_at = None
    blob.error_code = ""
    blob.status = "purged"
    blob.save()
    Photo.objects.filter(blob=blob, removed_at__isnull=True).update(removed_at=now)
    job.status = "completed"
    job.completed_at = now
    job.encrypted_paths = job.reason_code = ""
    job.save(update_fields=["attempts", "status", "completed_at", "encrypted_paths", "reason_code"])
    return True


def cleanup_one(job_id):
    # File deletion cannot be rolled back. Commit the paths and purging guard
    # first; retries still know what to delete if the worker stops afterwards.
    if connection.in_atomic_block:
        raise RuntimeError("Preparation cleanup requires independent committed phases")
    return prepare_cleanup(job_id) and delete_prepared(job_id)


def cleanup_due_preparations():
    # Existing retained jobs rotate by next_attempt_at, avoiding starvation by
    # shared files at the front of the preparation candidate list.
    candidates = (
        Blob.objects.filter(
            Q(photos__rectification_upload__discarded_at__isnull=False)
            | Q(photos__rectification_upload__expires_at__lte=timezone.now()),
            preparation_cleanup__isnull=True,
        )
        .order_by("pk")
        .values_list("pk", flat=True)
        .distinct()[:100]
    )
    queued = 0
    for blob_id in candidates:
        _, created = MediaPreparationCleanup.objects.get_or_create(blob_id=blob_id)
        queued += int(created)
    jobs = list(
        MediaPreparationCleanup.objects.filter(
            status__in=["queued", "failed", "retained"], next_attempt_at__lte=timezone.now()
        )
        .order_by("next_attempt_at", "pk")
        .values_list("pk", flat=True)[:100]
    )
    completed = sum(cleanup_one(job_id) for job_id in jobs)
    return {"queued": queued, "completed": completed}
