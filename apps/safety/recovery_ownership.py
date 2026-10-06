"""Check restored resource ownership before applying recovery effects."""

from django.db import connection
from django.db.models import Q
from django.views.decorators.debug import sensitive_variables

from apps.core.models import (
    AccountToken,
    Person,
    PhoneChallenge,
    RecoveryCode,
    RepresentationInvitation,
    User,
)
from apps.listings.models import Favorite, Listing, Revision
from apps.mediafiles.models import Blob, Photo
from scripts.recovery_ledger import LedgerIntegrityError
from scripts.recovery_receipts import validate_receipt

from .models import RightsExport


@sensitive_variables()
def validate_ownership(receipt):
    if not connection.in_atomic_block:
        raise RuntimeError("Recovery ownership requires an enclosing transaction")
    validate_receipt(receipt)
    refs = receipt["references"]
    person_id = receipt["subject"] if receipt["scope"] == "person" else None
    account_id = refs.get("account", {}).get("id")
    person = Person.objects.select_for_update().filter(pk=person_id).first() if person_id else None
    if person and account_id and str(person.subject_id) != account_id:
        raise LedgerIntegrityError("Recovery account does not belong to restored person")
    if account_id:
        User.objects.select_for_update().filter(pk=account_id).first()
    resources = refs["resources"]
    projections = {
        "tokens": (AccountToken, Q(user_id=account_id)),
        "recovery_codes": (RecoveryCode, Q(user_id=account_id)),
        "favorites": (Favorite, Q(user_id=account_id)),
        "phone_challenges": (PhoneChallenge, Q(person_id=person_id)),
        "representation_invitations": (RepresentationInvitation, Q(person_id=person_id)),
        "listings": (Listing, Q(person_id=person_id)),
        "revisions": (Revision, Q(listing__person_id=person_id)),
        "exports": (
            RightsExport,
            Q(person_id=person_id, account_subject_id=None)
            if person_id
            else Q(account_subject_id=receipt["subject"], person_id=None),
        ),
    }
    for name, (model, owner) in projections.items():
        if name not in resources:
            continue
        rows = model.objects.select_for_update().filter(pk__in=resources[name])
        if rows.exclude(owner).exists():
            raise LedgerIntegrityError("Recovery resource belongs to another scope")
    for reference in resources.get("photos", []):
        photo = Photo.objects.select_for_update().filter(pk=reference["photo"]).first()
        if photo and (
            str(photo.revision.listing.person_id) != person_id
            or str(photo.blob_id) != reference["blob"]
        ):
            raise LedgerIntegrityError("Recovery photo scope or blob changed")
    for job in refs.get("media_jobs", []):
        blob = Blob.objects.select_for_update().filter(pk=job["blob"]).first()
        if (
            Photo.objects.filter(blob_id=job["blob"])
            .exclude(revision__listing__person_id=person_id)
            .exists()
        ):
            raise LedgerIntegrityError("Restored media is shared with another person")
        paths = [path for path in job["paths"].values() if path]
        if (
            Blob.objects.exclude(pk=job["blob"])
            .filter(Q(original__in=paths) | Q(derivative__in=paths))
            .exists()
        ):
            raise LedgerIntegrityError("Restored storage path is shared")
        if blob and any(
            getattr(blob, field).name and getattr(blob, field).name != path
            for field, path in job["paths"].items()
        ):
            raise LedgerIntegrityError("Restored blob path changed")
    return receipt
