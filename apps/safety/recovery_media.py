"""Physical recovery deletion, authorized by the independently verified ledger."""

from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.conf import settings
from django.db import connection, models, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.mediafiles.models import Blob, Photo
from scripts.recovery_ledger import LedgerIntegrityError, digest
from scripts.recovery_receipts import validate_receipt

from .crypto import unseal
from .models import RecoveryApplication, RecoveryMediaJob


@sensitive_variables()
def checked_unseal(value):
    try:
        return unseal(value)
    except (InvalidToken, ValueError, TypeError) as error:
        raise LedgerIntegrityError("Recovery private evidence invalid") from error


def verified_receipts(store, start):
    if not getattr(settings, "RECOVERY_MODE", False) or connection.in_atomic_block:
        raise RuntimeError("Isolated recovery mode and no outer transaction required")
    indexed = {}
    for receipt in store.recover(start):
        validate_receipt(receipt)
        key = receipt["execution"]
        if key in indexed and indexed[key] != receipt:
            raise LedgerIntegrityError("Conflicting independently verified receipt")
        indexed[key] = receipt
    return indexed


@sensitive_variables()
def _destroy_one(job_id, receipt):
    initial = RecoveryMediaJob.objects.get(pk=job_id)
    if receipt is None:
        raise LedgerIntegrityError("No independent authority for recovery job")
    with transaction.atomic():
        application = RecoveryApplication.objects.select_for_update().get(pk=initial.application_id)
        if (
            application.receipt_digest != digest(receipt)
            or checked_unseal(application.encrypted_receipt) != receipt
        ):
            raise LedgerIntegrityError("Recovery application binding changed")
        blob = Blob.objects.select_for_update().filter(pk=initial.blob_reference).first()
        job = RecoveryMediaJob.objects.select_for_update().get(pk=job_id)
        if job.application_id != application.pk or job.blob_reference != initial.blob_reference:
            raise LedgerIntegrityError("Recovery job binding changed")
        if job.status == "completed" or job.next_attempt_at > timezone.now() or job.attempts >= 5:
            return False
        if (
            application.scope != receipt["scope"]
            or application.subject_reference != receipt["subject"]
        ):
            raise LedgerIntegrityError("Recovery scope binding changed")
        if job.blob_id is not None and job.blob_id != job.blob_reference:
            raise LedgerIntegrityError("Recovery blob binding changed")
        references = receipt["references"].get("media_jobs", [])
        reference = next(
            (item for item in references if item["blob"] == str(job.blob_reference)), None
        )
        if reference is None or checked_unseal(job.encrypted_paths) != reference["paths"]:
            raise LedgerIntegrityError("Recovery paths lack independent authority")
        person_id = receipt["subject"] if receipt["scope"] == "person" else None
        if (
            Photo.objects.filter(blob_id=job.blob_reference)
            .exclude(revision__listing__person_id=person_id)
            .exists()
        ):
            raise LedgerIntegrityError("Recovery blob is shared")
        paths = reference["paths"]
        names = [path for path in paths.values() if path]
        if (
            Blob.objects.exclude(pk=job.blob_reference)
            .filter(models.Q(original__in=names) | models.Q(derivative__in=names))
            .exists()
        ):
            raise LedgerIntegrityError("Recovery path is shared")
        if blob and any(
            getattr(blob, field).name and getattr(blob, field).name != path
            for field, path in paths.items()
        ):
            raise LedgerIntegrityError("Recovery blob storage changed")
        job.attempts += 1
        try:
            for field in ["original", "derivative"]:
                path = paths[field]
                if path:
                    storage = Blob._meta.get_field(field).storage
                    storage.delete(path)
                    if storage.exists(path):
                        raise OSError("Recovery deletion not confirmed")
        except OSError:
            job.status = "failed"
            job.next_attempt_at = timezone.now() + timedelta(seconds=60 * 2 ** (job.attempts - 1))
            job.save(update_fields=["status", "attempts", "next_attempt_at"])
            return False
        if blob:
            blob.original = blob.derivative = ""
            blob.status = "erased"
            blob.save(update_fields=["original", "derivative", "status"])
        job.status, job.completed_at, job.encrypted_paths = "completed", timezone.now(), ""
        job.save(update_fields=["status", "attempts", "completed_at", "encrypted_paths"])
        return True


def destroy_one(job_id, store, start):
    receipts = verified_receipts(store, start)
    job = RecoveryMediaJob.objects.get(pk=job_id)
    return _destroy_one(job_id, receipts.get(str(job.application_id)))


def destroy_due(store, start, limit=100):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Recovery batch limit between1 and100 required")
    receipts = verified_receipts(store, start)
    jobs = list(
        RecoveryMediaJob.objects.filter(
            status__in=["queued", "failed"], attempts__lt=5, next_attempt_at__lte=timezone.now()
        )
        .order_by("next_attempt_at", "pk")
        .values_list("pk", "application_id")[:limit]
    )
    return sum(_destroy_one(pk, receipts.get(str(application))) for pk, application in jobs)
