from celery import shared_task

from .services import process


@shared_task(
    bind=True, autoretry_for=(OSError,), retry_backoff=True, retry_kwargs={"max_retries": 3}
)
def process_blob(self, blob_id):
    process(blob_id)


@shared_task
def recover_media_jobs():
    from datetime import timedelta

    from django.db.models import Exists, OuterRef, Q
    from django.utils import timezone

    from apps.listings.history import rectification_history_ids

    from .models import Blob, Photo

    stale = timezone.now() - timedelta(minutes=3)
    # Match the detector's origin-photo scope, including private preparations.
    pending_comparisons = Photo.objects.filter(
        blob_id=OuterRef("pk"), comparison_complete=False, removed_at__isnull=True
    ).exclude(revision_id__in=rectification_history_ids())
    pending = Blob.objects.filter(
        Q(status="queued")
        | Q(status="processing", started_at__lt=stale)
        | Q(status="failed", attempts__lt=4)
        | (Q(status="ready") & Exists(pending_comparisons))
    ).distinct()
    for blob_id in pending.values_list("pk", flat=True)[:100]:
        process_blob.delay(str(blob_id))


@shared_task
def erase_media_files():
    from .erasure import erase_due_media

    return erase_due_media()


@shared_task
def cleanup_prepared_media():
    from .preparation_cleanup import cleanup_due_preparations

    return cleanup_due_preparations()
