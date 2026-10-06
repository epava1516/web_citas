from uuid import uuid4

import pytest
from test_erasure_execution import payload
from test_recovery_apply import stored_receipt
from test_reports import directory, photo_environment  # noqa: F401
from test_shared_media_redaction import prepared

from apps.mediafiles.models import Blob, Photo
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryApplication, RecoveryOutbox
from apps.safety.recovery_apply import reconcile
from scripts.recovery_ledger import LedgerIntegrityError

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("collision", ["data", "foreign", "original", "legacy"])
def test_signed_replacement_cannot_reuse_data_or_foreign_resource(
    request, settings, monkeypatch, tmp_path, collision
):
    case, actor, _, person, plan, shared, peer_photo, _ = prepared(request, settings, monkeypatch)
    before = list(Photo.objects.filter(revision__listing__person=person).values())
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    receipt = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    entries = [row for row in receipt["references"]["resources"]["photos"] if row["shared"]]
    assert entries and all("replacement" in row for row in entries)
    if collision in {"data", "foreign"}:
        target = Blob.objects.create(sha256=uuid4().hex + uuid4().hex, status="erased")
        if collision == "data":
            target.original = shared.original.name
            target.save(update_fields=["original"])
        else:
            Photo.objects.create(revision=peer_photo.revision, blob=target)
        for row in entries:
            row["replacement"] = str(target.pk)
    elif collision == "original":
        for row in entries:
            row["replacement"] = row["blob"]
    else:
        for row in entries:
            del row["replacement"]
    for row in before:
        Photo.objects.filter(pk=row["id"]).update(**{k: v for k, v in row.items() if k != "id"})
    restored = list(Photo.objects.values())
    store, checkpoint = stored_receipt(tmp_path, receipt)
    settings.RECOVERY_MODE = True
    if collision != "legacy":
        with pytest.raises(LedgerIntegrityError):
            reconcile(store, checkpoint)
        assert not RecoveryApplication.objects.exists()
        assert list(Photo.objects.values()) == restored
    else:
        assert reconcile(store, checkpoint)["applied"] == 1
        assert not Photo.objects.filter(revision__listing__person=person, blob=shared).exists()
        assert reconcile(store, checkpoint)["applied"] == 0
    assert shared.original.storage.exists(shared.original.name)
    peer_photo.refresh_from_db()
    assert peer_photo.blob_id == shared.pk and peer_photo.removed_at is None
