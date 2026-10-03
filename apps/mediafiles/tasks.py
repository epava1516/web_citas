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

    from django.db.models import Q
    from django.utils import timezone

    from .models import Blob

    stale = timezone.now() - timedelta(minutes=3)
    pending = Blob.objects.filter(
        Q(status="queued")
        | Q(status="processing", started_at__lt=stale)
        | Q(status="failed", attempts__lt=4)
        | Q(status="ready", photos__comparison_complete=False, photos__removed_at__isnull=True)
    ).distinct()
    for blob_id in pending.values_list("pk", flat=True)[:100]:
        process_blob.delay(str(blob_id))
