"""The inherited four-generation budget belongs to Blob, across automatic messages."""

import json
from datetime import timedelta

import pytest
from django.utils import timezone
from test_media_job_recovery import original_blob
from test_media_recovery_progress import fixture_revision, prepared_photo
from test_photos import photo_environment  # noqa: F401

from apps.mediafiles import services, tasks
from apps.mediafiles.models import Blob, Photo

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.usefixtures("photo_environment")]


@pytest.mark.parametrize("status", ["queued", "processing", "failed", "ready"])
@pytest.mark.parametrize("attempts", [4, 5])
def test_exhausted_generation_never_increments_or_reopens_original(
    settings, monkeypatch, record_property, status, attempts
):
    _, revision = fixture_revision(settings)
    item = original_blob("exhausted", status=status, attempts=attempts, width=640, height=480,
                         started_at=timezone.now()-timedelta(seconds=181),
                         error_code="decode_or_storage_failed" if status == "failed" else "")
    photo = Photo.objects.create(revision=revision, blob=item)
    original_name = item.original.name
    storage, opened = item.original.storage, []
    actual_open = storage.open

    def observed_open(name, *args, **kwargs):
        opened.append(name)
        return actual_open(name, *args, **kwargs)

    sent = []
    with monkeypatch.context() as patch:
        patch.setattr(tasks.process_blob, "delay", sent.append)
        tasks.recover_media_jobs.run()
    assert len(sent) == (0 if status == "failed" else 1)
    with monkeypatch.context() as patch:
        patch.setattr(storage, "open", observed_open)
        services.process(item.pk)
    item.refresh_from_db()
    photo.refresh_from_db()
    record_property("n03f_generation_budget", json.dumps({
        "initial_status": status, "initial_attempts": attempts, "final_status": item.status,
        "final_attempts": item.attempts, "storage_opens": len(opened),
        "comparison_complete": photo.comparison_complete, "error_code": item.error_code,
    }, sort_keys=True))
    assert item.attempts == attempts, "Automatic generation exceeded the inherited four-attempt ceiling"
    assert item.status == "failed" and not item.derivative and not item.signature
    assert not opened and not photo.comparison_complete
    assert item.original.name == original_name and storage.exists(original_name)
    assert item.error_code == ("decode_or_storage_failed" if status == "failed"
                               else "generation_attempts_exhausted")
    sent.clear()
    with monkeypatch.context() as patch:
        patch.setattr(tasks.process_blob, "delay", sent.append)
        tasks.recover_media_jobs.run()
    assert not sent


def test_fourth_generation_is_still_allowed(settings):
    _, revision = fixture_revision(settings)
    item = original_blob("last-permitted", status="failed", attempts=3, width=640, height=480)
    photo = Photo.objects.create(revision=revision, blob=item)
    services.process(item.pk)
    item.refresh_from_db()
    photo.refresh_from_db()
    assert item.status == "ready" and item.attempts == 4 and item.signature and item.derivative
    assert photo.comparison_complete and item.error_code == ""


def test_fresh_fourth_generation_lease_is_not_cancelled(settings):
    fixture_revision(settings)
    started = timezone.now()
    item = original_blob("active-fourth", status="processing", attempts=4, started_at=started,
                         width=640, height=480)
    services.process(item.pk)
    item.refresh_from_db()
    assert item.status == "processing" and item.attempts == 4 and item.started_at == started
    assert not item.derivative and item.error_code == ""


def test_ready_comparison_remains_recoverable_at_generation_ceiling(settings, monkeypatch):
    _, item, photo = prepared_photo(settings)
    path, signature = item.derivative.name, item.signature
    Blob.objects.filter(pk=item.pk).update(attempts=4)
    Photo.objects.filter(pk=photo.pk).update(comparison_complete=False)
    sent = []
    with monkeypatch.context() as patch:
        patch.setattr(tasks.process_blob, "delay", sent.append)
        tasks.recover_media_jobs.run()
    assert sent == [str(item.pk)]
    services.process(item.pk)
    item.refresh_from_db()
    photo.refresh_from_db()
    assert item.status == "ready" and item.attempts == 4 and item.derivative.name == path
    assert item.signature == signature and photo.comparison_complete
