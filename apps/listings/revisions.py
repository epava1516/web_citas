from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.mediafiles.models import Photo
from apps.mediafiles.tasks import process_blob

from .forms import DetailsForm
from .history import is_rectification_history
from .models import Rate, Revision


def create_draft(listing, person):
    """Called under manager/person/listing locks; approved content is never edited."""
    if person.publication_erased_at:
        raise ValidationError("Publication erased / Publicación suprimida")
    source = listing.approved_revision
    if source and source.manager_version != person.manager_version:
        source = None
    correction = (
        listing.revisions.filter(
            manager_version=person.manager_version, status__in=["rejected", "pending"]
        )
        .order_by("-created_at")
        .first()
    )
    if correction and (not source or correction.created_at > source.created_at):
        source = correction
    if source and is_rectification_history(source):
        source = None
    revision = Revision.objects.create(
        listing=listing, manager_version=person.manager_version, source_revision=source
    )
    if not source:
        return revision
    for name in DetailsForm.Meta.fields:
        field = Revision._meta.get_field(name)
        if field.many_to_many:
            getattr(revision, name).set(getattr(source, name).all())
        else:
            setattr(revision, field.attname, deepcopy(getattr(source, field.attname)))
    revision.whatsapp, revision.telegram = source.whatsapp, source.telegram
    # Every new version requires current contact exposure and a fresh declaration.
    revision.save()
    for rate in source.rates.all():
        Rate.objects.create(
            revision=revision,
            concept=rate.concept,
            mode=rate.mode,
            amount=rate.amount,
            currency=rate.currency,
            duration_minutes=rate.duration_minutes,
        )
    blob_ids = set()
    for photo in source.photos.filter(removed_at__isnull=True):
        Photo.objects.create(revision=revision, blob_id=photo.blob_id, position=photo.position)
        blob_ids.add(str(photo.blob_id))
    for blob_id in blob_ids:
        transaction.on_commit(lambda blob_id=blob_id: process_blob.delay(blob_id), robust=True)
    return revision
