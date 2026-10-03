from django.core.exceptions import ValidationError
from django.db import connection

from apps.core.manager_review import transfer_conflict
from apps.core.models import Agency, AgencyMember, Person, RepresentationAction
from apps.listings.models import Listing

from .models import RightsRequest


def agency_conflict(user, agency_id):
    return bool(
        agency_id
        and (
            Agency.objects.filter(pk=agency_id, owner=user).exists()
            or AgencyMember.objects.filter(agency_id=agency_id, user=user).exists()
        )
    )


def permitted(user, case):
    if case.actor_id == user.pk or user.pk in [
        case.reported_individual_id,
        case.reported_subject_id,
    ]:
        return False
    if agency_conflict(user, case.reported_agency_id):
        return False
    if case.person_id:
        if case.manager_version is None or transfer_conflict(user, case.person):
            return False
    if case.referenced_revision_id:
        acceptance = case.referenced_revision.publisher_acceptance
        if (
            not acceptance
            or acceptance.user_id == user.pk
            or agency_conflict(user, acceptance.agency_id)
        ):
            return False
    return True


def locked_case(case_id, link_listing_id=None):
    if not connection.in_atomic_block:
        raise RuntimeError("Rights locks require an enclosing transaction")
    initial = RightsRequest.objects.select_related(
        "person", "referenced_revision__publisher_acceptance"
    ).get(pk=case_id)
    candidate = None
    person = initial.person
    if link_listing_id:
        candidate = (
            Listing.objects.select_related("person", "approved_revision__publisher_acceptance")
            .filter(pk=link_listing_id)
            .first()
        )
        if not candidate:
            raise ValidationError("Profile unidentified / Perfil sin identificar")
        if person and person.pk != candidate.person_id:
            raise ValidationError("Reference already linked / Referencia ya vinculada")
        person = candidate.person
    agency_ids = {
        value
        for value in [initial.reported_agency_id, person.agency_id if person else None]
        if value
    }
    if person:
        transfer = (
            RepresentationAction.objects.filter(
                person=person, manager_version=person.manager_version, action="transfer"
            )
            .order_by("-created_at")
            .first()
        )
        if transfer and transfer.previous_manager_kind == "agency" and transfer.previous_manager_id:
            agency_ids.add(transfer.previous_manager_id)
    for revision in [
        initial.referenced_revision,
        candidate.approved_revision if candidate else None,
    ]:
        if (
            revision
            and revision.publisher_acceptance_id
            and revision.publisher_acceptance.agency_id
        ):
            agency_ids.add(revision.publisher_acceptance.agency_id)
    list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
    if person:
        previous_agency = person.agency_id
        previous_version = person.manager_version
        person = Person.objects.select_for_update().get(pk=person.pk)
        if person.agency_id != previous_agency or person.manager_version != previous_version:
            raise ValidationError("Management changed; reload / Gestor cambiado; recarga")
    if candidate:
        candidate = Listing.objects.select_for_update().get(pk=candidate.pk)
    case = RightsRequest.objects.select_for_update().get(pk=case_id)
    if person and case.person_id == person.pk:
        case.person = person
    return case, person, candidate
