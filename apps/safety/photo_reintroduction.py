"""Private retrieval candidates; visual similarity never authorizes or bans reuse."""

from django.db import transaction

from apps.core.models import Agency, Person
from apps.listings.history import is_rectification_history
from apps.mediafiles.models import Blob, Photo

from .models import RightsPhotoReintroduction
from .photo_dispositions import active_withdrawals


@transaction.atomic
def detect(photo_id):
    from apps.mediafiles.services import stored_signature
    from apps.mediafiles.similarity import compare_signatures

    initial = Photo.objects.select_related("revision__listing__person").get(pk=photo_id)
    snapshot = initial.revision.listing.person
    if snapshot.agency_id:
        Agency.objects.select_for_update().get(pk=snapshot.agency_id)
    person = Person.objects.select_for_update().get(pk=snapshot.pk)
    if person.agency_id != snapshot.agency_id:
        return
    withdrawals = list(active_withdrawals(person.pk))
    blobs = {
        blob.pk: blob
        for blob in Blob.objects.select_for_update()
        .filter(pk__in=[initial.blob_id] + [row.blob_id for row in withdrawals])
        .order_by("pk")
    }
    photo = Photo.objects.select_related("revision").get(pk=photo_id)
    if (
        photo.removed_at
        or photo.blob_id != initial.blob_id
        or photo.revision.manager_version != person.manager_version
        or photo.revision.status == "rights-stage"
        or hasattr(photo, "rectification_upload")
        or is_rectification_history(photo.revision)
    ):
        return
    blob = blobs[photo.blob_id]
    if blob.status != "ready":
        return
    signature = stored_signature(blob)
    for disposition in withdrawals:
        candidate = blobs[disposition.blob_id]
        if candidate.status != "ready":
            continue
        method, score = "sha256", 1
        if candidate.pk != blob.pk:
            other = stored_signature(candidate)
            if not signature or not other:
                continue
            result = compare_signatures(signature, other)
            if not result.is_candidate:
                continue
            method, score = "regional", 1 - result.distance / 64
        RightsPhotoReintroduction.objects.get_or_create(
            photo=photo,
            disposition=disposition,
            defaults={"uploaded_blob": blob, "method": method, "score": score},
        )
