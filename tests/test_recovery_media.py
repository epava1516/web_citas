import pytest
from django.core.files.base import ContentFile
from django.utils import timezone
from test_erasure_execution import payload
from test_media_erasure import setup
from test_recovery_apply import stored_receipt
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.mediafiles.models import Photo
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryMediaJob, RecoveryOutbox
from apps.safety.recovery_apply import reconcile
from apps.safety.recovery_media import destroy_one
from scripts.recovery_ledger import LedgerIntegrityError

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch, tmp_path):
    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    reconcile(store, start)
    return person, blob, store, start, RecoveryMediaJob.objects.get(blob=blob)


def test_actual_deletion_and_reintroduced_file_replay(request, settings, monkeypatch, tmp_path):
    person, blob, store, start, job = prepared(request, settings, monkeypatch, tmp_path)
    original, derivative = blob.original.name, blob.derivative.name
    storage = blob.original.storage
    saved_paths = job.encrypted_paths
    job.encrypted_paths = "Synthetic damaged encrypted recovery paths"
    job.save(update_fields=["encrypted_paths"])
    with pytest.raises(LedgerIntegrityError):
        destroy_one(job.pk, store, start)
    assert storage.exists(original)
    job.encrypted_paths = saved_paths
    job.save(update_fields=["encrypted_paths"])
    with storage.open(original, "rb") as source:
        original_bytes = source.read()
    assert destroy_one(job.pk, store, start)
    assert not storage.exists(original) and not blob.derivative.storage.exists(derivative)
    job.refresh_from_db()
    blob.refresh_from_db()
    assert job.status == "completed" and not job.encrypted_paths and blob.status == "erased"
    assert not destroy_one(job.pk, store, start)
    assert storage.save(original, ContentFile(original_bytes)) == original
    assert reconcile(store, start)["applied"] == 0
    job.refresh_from_db()
    assert job.status == "queued"
    assert destroy_one(job.pk, store, start)
    assert not storage.exists(original)
    assert (
        RecoveryMediaJob.objects.filter(application=job.application, blob_reference=blob.pk).count()
        == 1
    )


def test_failure_preserves_retry_and_checks_missing_file(request, settings, monkeypatch, tmp_path):
    person, blob, store, start, job = prepared(request, settings, monkeypatch, tmp_path)
    original, derivative = blob.original.name, blob.derivative.name
    storage = blob.original.storage
    delete = storage.delete

    def fail_derivative(path):
        if path == derivative:
            raise OSError("Synthetic storage failure")
        return delete(path)

    with monkeypatch.context() as patch:
        patch.setattr(storage, "delete", fail_derivative)
        assert not destroy_one(job.pk, store, start)
    job.refresh_from_db()
    assert job.status == "failed" and job.attempts == 1 and job.encrypted_paths
    assert not storage.exists(original) and storage.exists(derivative)
    retry_state = (job.status, job.attempts, job.next_attempt_at, job.encrypted_paths)
    assert reconcile(store, start)["applied"] == 0
    job.refresh_from_db()
    assert (job.status, job.attempts, job.next_attempt_at, job.encrypted_paths) == retry_state
    assert not destroy_one(job.pk, store, start)
    RecoveryMediaJob.objects.filter(pk=job.pk).update(next_attempt_at=timezone.now())
    assert destroy_one(job.pk, store, start)
    job.refresh_from_db()
    assert job.status == "completed" and job.attempts == 2


def test_new_sharing_and_missing_external_authority_prevent_deletion(
    request, settings, monkeypatch, tmp_path
):
    person, blob, store, start, job = prepared(request, settings, monkeypatch, tmp_path)
    peer = Person.objects.exclude(pk=person.pk).first()
    Photo.objects.create(revision=peer.listing.revisions.first(), blob=blob)
    with pytest.raises(LedgerIntegrityError):
        destroy_one(job.pk, store, start)
    assert blob.original.storage.exists(blob.original.name)
    job.refresh_from_db()
    assert job.status == "queued" and job.attempts == 0
    (store.checkpoint_directory / "checkpoint.json").unlink()
    with pytest.raises(LedgerIntegrityError):
        destroy_one(job.pk, store, start)
    assert blob.original.storage.exists(blob.original.name)


@pytest.mark.parametrize("mixed", [False, True])
def test_restored_shared_redaction_preserves_peer_and_pending_exclusive_media(
    request, settings, monkeypatch, tmp_path, mixed
):
    from test_shared_media_redaction import prepared as shared_fixture

    from apps.mediafiles.models import Blob
    from apps.safety.models import RecoveryApplication

    case, actor, _, person, plan, shared, peer_photo, exclusive = shared_fixture(
        request, settings, monkeypatch, mixed=mixed
    )
    own_photos = list(Photo.objects.filter(revision__listing__person=person).values())
    peer_before = Photo.objects.filter(pk=peer_photo.pk).values().get()
    blob_before = Blob.objects.filter(pk=shared.pk).values().get()
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    assert not event["references"]["media_jobs"]
    for row in own_photos:
        Photo.objects.filter(pk=row["id"]).update(**{k: v for k, v in row.items() if k != "id"})
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    assert reconcile(store, start)["applied"] == 1
    assert not Photo.objects.filter(revision__listing__person=person, blob=shared).exists()
    assert not Photo.objects.filter(
        revision__listing__person=person, removed_at__isnull=True
    ).exists()
    assert Photo.objects.filter(pk=peer_photo.pk).values().get() == peer_before
    assert Blob.objects.filter(pk=shared.pk).values().get() == blob_before
    assert shared.original.storage.exists(shared.original.name)
    assert shared.derivative.storage.exists(shared.derivative.name)
    assert not RecoveryMediaJob.objects.exists()
    if mixed:
        exclusive.refresh_from_db()
        assert exclusive.status == "ready" and exclusive.original.storage.exists(
            exclusive.original.name
        )
        assert "media" in event["pending_purposes"]
    after = list(Photo.objects.values())
    assert reconcile(store, start)["applied"] == 0
    assert list(Photo.objects.values()) == after and RecoveryApplication.objects.count() == 1
