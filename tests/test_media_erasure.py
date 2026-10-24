import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.utils import timezone
from test_erasure_execution import payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.core.operational_assessment import assess
from apps.core.operational_snapshot import collect_snapshot
from apps.mediafiles.erasure import erase_due_media, erase_one
from apps.mediafiles.models import Blob, MediaErasure, Photo
from apps.mediafiles.services import process
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.erasure_inventory import prepare
from apps.safety.erasure_plans import record

pytestmark = pytest.mark.django_db(transaction=True)


def setup(request, settings, monkeypatch):
    result = plan_fixture(request, settings, monkeypatch, selected_purposes=["media"])
    case, actor, _, _, _, person, plan, _, _, _ = result
    photo = person.listing.approved_revision.photos.first()
    return case, actor, person, plan, photo.blob


def test_files_and_fingerprints_erased_durably_without_worker_resurrection(
    request, settings, monkeypatch
):
    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    original, derivative = blob.original.name, blob.derivative.name
    storage = Blob._meta.get_field("original").storage
    sha = blob.sha256
    assert storage.exists(original) and storage.exists(derivative)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    blob.refresh_from_db()
    job = MediaErasure.objects.get(blob=blob)
    assert blob.status == "erasing" and blob.sha256 != sha
    assert not blob.phash and not blob.signature and not blob.regional_hashes
    assert unseal(execution.encrypted_result)["media_jobs_queued"] >= 1
    assert not Photo.objects.filter(
        revision__listing__person=person, removed_at__isnull=True
    ).exists()
    assert storage.exists(original) and storage.exists(derivative)
    process(blob.pk)
    assert erase_due_media() >= 1
    assert not storage.exists(original) and not storage.exists(derivative)
    blob.refresh_from_db()
    job.refresh_from_db()
    assert blob.status == "erased" and not blob.original and not blob.derivative
    assert job.status == "completed" and job.completed_at and not job.encrypted_paths
    assert not erase_one(job.pk)
    process(blob.pk)
    blob.refresh_from_db()
    assert blob.status == "erased" and not blob.derivative
    assert Photo.objects.filter(blob=blob).exists()
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_shared_file_cannot_be_erased_by_another_person(request, settings, monkeypatch):
    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    Photo.objects.create(revision=peer.listing.revisions.first(), blob=blob)
    original = blob.original.name
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    blob.refresh_from_db()
    assert blob.status == "ready" and blob.original.storage.exists(original)
    assert not MediaErasure.objects.exists()
    assert Photo.objects.filter(blob=blob, removed_at__isnull=True).count() >= 2


def test_partial_storage_failure_keeps_retry_state_and_repeats_missing_file(
    request, settings, monkeypatch
):
    case, actor, _, plan, blob = setup(request, settings, monkeypatch)
    execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    job = MediaErasure.objects.get(blob=blob)
    original, derivative = blob.original.name, blob.derivative.name
    storage = Blob._meta.get_field("original").storage
    actual_delete = storage.delete

    def fail_second(name):
        if name == derivative:
            raise OSError("Synthetic storage failure")
        actual_delete(name)

    monkeypatch.setattr(storage, "delete", fail_second)
    assert not erase_one(job.pk)
    job.refresh_from_db()
    assert job.status == "failed" and job.attempts == 1 and job.encrypted_paths
    assert not storage.exists(original) and storage.exists(derivative)
    observed = collect_snapshot()
    assert observed['media']['physical_jobs']['MediaErasure']['failed']['count'] == 1
    assert 'media_physical_failure' in {row['code'] for row in assess(observed)['findings']}
    assert original not in str(observed) and derivative not in str(observed)
    assert not erase_one(job.pk)  # Backoff, no extra attempt.
    monkeypatch.setattr(storage, "delete", actual_delete)
    MediaErasure.objects.filter(pk=job.pk).update(next_attempt_at=timezone.now())
    assert erase_one(job.pk)
    assert not storage.exists(derivative)
    job.refresh_from_db()
    assert job.attempts == 2 and job.status == "completed"
    assert collect_snapshot()['media']['physical_jobs']['MediaErasure']['failed']['count'] == 0


def test_inflight_processing_cannot_write_derivative_after_erasure(request, settings, monkeypatch):
    from apps.mediafiles import services

    case, actor, _, old_plan, blob = setup(request, settings, monkeypatch)
    Blob.objects.filter(pk=blob.pk).update(status="queued")
    reached, resume = Event(), Event()
    compute = services.compute_signature

    def waiting(image):
        reached.set()
        assert resume.wait(timeout=30)
        return compute(image)

    monkeypatch.setattr(services, "compute_signature", waiting)

    def worker():
        close_old_connections()
        try:
            process(blob.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(worker)
        try:
            assert reached.wait(timeout=15)
            # Snapshot the processing state; execution revalidates it under Blob lock.
            inventory = prepare(
                actor,
                case.pk,
                uuid.uuid4(),
                case.version,
                "Review current in-flight media processing scope",
            )
            decisions = unseal(old_plan.encrypted_decisions)["decisions"]
            plan = record(actor, case.pk, inventory.pk, uuid.uuid4(), case.version, decisions)
            execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
            erase_due_media()
        finally:
            resume.set()
        future.result(timeout=30)
    blob.refresh_from_db()
    assert blob.status == "erased" and not blob.derivative and not blob.signature


def test_distinct_blob_with_shared_storage_path_prevents_file_deletion(
    request, settings, monkeypatch
):
    case, actor, _, plan, blob = setup(request, settings, monkeypatch)
    alias = Blob.objects.create(sha256="a" * 64, original=blob.derivative.name, status="ready")
    with pytest.raises(ValidationError):
        execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    blob.refresh_from_db()
    assert blob.status == "ready" and blob.derivative.storage.exists(alias.original.name)
    assert not MediaErasure.objects.exists()
