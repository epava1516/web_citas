"""Explicit subject-only projections for reviewed rights copies; no secret fields."""

from apps.core.models import LegalAcceptance, RepresentationAction, User, VerificationCheck
from apps.listings.models import Favorite


def date(value):
    return value.isoformat() if value else None


def legal_acceptances(user):
    """Include the exact referenced version, including inactive historical documents."""
    return [
        {
            "document": item.document.slug,
            "version": item.document.version,
            "language": item.document.language,
            "title": item.document.title,
            "body": item.document.body,
            "published_at": date(item.document.published_at),
            "action": item.action,
            "accepted_at": date(item.created_at),
        }
        for item in LegalAcceptance.objects.filter(user=user)
        .select_related("document")
        .order_by("pk")
    ]


def subject_data(person):
    # A manager, editor or requesting account is never substituted for the represented subject.
    user = User.objects.filter(pk=person.subject_id).first() if person.subject_id else None
    account = None
    acceptances = []
    if user:
        account = {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": date(user.date_joined),
            "last_login": date(user.last_login),
            "email_verified_at": date(user.email_verified_at),
            "role": user.role,
            "active": user.is_active,
            "mfa_enabled": user.mfa_enabled,
        }
        acceptances = legal_acceptances(user)
    verifications = (
        [
            {
                "manager_version": item.manager_version,
                "provider": item.provider,
                "procedure": item.procedure,
                "status": item.status,
                "created_at": date(item.created_at),
                "completed_at": date(item.completed_at),
            }
            for item in VerificationCheck.objects.filter(
                person=person, subject_id=person.subject_id
            ).order_by("created_at", "pk")
        ]
        if person.subject_id
        else []
    )
    return {
        "subject_account": account,
        "legal_acceptances": acceptances,
        "account_activity": {
            "favorites": [
                {"listing_reference": str(item.listing_id), "created_at": date(item.created_at)}
                for item in Favorite.objects.filter(user=user).order_by("pk")
            ]
            if user
            else [],
        },
        "representation": {
            "manager_type": "agency" if person.agency_id else "individual",
            "manager_version": person.manager_version,
            "manager_review_status": person.manager_review_status,
            "age_status": person.age_status,
            "consent_version": person.consent_version,
            "consent_revoked_at": date(person.consent_revoked_at),
            "verifications": verifications,
            "history": [
                {
                    "action": item.action,
                    "manager_version": item.manager_version,
                    "manager_type": item.manager_kind,
                    "previous_manager_type": item.previous_manager_kind,
                    "created_at": date(item.created_at),
                    "document": {
                        "slug": item.document.slug,
                        "version": item.document.version,
                        "language": item.document.language,
                    }
                    if item.document_id
                    else None,
                }
                for item in RepresentationAction.objects.filter(
                    person=person, subject_id=person.subject_id
                )
                .select_related("document")
                .order_by("created_at", "pk")
            ]
            if person.subject_id
            else [],
        },
    }


def contact_data(person, revision):
    claim = person.phone_claim
    owned = bool(
        claim
        and person.subject_id
        and claim.individual_id == person.subject_id
        and not claim.agency_id
        and claim.verified_at
        and revision.phone == claim.phone
    )
    # A publication contact is not automatically the subject's own telephone.
    return {
        "scope": "subject_personal_verified" if owned else "shared_or_unestablished",
        "phone": revision.phone if owned else "",
        "whatsapp": revision.whatsapp if owned else False,
        "telegram": "",  # Username ownership has no independent scoped proof yet.
    }


def image_inventory(revision):
    photos = getattr(revision, "copy_photos", None)
    if photos is None:
        photos = revision.photos.select_related("blob").order_by("created_at", "pk")
    return [
        {
            "photo": str(photo.pk),
            "position": photo.position,
            "created_at": date(photo.created_at),
            "removed_at": date(photo.removed_at),
            "processing_status": photo.blob.status,
            "width": photo.blob.width,
            "height": photo.blob.height,
            "content_included": False,
            "exclusion_code": "awaiting_review",
        }
        for photo in photos
    ]
