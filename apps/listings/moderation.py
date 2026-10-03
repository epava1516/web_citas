from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.models import Agency, AgencyMember, Person
from apps.mediafiles.models import Match

from .models import Listing, ModerationDecision, Revision
from .submissions import validate_submission


def reviewer_allowed(request):
    return bool(
        request.user.has_perm("listings.review_listing")
        and request.user.mfa_enabled
        and request.session.get("mfa_version") == request.user.mfa_version
    )


def conflict_of_interest(user, person):
    return bool(
        user.pk in [person.individual_id, person.subject_id]
        or (
            person.agency_id
            and (
                person.agency.owner_id == user.pk
                or AgencyMember.objects.filter(
                    agency_id=person.agency_id, user=user, active=True
                ).exists()
            )
        )
    )


def unresolved_matches(revision):
    photos = revision.photos.filter(removed_at__isnull=True)
    return Match.objects.filter(
        Q(photo__in=photos) | Q(candidate__in=photos), resolved_at__isnull=True
    )


@transaction.atomic
def decide(user, revision_id, version, outcome, reason):
    if not user.has_perm("listings.review_listing") or not user.mfa_enabled:
        raise PermissionDenied("Moderator permission and MFA required")
    initial = Revision.objects.select_related("listing__person").get(pk=revision_id)
    if initial.listing.person.agency_id:
        Agency.objects.select_for_update().get(pk=initial.listing.person.agency_id)
    person = Person.objects.select_for_update().get(pk=initial.listing.person_id)
    listing = Listing.objects.select_for_update().get(pk=initial.listing_id)
    revision = Revision.objects.select_for_update().get(pk=revision_id)
    if conflict_of_interest(user, person):
        raise PermissionDenied("Cannot review your own listing")
    if (
        revision.status != "pending"
        or revision.edit_version != version
        or not hasattr(revision, "submission")
    ):
        raise ValidationError("Review changed; reload / Revisión cambiada; recarga")
    if outcome not in {"approved", "rejected"} or not reason.strip() or len(reason) > 1000:
        raise ValidationError("Invalid decision / Decisión inválida")
    if outcome == "approved":
        validate_submission(revision, person)
        if unresolved_matches(revision).exists():
            raise ValidationError(
                "Coincidencias pendientes de resolución / Unresolved photo matches"
            )
        revision.photos.filter(removed_at__isnull=True).update(approved=True)
        listing.approved_revision = revision
        listing.status = "published"
        listing.published_at = timezone.now()
        listing.expires_at = timezone.now() + timedelta(days=30)
        listing.save(update_fields=["approved_revision", "status", "published_at", "expires_at"])
    elif not listing.approved_revision_id:
        listing.status = "rejected"
        listing.save(update_fields=["status"])
    revision.status = outcome
    revision.save(update_fields=["status", "updated_at"])
    ModerationDecision.objects.create(
        revision=revision, reviewer=user, outcome=outcome, reason=reason.strip()
    )
    return revision


def publicly_visible(listing):
    revision = listing.approved_revision
    if (
        listing.status != "published"
        or not revision
        or revision.listing_id != listing.pk
        or revision.status != "approved"
        or not listing.expires_at
        or listing.expires_at <= timezone.now()
    ):
        return False
    try:
        validate_submission(revision, listing.person)
    except ValidationError:
        return False
    return True
