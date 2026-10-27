from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.models import Agency, AgencyMember, Person, User
from apps.mediafiles.models import Match

from .appeal_authority import reviewer_allowed as fresh_reviewer_allowed
from .history import is_rectification_history, ordinary_matches
from .models import Listing, ModerationDecision, Revision
from .profile_contract import CURRENT_CONTRACT
from .submissions import validate_submission


def reviewer_allowed(request):
    return fresh_reviewer_allowed(request)


def require_current_reviewer(user):
    current = User.objects.filter(pk=user.pk).first()
    if (
        current is None
        or not current.is_active
        or current.account_erased_at
        or not current.mfa_enabled
        or current.session_version != user.session_version
        or current.mfa_version != user.mfa_version
        or not current.has_perm("listings.review_listing")
    ):
        raise PermissionDenied("Moderator permission and MFA required")
    return current


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
    return ordinary_matches(
        Match.objects.filter(
            Q(photo__in=photos) | Q(candidate__in=photos),
            Q(resolved_at__isnull=True) | Q(decision="conflict"),
            photo__removed_at__isnull=True,
            candidate__removed_at__isnull=True,
        )
    )


@transaction.atomic
def decide(user, revision_id, version, outcome, reason):
    require_current_reviewer(user)
    initial = Revision.objects.select_related("listing__person").get(pk=revision_id)
    if initial.listing.person.agency_id:
        Agency.objects.select_for_update().get(pk=initial.listing.person.agency_id)
    person = Person.objects.select_for_update().get(pk=initial.listing.person_id)
    listing = Listing.objects.select_for_update().get(pk=initial.listing_id)
    revision = Revision.objects.select_for_update().get(pk=revision_id)
    require_current_reviewer(user)
    if conflict_of_interest(user, person):
        raise PermissionDenied("Cannot review your own listing")
    if (
        is_rectification_history(revision)
        or revision.photos.filter(rectification_upload__isnull=False).exists()
        or revision.status != "pending"
        or revision.content_contract != CURRENT_CONTRACT
        or revision.edit_version != version
        or not hasattr(revision, "submission")
    ):
        raise ValidationError("Review changed; reload / Revisión cambiada; recarga")
    if outcome not in {"approved", "rejected"} or not reason.strip() or len(reason) > 1000:
        raise ValidationError("Invalid decision / Decisión inválida")
    superseded_revisions = []
    if outcome == "approved":
        if revision.submission.approved_base_id != listing.approved_revision_id:
            raise ValidationError(
                "Publicación cambiada; crea una revisión actual / Publication changed; create a current revision"
            )
        validate_submission(revision, person)
        if unresolved_matches(revision).exists():
            raise ValidationError(
                "Coincidencias pendientes de resolución / Unresolved photo matches"
            )
        superseded_revisions = list(
            listing.revisions.select_for_update().filter(status="pending")
            .exclude(pk=revision.pk).order_by("pk")
        )
        # These pending revisions can also block; re-read authority before any write.
        require_current_reviewer(user)
        revision.photos.filter(removed_at__isnull=True).update(approved=True)
        listing.approved_revision = revision
        listing.status = "published"
        listing.published_at = timezone.now()
        listing.expires_at = timezone.now() + timedelta(days=30)
        listing.available_until = None
        listing.lifecycle_version += 1
        listing.save(
            update_fields=[
                "approved_revision",
                "status",
                "published_at",
                "expires_at",
                "available_until",
                "lifecycle_version",
            ]
        )
        for superseded in superseded_revisions:
            superseded.status = "obsolete"
            superseded.save(update_fields=["status", "updated_at"])
            ModerationDecision.objects.create(
                revision=superseded,
                reviewer=user,
                outcome="obsolete",
                reason="Publicación actualizada por otra revisión; crea un borrador actual / Publication updated by another revision; create a current draft",
            )
    elif not listing.approved_revision_id:
        listing.status = "rejected"
        listing.lifecycle_version += 1
        listing.save(update_fields=["status", "lifecycle_version"])
    revision.status = outcome
    revision.save(update_fields=["status", "updated_at"])
    ModerationDecision.objects.create(
        revision=revision, reviewer=user, outcome=outcome, reason=reason.strip()
    )
    return revision


def publicly_visible(listing, *, context=None):
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
        validate_submission(revision, listing.person, context=context)
    except ValidationError:
        return False
    if (
        context.row(revision)._pv_conflict
        if context
        else unresolved_matches(revision).filter(decision="conflict").exists()
    ):
        return False
    return True
