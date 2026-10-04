"""SQL authority tests with synthetic persisted ledgers, not proof of human approval."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.mediafiles.models import Blob, Photo
from apps.safety import models
from apps.safety.crypto import seal
from apps.safety.photo_dispositions import active_withdrawals

pytestmark = pytest.mark.django_db(transaction=True)


def ledger(person):
    now = timezone.now()
    user = person.subject
    case = models.RightsRequest.objects.create(
        submission_key=uuid4(),
        person=person,
        kind="rectify",
        encrypted_payload=seal({}),
        received_at=now,
        initial_due_at=now + timedelta(days=30),
        receipt_expires_at=now + timedelta(days=30),
    )
    proof = models.RightsProof.objects.create(
        key=uuid4(),
        request=case,
        person=person,
        initiated_by=user,
        case_version=1,
        manager_version=person.manager_version,
        scope="rectify",
        expires_at=now + timedelta(hours=1),
        encrypted_reason=seal({}),
    )

    def action(operation):
        return models.RightsAction.objects.create(
            key=uuid4(),
            request=case,
            actor=user,
            expected_version=1,
            operation=operation,
            encrypted_reason=seal({}),
        )

    proposal = models.RightsRectificationProposal.objects.create(
        action=action("rectify_propose"),
        proof=proof,
        person=person,
        source_revision=person.listing.approved_revision,
        encrypted_changes=seal({"photos": []}),
    )
    review = models.RightsRectificationReview.objects.create(
        proposal=proposal,
        action=action("rectify_review"),
        proof=proof,
        outcome="approved",
    )
    response = models.RightsResponse.objects.create(
        key=uuid4(),
        request=case,
        actor=user,
        case_version=1,
        response_version=1,
        kind="progress",
        encrypted_reason=seal({}),
        encrypted_response=seal({}),
    )
    notification = models.RightsRectificationNotification.objects.create(
        review=review,
        action=action("rectify_notify"),
        response=response,
        proof=proof,
    )
    return models.RightsRectificationExecution.objects.create(
        notification=notification,
        action=action("rectify_execute"),
        proof=proof,
        encrypted_previous_values=seal({}),
        resulting_rights_version=person.rights_version,
    )


def test_latest_explicit_file_decision_is_scoped_and_survives_unrelated_corrections(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    original = person.listing.approved_revision.photos.first()
    other = Photo.objects.create(
        revision=original.revision,
        blob=Blob.objects.create(sha256="f" * 64),
        position=7,
    )

    def record(execution, photo, outcome):
        return models.RightsRectificationPhotoDisposition.objects.create(
            execution=execution,
            source_photo=photo,
            blob=photo.blob,
            outcome=outcome,
        )

    first = ledger(person)
    a = record(first, original, "withdrawn")
    b = record(first, other, "withdrawn")
    peer_photo, _ = Photo.objects.get_or_create(
        revision=peer.listing.revisions.first(), blob=original.blob
    )
    record(ledger(peer), peer_photo, "retained")  # Same bytes, other person.
    assert set(active_withdrawals(person.pk).values_list("pk", flat=True)) == {a.pk, b.pk}
    retained = record(ledger(person), original, "retained")
    assert set(active_withdrawals(person.pk).values_list("pk", flat=True)) == {b.pk}
    latest = record(ledger(person), original, "withdrawn")
    # Exercise the deterministic tie breaker as well as ordinary chronological order.
    models.RightsRectificationPhotoDisposition.objects.filter(
        pk__in=[a.pk, retained.pk, latest.pk]
    ).update(created_at=timezone.now())
    assert set(active_withdrawals(person.pk).values_list("pk", flat=True)) == {b.pk, latest.pk}
    assert not active_withdrawals(peer.pk).exists()


def test_protected_exact_and_visual_candidates_are_private_and_scoped(request):
    import hashlib
    import io

    from django.core.files.base import ContentFile
    from PIL import Image

    from apps.listings.models import Revision
    from apps.mediafiles.services import process
    from apps.safety.photo_reintroduction import detect

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    peer = Person.objects.get(subject__username="fixture-v1-model-b")
    original = person.listing.approved_revision.photos.first()
    execution = ledger(person)
    disposition = models.RightsRectificationPhotoDisposition.objects.create(
        execution=execution,
        source_photo=original,
        blob=original.blob,
        outcome="withdrawn",
    )
    revision = Revision.objects.create(
        listing=person.listing,
        manager_version=person.manager_version,
        status="draft",
    )
    photo = Photo.objects.create(revision=revision, blob=original.blob)
    detect(photo.pk)
    detect(photo.pk)
    event = models.RightsPhotoReintroduction.objects.get(photo=photo)
    assert event.disposition_id == disposition.pk and event.method == "sha256"
    assert event.uploaded_blob_id == photo.blob_id
    peer_revision = Revision.objects.create(
        listing=peer.listing,
        manager_version=peer.manager_version,
        status="draft",
    )
    peer_photo = Photo.objects.create(revision=peer_revision, blob=original.blob)
    detect(peer_photo.pk)
    assert not models.RightsPhotoReintroduction.objects.filter(photo=peer_photo).exists()
    with original.blob.derivative.open("rb") as source:
        image = Image.open(source).convert("RGB")
    for cropped in [False, True]:
        variant = image
        if cropped:
            width, height = image.size
            variant = image.crop((width // 10, height // 10, width * 9 // 10, height * 9 // 10))
        output = io.BytesIO()
        variant.save(output, format="JPEG", quality=72)
        raw = output.getvalue()
        blob = Blob.objects.create(sha256=hashlib.sha256(raw).hexdigest())
        blob.original.save(str(uuid4()), ContentFile(raw))
        uploaded = Photo.objects.create(revision=revision, blob=blob, position=2 + int(cropped))
        process(blob.pk)
        candidate = models.RightsPhotoReintroduction.objects.get(photo=uploaded)
        assert candidate.disposition_id == disposition.pk and candidate.method == "regional"
    assert models.RightsPhotoReintroduction.objects.filter(photo=photo).count() == 1
    assert not models.RightsPhotoReintroduction.objects.filter(photo=original).exists()
