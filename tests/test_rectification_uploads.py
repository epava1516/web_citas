import io
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.test import Client
from django.utils import timezone
from PIL import Image
from test_photos import raw_image
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready

from apps.core.models import User
from apps.listings.submissions import validate_submission
from apps.mediafiles.models import Blob, Match
from apps.safety.crypto import unseal
from apps.safety.models import (
    RightsRectificationPhotoUpload,
    RightsRectificationProposal,
    RightsRequest,
)
from apps.safety.rectification_photos import validate

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic supplied replacement image with private scoped correction grounds"


def audit(staff, case):
    path = f"/en/moderation/rights/{case.pk}/rectification/"
    initial = staff.get(path).context["form"].initial
    response = staff.post(
        path,
        initial
        | {
            "operation": "preview",
            "purpose": "Inspect current scoped source including prepared replacement images",
        },
    )
    assert response.status_code == 200
    return path, initial, response


def payload(case, *, key=None, raw=None):
    return {
        "key": key or uuid.uuid4(),
        "version": case.version,
        "operation": "upload",
        "reason": REASON,
        "image": SimpleUploadedFile(
            "private-input.jpg",
            raw if raw is not None else raw_image(942),
            content_type="image/jpeg",
        ),
    }


def test_upload_private_pipeline_replay_and_selected_replacement(request, settings, monkeypatch):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    original_version = case.version
    original_revision = person.listing.approved_revision
    source_rows = list(original_revision.photos.values_list("pk", "blob_id", "position"))
    key = uuid.uuid4()
    assert staff.post(path, payload(case, key=key)).status_code == 409
    assert not RightsRectificationPhotoUpload.objects.exists()
    assert Client(enforce_csrf_checks=True).post(path, payload(case, key=key)).status_code == 403
    form_path, initial, _ = audit(staff, case)
    assert staff.post(path, payload(case, raw=b"not an image")).status_code == 409
    assert staff.post(path, payload(case, key=key)).status_code == 302
    item = RightsRectificationPhotoUpload.objects.get()
    photo = item.photo
    photo.refresh_from_db()
    assert (
        photo.revision.status == "rights-stage" and not photo.approved and photo.comparison_complete
    )
    assert photo.blob.status == "ready" and photo.blob.signature
    with photo.blob.derivative.open("rb") as output:
        derivative = Image.open(io.BytesIO(output.read()))
        assert derivative.format == "WEBP" and not derivative.getexif()
    assert item.expires_at <= item.proof.expires_at
    assert staff.post(path, payload(case, key=key)).status_code == 302
    assert RightsRectificationPhotoUpload.objects.count() == 1
    assert staff.post(path, payload(case, key=key, raw=raw_image(943))).status_code == 409
    case.refresh_from_db()
    assert case.version == original_version and case.status == "reviewing"
    image_url = f"/en/moderation/rights/{case.pk}/rectification/photos/{photo.pk}/"
    assert staff.get(image_url).status_code == 404  # Upload changed the source; no implicit grant.
    data = initial | {
        "operation": "propose",
        "fields": ["photos"],
        "reason": REASON,
        "photos-TOTAL_FORMS": "1",
        "photos-INITIAL_FORMS": "0",
        "photos-0-photo_id": photo.pk,
        "photos-0-position": "0",
    }
    assert staff.post(form_path, data).status_code == 409
    _, _, page = audit(staff, case)
    assert str(photo.pk) in page.context["source_fields"]["upload_choices"]
    assert page.context["photo_editor"].total_form_count() == len(source_rows) + 1
    assert page.context["photo_editor"].forms[-1].initial["DELETE"] is True
    response = staff.get(image_url)
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    assert b"".join(response.streaming_content)
    response.close()
    manager = User.objects.get(
        pk=person.agency.owner_id if person.agency_id else person.individual_id
    )
    owner = Client()
    owner.force_login(manager)
    session = owner.session
    session["mfa_version"] = manager.mfa_version
    session.save()
    assert owner.get(f"/en/photos/{photo.pk}/private/").status_code == 404
    assert owner.get(f"/en/draft/{photo.revision_id}/status/").status_code == 404
    assert owner.get(f"/en/draft/{photo.revision_id}/1/").status_code == 404
    with pytest.raises(ValidationError, match="cannot publish"):
        validate_submission(photo.revision, person)
    assert staff.post(form_path, data).status_code == 302
    assert unseal(RightsRectificationProposal.objects.get().encrypted_changes) == {
        "photos": [str(photo.pk)]
    }
    assert list(original_revision.photos.values_list("pk", "blob_id", "position")) == source_rows
    person.listing.refresh_from_db()
    assert person.listing.approved_revision_id == original_revision.pk


def test_processing_expiry_and_discard_invalidate_private_selection(request, settings, monkeypatch):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    audit(staff, case)
    from apps.mediafiles.tasks import process_blob

    scheduled = []
    with monkeypatch.context() as patch:
        patch.setattr(process_blob, "delay", lambda identifier: scheduled.append(identifier))
        assert staff.post(path, payload(case)).status_code == 302
    item = RightsRectificationPhotoUpload.objects.get()
    assert scheduled == [str(item.photo.blob_id)]  # Captured dispatch, not broker verification.
    form_path, initial, _ = audit(staff, case)
    data = initial | {
        "operation": "propose",
        "fields": ["photos"],
        "reason": REASON,
        "photos-TOTAL_FORMS": "1",
        "photos-INITIAL_FORMS": "0",
        "photos-0-photo_id": item.photo_id,
        "photos-0-position": "0",
    }
    assert staff.post(form_path, data).status_code == 409
    process_blob(
        str(item.photo.blob_id)
    )  # Real local processing after deliberate dispatch capture.
    assert staff.post(form_path, data).status_code == 409  # Processing changed the audited source.
    audit(staff, case)
    with transaction.atomic():
        assert validate([str(item.photo_id)], person, case) == [str(item.photo_id)]
    original_expiry = item.expires_at
    item.expires_at = timezone.now()
    item.save(update_fields=["expires_at"])
    with transaction.atomic(), pytest.raises(ValidationError):
        validate([str(item.photo_id)], person, case)
    item.expires_at = original_expiry  # Test-only metadata restore isolates discard.
    item.save(update_fields=["expires_at"])
    audit(staff, case)
    key = uuid.uuid4()
    discard_data = {
        "key": key,
        "version": case.version,
        "operation": "discard",
        "photo_id": item.photo_id,
        "reason": REASON,
    }
    assert staff.post(path, discard_data).status_code == 302
    assert staff.post(path, discard_data).status_code == 302
    item.refresh_from_db()
    assert item.discarded_at and item.photo.blob.original.storage.exists(
        item.photo.blob.original.name
    )
    assert (
        staff.get(
            f"/en/moderation/rights/{case.pk}/rectification/photos/{item.photo_id}/"
        ).status_code
        == 404
    )
    _, _, page = audit(staff, case)
    assert not page.context["source_fields"]["upload_choices"]
    assert not RightsRectificationProposal.objects.exists()


def test_uploads_reject_changed_base_other_case_epoch_and_duplicate_bytes(
    request, settings, monkeypatch
):
    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    audit(staff, case)
    assert staff.post(path, payload(case)).status_code == 302
    item = RightsRectificationPhotoUpload.objects.get()
    source = person.listing.approved_revision
    original = source.title
    source.title = "Interleaved synthetic base correction"
    source.save(update_fields=["title"])
    _, _, page = audit(staff, case)
    assert not page.context["source_fields"]["upload_choices"]
    with transaction.atomic(), pytest.raises(ValidationError):
        validate([str(item.photo_id)], person, case)
    source.title = original
    source.save(update_fields=["title"])
    audit(staff, case)
    original_epoch = person.rights_version
    person.rights_version += 1
    person.save(update_fields=["rights_version"])
    with transaction.atomic(), pytest.raises(ValidationError):
        validate([str(item.photo_id)], person, case)
    person.rights_version = original_epoch
    person.save(update_fields=["rights_version"])
    foreign_values = {
        field.attname: getattr(case, field.attname)
        for field in RightsRequest._meta.concrete_fields
        if field.name not in {"id", "submission_key"}
    }
    foreign_values["receipt_digest"] = "a" * 64
    other_case = RightsRequest.objects.create(submission_key=uuid.uuid4(), **foreign_values)
    with transaction.atomic(), pytest.raises(ValidationError):
        validate([str(item.photo_id)], person, other_case)
    audit(staff, case)
    assert staff.post(path, payload(case)).status_code == 302
    second = RightsRectificationPhotoUpload.objects.exclude(pk=item.pk).get()
    assert second.photo.blob_id == item.photo.blob_id
    with transaction.atomic(), pytest.raises(ValidationError, match="Same image"):
        validate([str(item.photo_id), str(second.photo_id)], person, case)


def test_global_duplicates_do_not_expose_staging_to_general_match_review(
    request, settings, monkeypatch
):
    from apps.mediafiles.models import Photo
    from apps.mediafiles.services import process

    case, _, staff, _, _, person = ready(request, settings, monkeypatch, "rectify")
    foreign = (
        Photo.objects.exclude(revision__listing__person=person)
        .filter(removed_at__isnull=True)
        .first()
    )
    Blob.objects.filter(pk=foreign.blob_id).update(status="queued")
    process(str(foreign.blob_id))  # Prepare fixture bytes with the actual signature pipeline.
    foreign.blob.refresh_from_db()
    with foreign.blob.original.open("rb") as image:
        raw = image.read()
    audit(staff, case)
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    assert staff.post(path, payload(case, raw=raw)).status_code == 302
    item = RightsRectificationPhotoUpload.objects.get()
    match = Match.objects.filter(photo=item.photo, candidate=foreign).first()
    assert match and match.method == "sha256"
    assert staff.get(f"/en/moderation/matches/{match.pk}/photo/image/").status_code in {403, 404}
    queue = staff.get("/en/moderation/matches/")
    assert queue.status_code == 200
    assert match.pk not in [value.pk for value in queue.context["matches"]]
    assert not Match.objects.filter(candidate=item.photo).exists()
    from apps.listings.moderation import unresolved_matches

    assert not unresolved_matches(foreign.revision).filter(pk=match.pk).exists()
    assert staff.get(f"/en/moderation/matches/{match.pk}/photo/image/").status_code == 403
    # A later lifecycle change cannot turn a prepared reference into a generic one.
    item.photo.revision.status = "withdrawn"
    item.photo.revision.save(update_fields=["status"])
    assert staff.get(f"/en/moderation/matches/{match.pk}/photo/image/").status_code == 403
    assert match.pk not in [
        value.pk for value in staff.get("/en/moderation/matches/").context["matches"]
    ]
    assert not unresolved_matches(foreign.revision).filter(pk=match.pk).exists()


def test_same_upload_key_serializes_in_postgresql(request, settings, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import connections

    from apps.safety.rectification_uploads import upload

    case, moderator, staff, _, _, _ = ready(request, settings, monkeypatch, "rectify")
    audit(staff, case)
    barrier = Barrier(2)
    key = uuid.uuid4()

    def invoke():
        connections.close_all()
        try:
            user = User.objects.get(pk=moderator.pk)
            barrier.wait(timeout=10)
            result = upload(user, case.pk, key, case.version, payload(case)["image"], REASON)
            return result.pk, result.photo_id
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(invoke) for _ in range(2)]
        results = [future.result(timeout=30) for future in futures]
    assert results[0] == results[1]
    assert RightsRectificationPhotoUpload.objects.count() == 1


@pytest.mark.parametrize("expired_during", ["source", "blob"])
def test_upload_rejects_proof_expiring_during_source_lock_wait(
    request, settings, monkeypatch, expired_during
):
    from datetime import timedelta
    from pathlib import Path

    from apps.listings.models import Revision
    from apps.mediafiles.models import Photo
    from apps.safety import rights_rectification
    from apps.safety.models import RightsAction

    case, _, staff, _, _, _ = ready(request, settings, monkeypatch, "rectify")
    audit(staff, case)
    proof = case.proofs.order_by("-created_at", "-pk").first()
    expired = proof.expires_at + timedelta(seconds=1)
    original_snapshot = rights_rectification.source_snapshot
    observed = []
    before = (Blob.objects.count(), Photo.objects.count(), Revision.objects.count())
    media = Path(settings.MEDIA_ROOT)
    files_before = {p.relative_to(media) for p in media.rglob("*") if p.is_file()}

    def after_wait(*args, **kwargs):
        result = original_snapshot(*args, **kwargs)
        observed.append(proof.pk)
        # Model elapsed lock-wait time; domain source/DB/authorization remain real.
        if expired_during == "source":
            monkeypatch.setattr(timezone, "now", lambda: expired)
        return result

    monkeypatch.setattr(rights_rectification, "source_snapshot", after_wait)
    if expired_during == "blob":
        manager = Blob.objects
        original_create = manager.get_or_create

        def after_blob_wait(*args, **kwargs):
            result = original_create(*args, **kwargs)
            monkeypatch.setattr(timezone, "now", lambda: expired)
            return result

        monkeypatch.setattr(manager, "get_or_create", after_blob_wait)
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    key = uuid.uuid4()
    response = staff.post(path, payload(case, key=key))
    assert observed
    assert response.status_code == 409
    assert not RightsRectificationPhotoUpload.objects.exists()
    assert not RightsAction.objects.filter(key=key).exists()
    assert (Blob.objects.count(), Photo.objects.count(), Revision.objects.count()) == before
    assert {p.relative_to(media) for p in media.rglob("*") if p.is_file()} == files_before


def test_discard_rejects_proof_expiring_during_upload_lock_wait(request, settings, monkeypatch):
    from datetime import timedelta

    from django.db.models.query import QuerySet

    from apps.safety.models import RightsAction

    case, _, staff, _, _, _ = ready(request, settings, monkeypatch, "rectify")
    path = f"/en/moderation/rights/{case.pk}/rectification/uploads/"
    audit(staff, case)
    assert staff.post(path, payload(case)).status_code == 302
    item = RightsRectificationPhotoUpload.objects.get()
    audit(staff, case)
    proof = case.proofs.order_by("-created_at", "-pk").first()
    expired = proof.expires_at + timedelta(seconds=1)
    original_first = QuerySet.first
    observed = []

    def after_wait(query):
        result = original_first(query)
        if query.model is RightsRectificationPhotoUpload and query.query.select_for_update:
            observed.append(result.pk)
            monkeypatch.setattr(timezone, "now", lambda: expired)
        return result

    monkeypatch.setattr(QuerySet, "first", after_wait)
    key = uuid.uuid4()
    response = staff.post(path, {
        "key": key, "version": case.version, "operation": "discard",
        "photo_id": item.photo_id, "reason": REASON,
    })
    assert observed == [item.pk]
    assert response.status_code == 409
    item.refresh_from_db()
    assert item.discarded_at is None
    assert not RightsAction.objects.filter(key=key).exists()
