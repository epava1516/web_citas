"""Durable physical deletion. File operations are retried after partial failures."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.safety.crypto import unseal

from .models import Blob, MediaErasure


def erase_one(job_id):
    initial = MediaErasure.objects.get(pk=job_id)
    with transaction.atomic():
        blob = Blob.objects.select_for_update().get(pk=initial.blob_id)
        job = MediaErasure.objects.select_for_update().get(pk=job_id)
        if job.status == "completed" or job.next_attempt_at > timezone.now() or job.attempts >= 5:
            return False
        if blob.status != "erasing":
            return False
        paths = unseal(job.encrypted_paths)
        job.attempts += 1
        try:
            for field in ["original", "derivative"]:
                if paths[field]:
                    storage = Blob._meta.get_field(field).storage
                    storage.delete(paths[field])
                    if storage.exists(paths[field]):
                        raise OSError("Deletion not confirmed")
        except OSError:
            job.status = "failed"
            job.error_code = "storage_delete_failed"
            job.next_attempt_at = timezone.now() + timedelta(seconds=60 * 2 ** (job.attempts - 1))
            job.save(update_fields=["attempts", "status", "error_code", "next_attempt_at"])
            return False
        blob.original = blob.derivative = ""
        blob.status = "erased"
        blob.save(update_fields=["original", "derivative", "status"])
        job.status = "completed"
        job.completed_at = timezone.now()
        job.encrypted_paths = ""
        job.error_code = ""
        job.save(
            update_fields=["attempts", "status", "completed_at", "encrypted_paths", "error_code"]
        )
        return True


def erase_due_media():
    jobs = list(
        MediaErasure.objects.filter(
            status__in=["queued", "failed"], attempts__lt=5, next_attempt_at__lte=timezone.now()
        )
        .order_by("next_attempt_at", "pk")
        .values_list("pk", flat=True)[:100]
    )
    return sum(erase_one(job_id) for job_id in jobs)
