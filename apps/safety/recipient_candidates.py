"""Historical role candidates; none of these records proves disclosure by itself."""

from apps.core.models import RepresentationAction
from apps.listings.models import Revision, Submission


def manager_evidence(person):
    yield (
        "agency" if person.agency_id else "individual",
        person.agency_id or person.individual_id,
        "current_manager",
        person.pk,
    )
    for row in RepresentationAction.objects.filter(person=person).order_by("pk"):
        yield row.manager_kind, row.manager_id, "representation_history", row.pk
        yield row.previous_manager_kind, row.previous_manager_id, "previous_representation", row.pk
    for row in Submission.objects.filter(revision__listing__person=person).order_by("pk"):
        yield "account", row.actor_id, "submission_actor", row.pk
    for row in (
        Revision.objects.filter(listing__person=person, publisher_acceptance__isnull=False)
        .select_related("publisher_acceptance")
        .order_by("pk")
    ):
        yield (
            "account",
            row.publisher_acceptance.user_id,
            "publishing_acceptance",
            row.publisher_acceptance_id,
        )
