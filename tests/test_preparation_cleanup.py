import uuid
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
from time import monotonic

import pytest
from django.db import close_old_connections, connection, connections, transaction
from django.utils import timezone
from test_rectification_uploads import REASON, audit, payload
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import Person
from apps.mediafiles.models import Blob, MediaPreparationCleanup, Photo
from apps.mediafiles.preparation_cleanup import cleanup_due_preparations, cleanup_one
from apps.mediafiles.services import process
from apps.safety.erasure_inventory import source_manifest
from apps.safety.models import RightsRectificationPhotoUpload

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch):
    case, actor, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    audit(staff, case)
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    assert staff.post(path, payload(case)).status_code == 302
    item = RightsRectificationPhotoUpload.objects.get()
    return case, actor, staff, person, item


def expire(item):
    item.expires_at = timezone.now()
    item.save(update_fields=["expires_at"])


def test_expired_exclusive_files_purged_and_same_bytes_can_be_uploaded_again(
    request, settings, monkeypatch
):
    case, _, staff, person, item = prepared(request, settings, monkeypatch)
    blob = item.photo.blob
    sha, original, derivative = blob.sha256, blob.original.name, blob.derivative.name
    storage = blob.original.storage
    expire(item)
    result = cleanup_due_preparations()
    assert result == {"queued": 1, "completed": 1}
    blob.refresh_from_db()
    item.photo.refresh_from_db()
    job = MediaPreparationCleanup.objects.get(blob=blob)
    assert blob.status == "purged" and blob.sha256 != sha
    assert not blob.original and not blob.derivative and not blob.signature and not blob.phash
    assert not blob.regional_hashes and blob.width == blob.height == 0
    assert not storage.exists(original) and not storage.exists(derivative)
    assert item.photo.removed_at and job.completed_at and job.attempts == 1
    assert not job.encrypted_paths and not cleanup_one(job.pk)
    assert cleanup_due_preparations() == {"queued": 0, "completed": 0}
    process(blob.pk)
    blob.refresh_from_db()
    assert blob.status == "purged" and not blob.derivative
    audit(staff, case)
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    assert staff.post(path, payload(case)).status_code == 302
    new = RightsRectificationPhotoUpload.objects.exclude(pk=item.pk).get()
    assert new.photo.blob_id != blob.pk and new.photo.blob.sha256 == sha
    assert new.photo.blob.status == "ready" and new.photo.comparison_complete
    entries = {entry["model"]: entry for entry in source_manifest(person)["entries"]}
    assert entries["safety.RightsRectificationPhotoUpload"]["count"] == 2
    assert entries["mediafiles.MediaPreparationCleanup"]["count"] == 1
    assert (
        staff.get(
            f"/en/moderation/rights/{case.pk}/rectification/photos/{item.photo_id}/"
        ).status_code
        == 404
    )


def test_shared_historical_reference_and_active_sibling_prevent_cleanup(
    request, settings, monkeypatch
):
    case, _, staff, _, item = prepared(request, settings, monkeypatch)
    blob = item.photo.blob
    expire(item)
    audit(staff, case)
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    assert staff.post(path, payload(case)).status_code == 302
    sibling = RightsRectificationPhotoUpload.objects.exclude(pk=item.pk).get()
    assert sibling.photo.blob_id == blob.pk
    assert cleanup_due_preparations() == {"queued": 1, "completed": 0}
    job = MediaPreparationCleanup.objects.get(blob=blob)
    assert job.status == "retained" and job.reason_code == "active_upload"
    expire(sibling)
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    historical = Photo.objects.create(
        revision=peer.listing.revisions.first(), blob=blob, removed_at=timezone.now()
    )
    MediaPreparationCleanup.objects.filter(pk=job.pk).update(next_attempt_at=timezone.now())
    assert not cleanup_one(job.pk)
    job.refresh_from_db()
    blob.refresh_from_db()
    assert job.reason_code == "shared_reference" and job.attempts == 0
    assert blob.status == "ready" and blob.original.storage.exists(blob.original.name)
    assert Photo.objects.filter(pk=historical.pk).exists()


def test_shared_storage_path_preserved_even_without_shared_photo(request, settings, monkeypatch):
    _, _, _, _, item = prepared(request, settings, monkeypatch)
    blob = item.photo.blob
    expire(item)
    alias = Blob.objects.create(sha256="a" * 64, original=blob.derivative.name, status="ready")
    assert cleanup_due_preparations() == {"queued": 1, "completed": 0}
    job = MediaPreparationCleanup.objects.get(blob=blob)
    blob.refresh_from_db()
    assert job.status == "retained" and job.reason_code == "shared_storage_path"
    assert job.attempts == 0 and not job.encrypted_paths
    assert blob.status == "ready" and alias.original.storage.exists(alias.original.name)
    assert blob.original.storage.exists(blob.original.name)


def test_proposal_evidence_is_retained_without_worker_decryption(request, settings, monkeypatch):
    case, _, staff, _, item = prepared(request, settings, monkeypatch)
    path, initial, _ = audit(staff, case)
    assert (
        staff.post(
            path,
            initial
            | {
                "operation": "propose",
                "fields": ["photos"],
                "reason": REASON,
                "photos-TOTAL_FORMS": "1",
                "photos-INITIAL_FORMS": "0",
                "photos-0-photo_id": item.photo_id,
                "photos-0-position": "0",
            },
        ).status_code
        == 302
    )
    expire(item)
    assert cleanup_due_preparations() == {"queued": 1, "completed": 0}
    job = MediaPreparationCleanup.objects.get(blob=item.photo.blob)
    assert job.status == "retained" and job.reason_code == "case_evidence"
    assert not job.encrypted_paths and job.attempts == 0
    assert item.photo.blob.original.storage.exists(item.photo.blob.original.name)


def test_discard_cleanup_partial_storage_failure_retries_and_blocks_upload(
    request, settings, monkeypatch
):
    case, _, staff, _, item = prepared(request, settings, monkeypatch)
    audit(staff, case)
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    assert (
        staff.post(
            path,
            {
                "key": uuid.uuid4(),
                "version": case.version,
                "operation": "discard",
                "photo_id": item.photo_id,
                "reason": REASON,
            },
        ).status_code
        == 302
    )
    blob = item.photo.blob
    original, derivative = blob.original.name, blob.derivative.name
    storage = blob.original.storage
    delete = storage.delete

    def fail_derivative(name):
        if name == derivative:
            raise OSError("Synthetic partial deletion failure")
        delete(name)

    monkeypatch.setattr(storage, "delete", fail_derivative)
    assert cleanup_due_preparations() == {"queued": 1, "completed": 0}
    job = MediaPreparationCleanup.objects.get(blob=blob)
    blob.refresh_from_db()
    assert job.status == "failed" and job.attempts == 1 and job.encrypted_paths
    assert job.reason_code == "storage_delete_failed" and blob.status == "purging"
    assert not storage.exists(original) and storage.exists(derivative)
    assert not cleanup_one(job.pk)
    process(blob.pk)
    audit(staff, case)
    assert staff.post(path, payload(case)).status_code == 409
    assert RightsRectificationPhotoUpload.objects.count() == 1
    monkeypatch.setattr(storage, "delete", delete)
    MediaPreparationCleanup.objects.filter(pk=job.pk).update(next_attempt_at=timezone.now())
    assert cleanup_one(job.pk)
    job.refresh_from_db()
    assert job.attempts == 2 and job.status == "completed" and not job.encrypted_paths
    assert not storage.exists(derivative)


@pytest.mark.parametrize("failure_after_cleanup", [False, True])
def test_inflight_processing_cannot_recreate_purged_preparation(
    request, settings, monkeypatch, failure_after_cleanup
):
    from apps.mediafiles import services

    _, _, _, _, item = prepared(request, settings, monkeypatch)
    blob = item.photo.blob
    Blob.objects.filter(pk=blob.pk).update(status="queued")
    reached, resume = Event(), Event()
    compute = services.compute_signature

    def wait_signature(image):
        reached.set()
        assert resume.wait(timeout=30)
        if failure_after_cleanup:
            raise OSError("Synthetic processing failure after cleanup")
        return compute(image)

    monkeypatch.setattr(services, "compute_signature", wait_signature)

    def processing():
        close_old_connections()
        try:
            if failure_after_cleanup:
                with pytest.raises(OSError):
                    process(blob.pk)
            else:
                process(blob.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(processing)
        try:
            assert reached.wait(timeout=30)
            expire(item)
            assert cleanup_due_preparations() == {"queued": 1, "completed": 1}
        finally:
            resume.set()
        future.result(timeout=30)
    blob.refresh_from_db()
    assert blob.status == "purged" and not blob.original and not blob.derivative


def test_cleanup_serializes_with_new_shared_reference(request, settings, monkeypatch):
    _, _, _, _, item = prepared(request, settings, monkeypatch)
    expire(item)
    blob = item.photo.blob
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    writer_pid = Queue()
    pause = Event()
    job = MediaPreparationCleanup.objects.create(blob=blob)

    def cleaning():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                writer_pid.put(cursor.fetchone()[0])
            return cleanup_one(job.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Blob.objects.select_for_update().get(pk=blob.pk)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder_pid = cursor.fetchone()[0]
            future = pool.submit(cleaning)
            pid = writer_pid.get(timeout=5)
            deadline = monotonic() + 5
            blockers = []
            while monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_blocking_pids(%s)", [pid])
                    blockers = cursor.fetchone()[0]
                if holder_pid in blockers:
                    break
                pause.wait(0.01)
            assert holder_pid in blockers and not future.done()
            Photo.objects.create(revision=peer.listing.revisions.first(), blob=blob)
        assert not future.result(timeout=30)
    job.refresh_from_db()
    assert job.status == "retained" and job.reason_code == "shared_reference"
    assert blob.original.storage.exists(blob.original.name)


@pytest.mark.parametrize("interruption", ["before", "partial"])
def test_worker_interruption_keeps_committed_guard_and_paths(
    request, settings, monkeypatch, interruption
):
    from apps.mediafiles import preparation_cleanup

    case, _, staff, _, item = prepared(request, settings, monkeypatch)
    expire(item)
    blob = item.photo.blob
    original, derivative = blob.original.name, blob.derivative.name
    job = MediaPreparationCleanup.objects.create(blob=blob)
    actual_delete_prepared = preparation_cleanup.delete_prepared

    def interrupted(job_id):
        raise RuntimeError("Synthetic worker termination before deletion")

    storage = blob.original.storage
    delete = storage.delete

    def delete_then_interrupt(name):
        delete(name)
        raise RuntimeError("Synthetic worker termination after partial deletion")

    with monkeypatch.context() as patch:
        if interruption == "before":
            patch.setattr(preparation_cleanup, "delete_prepared", interrupted)
        else:
            patch.setattr(storage, "delete", delete_then_interrupt)
        with pytest.raises(RuntimeError, match="Synthetic worker termination"):
            cleanup_one(job.pk)
    blob.refresh_from_db()
    job.refresh_from_db()
    assert blob.status == "purging" and job.encrypted_paths and job.status == "queued"
    assert job.attempts == 0
    assert storage.exists(original) == (interruption == "before")
    assert storage.exists(derivative)
    audit(staff, case)
    assert (
        staff.post(
            f"/en/moderation/rights/{case.pk}/rectification/uploads/", payload(case)
        ).status_code
        == 409
    )
    assert actual_delete_prepared(job.pk)
    assert not blob.original.storage.exists(original)
    assert not blob.original.storage.exists(derivative)
    job.refresh_from_db()
    assert job.status == "completed" and not job.encrypted_paths
    with transaction.atomic(), pytest.raises(RuntimeError, match="independent committed phases"):
        cleanup_one(job.pk)
