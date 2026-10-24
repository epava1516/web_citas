"""Statement-local queue scope; evidence access keeps its independent authority."""

from django.db.models import Exists, OuterRef, Q

from apps.core.models import AgencyMember

from .models import Report


def queue_reports(user, statuses):
    """Match views.permitted without per-row reads or truncating eligible cases.

    The caller enforces review permission and MFA. These rows describe the
    query's snapshot and never authorize subsequent private evidence access.
    A reported agency excludes even inactive members; current listing COI
    excludes only active members, as in moderation.conflict_of_interest.
    """
    memberships = AgencyMember.objects.filter(user_id=user.pk)
    return (
        Report.objects.filter(status__in=statuses)
        .exclude(actor_id=user.pk)
        .exclude(Q(reported_individual_id=user.pk) | Q(reported_subject_id=user.pk))
        .exclude(reported_agency__owner_id=user.pk)
        .filter(~Exists(memberships.filter(agency_id=OuterRef("reported_agency_id"))))
        .exclude(revision_id__isnull=False, manager_version__isnull=True)
        .exclude(
            Q(listing__person__individual_id=user.pk)
            | Q(listing__person__subject_id=user.pk)
            | Q(listing__person__agency__owner_id=user.pk)
        )
        .filter(~Exists(memberships.filter(
            agency_id=OuterRef("listing__person__agency_id"), active=True,
        )))
        # Queue presentation needs no ciphertext or hydrated target models.
        .only("id", "created_at", "reason", "mode", "priority")
    )
