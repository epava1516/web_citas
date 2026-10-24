from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.mediafiles.models import Photo
from apps.mediafiles.tasks import process_blob

from .forms import DetailsForm
from .history import is_rectification_history
from .models import Revision
from .profile_contract import CURRENT_CONTRACT, set_profile_catalog


def create_draft(listing, person):
    """Called under manager/person/listing locks; approved content is never edited."""
    if person.publication_erased_at:
        raise ValidationError("Publication erased / Publicación suprimida")
    source = listing.approved_revision
    if source and source.manager_version != person.manager_version:
        source = None
    correction = (
        listing.revisions.filter(
            manager_version=person.manager_version, status__in=["rejected", "pending"],
            content_contract=CURRENT_CONTRACT
        )
        .order_by("-created_at")
        .first()
    )
    if correction and (not source or correction.created_at > source.created_at):
        source = correction
    if source and (is_rectification_history(source) or source.content_contract != CURRENT_CONTRACT):
        source = None
    revision = Revision.objects.create(
        listing=listing, manager_version=person.manager_version, source_revision=source
    )
    set_profile_catalog(revision)
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
    blob_ids = set()
    for photo in source.photos.filter(removed_at__isnull=True):
        Photo.objects.create(revision=revision, blob_id=photo.blob_id, position=photo.position)
        blob_ids.add(str(photo.blob_id))
    for blob_id in blob_ids:
        transaction.on_commit(lambda blob_id=blob_id: process_blob.delay(blob_id), robust=True)
    return revision
