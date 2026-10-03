from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.models import Agency, Person
from apps.core.verification_services import publication_ready
from apps.mediafiles.models import Match, MatchResolution, Photo, PhotoRestriction

from .models import Listing
from .moderation import conflict_of_interest


def locked_pair(match_id):
    """Acquire agency/person/listing/match locks in the shared order inside atomic."""
    initial = Match.objects.select_related(
        "photo__revision__listing", "candidate__revision__listing"
    ).get(pk=match_id)
    person_ids = {
        initial.photo.revision.listing.person_id,
        initial.candidate.revision.listing.person_id,
    }
    snapshots = list(Person.objects.filter(pk__in=person_ids))
    list(
        Agency.objects.select_for_update()
        .filter(pk__in={p.agency_id for p in snapshots if p.agency_id})
        .order_by("pk")
    )
    people = list(Person.objects.select_for_update().filter(pk__in=person_ids).order_by("pk"))
    baseline = {p.pk: p for p in snapshots}
    if any(
        p.manager_version != baseline[p.pk].manager_version
        or p.agency_id != baseline[p.pk].agency_id
        for p in people
    ):
        raise ValidationError("Manager changed; reload / Gestor cambiado; recarga")
    listings = list(
        Listing.objects.select_for_update().filter(person_id__in=person_ids).order_by("pk")
    )
    pair = Q(photo_id=initial.photo_id, candidate_id=initial.candidate_id) | Q(
        photo_id=initial.candidate_id, candidate_id=initial.photo_id
    )
    matches = list(Match.objects.select_for_update().filter(pair).order_by("pk"))
    current = next(m for m in matches if m.pk == match_id)
    return initial, people, listings, matches, current


@transaction.atomic
def resolve(user, match_id, version, outcome, reason, evidence_reference):
    if not user.has_perm("listings.review_listing") or not user.mfa_enabled:
        raise PermissionDenied("Moderator permission and MFA required")
    initial, people, listings, matches, current = locked_pair(match_id)
    if any(conflict_of_interest(user, person) for person in people):
        raise PermissionDenied("Cannot review a conflict involving your own profile")
    if (
        Photo.objects.filter(
            pk__in=[initial.photo_id, initial.candidate_id], removed_at__isnull=True
        ).count()
        != 2
    ):
        raise ValidationError("Photo removed; reload / Foto retirada; recarga")
    if current.review_version != version:
        raise ValidationError("Conflict review changed; reload / Revisión cambiada; recarga")
    if (
        outcome not in {"false_positive", "distinct_people", "conflict"}
        or not reason.strip()
        or len(reason) > 1000
        or not evidence_reference.strip()
        or len(evidence_reference) > 80
    ):
        raise ValidationError("Invalid resolution / Resolución inválida")
    if outcome == "false_positive" and (
        initial.photo.blob_id == initial.candidate.blob_id
        or any(m.method == "sha256" for m in matches)
    ):
        raise ValidationError(
            "Exact bytes cannot be a visual false positive / Bytes exactos no son falso positivo visual"
        )
    if outcome == "distinct_people" and (
        len(people) != 2
        or len({p.subject_id for p in people}) != 2
        or not all(publication_ready(p) for p in people)
    ):
        raise ValidationError(
            "Direct authorizations of distinct subjects required / Se requieren autorizaciones directas de sujetos distintos"
        )
    now = timezone.now()
    current_decision = None
    for match in matches:
        decision = MatchResolution.objects.create(
            match=match,
            reviewer=user,
            outcome=outcome,
            reason=reason.strip(),
            evidence_reference=evidence_reference.strip(),
        )
        if match.pk == current.pk:
            current_decision = decision
        match.resolved_at, match.decision = now, outcome
        match.review_version += 1
        match.save(update_fields=["resolved_at", "decision", "review_version"])
    if outcome == "conflict":
        for photo in [initial.photo, initial.candidate]:
            person = next(p for p in people if p.pk == photo.revision.listing.person_id)
            if photo.revision.manager_version == person.manager_version:
                PhotoRestriction.objects.get_or_create(
                    person=person,
                    decision=current_decision,
                    defaults={"photo": photo, "manager_version": person.manager_version},
                )
        for listing in listings:
            if listing.status == "published":
                listing.status = "paused"
                listing.available_until = None
                listing.save(update_fields=["status", "available_until"])
    # Clearing a conflict does not automatically republish a paused listing.
    return current
