"""Minimized resource references captured inside an authorized erasure transaction.

References are private evidence, not permission to erase other resources. This
schema needs an independent export and a typed reconciler before recovery use.
"""

from django.views.decorators.debug import sensitive_variables

from apps.core.models import AccountToken, PhoneChallenge, RecoveryCode, RepresentationInvitation
from apps.listings.models import Favorite, Listing, Revision
from apps.mediafiles.models import MediaErasure, Photo

from .crypto import unseal


def ids(query):
    return [str(pk) for pk in query.order_by("pk").values_list("pk", flat=True)]


@sensitive_variables()
def capture(person, subject, purposes, exports, shared_ids, media_redaction):
    refs = {}
    if "authentication" in purposes:
        refs["tokens"] = ids(AccountToken.objects.filter(user=subject))
        refs["recovery_codes"] = ids(RecoveryCode.objects.filter(user=subject))
    if "account_preferences" in purposes:
        refs["favorites"] = ids(Favorite.objects.filter(user=subject))
    if "contact" in purposes:
        refs["phone_challenges"] = ids(PhoneChallenge.objects.filter(person=person))
    if "representation" in purposes:
        refs["representation_invitations"] = ids(
            RepresentationInvitation.objects.filter(person=person)
        )
    if set(purposes) & {"publication", "representation", "shared_contact_review"}:
        refs["listings"] = ids(Listing.objects.filter(person=person))
    if set(purposes) & {"publication", "shared_contact_review"}:
        refs["revisions"] = ids(Revision.objects.filter(listing__person=person))
    if "transient_copy" in purposes:
        refs["exports"] = [str(export.pk) for export in exports if not export.purged_at]
    if "media" in purposes:
        photos = list(
            Photo.objects.filter(revision__listing__person=person)
            .order_by("pk")
            .values_list("pk", "blob_id")
        )
        refs["photos"] = [
            {"photo": str(pk), "blob": str(blob), "shared": blob in shared_ids}
            for pk, blob in photos
        ]
        refs["media_operation"] = (
            "detach_shared_and_review_exclusive" if media_redaction else "erase_exclusive"
        )
    return refs


@sensitive_variables()
def finalized(refs, person, subject, purposes, execution):
    value = {"schema": "recovery-resource-references-v1", "resources": refs}
    if subject:
        value["account"] = {
            "id": str(subject.pk),
            "minimum_session_version": subject.session_version,
            "minimum_mfa_version": subject.mfa_version,
            "anonymize": "account" in purposes,
        }
    if person:
        value["person"] = {
            "id": str(person.pk),
            "minimum_rights_version": person.rights_version,
            "minimum_manager_version": person.manager_version,
        }
    if "media" in purposes:
        replacements = dict(
            Photo.objects.filter(
                pk__in=[row["photo"] for row in refs["photos"] if row["shared"]]
            ).values_list("pk", "blob_id")
        )
        if refs["media_operation"] == "detach_shared_and_review_exclusive":
            for row in refs["photos"]:
                if row["shared"]:
                    row["replacement"] = str(replacements[Photo._meta.pk.to_python(row["photo"])])
        value["media_jobs"] = [
            {"job": str(job.pk), "blob": str(job.blob_id), "paths": unseal(job.encrypted_paths)}
            for job in MediaErasure.objects.filter(execution=execution).order_by("pk")
        ]
    return value
