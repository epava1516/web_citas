"""Decision linkage never grants access to the underlying notifier's payload."""

from django.core.exceptions import ValidationError

from apps.core.models import Agency, AgencyMember, Person
from apps.listings.models import Listing, ModerationDecision, Revision
from apps.listings.moderation import conflict_of_interest

from .models import Complaint, Report, ReportAction


def permitted(user, complaint):
    from .views import permitted as report_permitted

    if complaint.actor_id == user.pk:
        return False
    if complaint.listing_decision_id:
        decision = complaint.listing_decision
        acceptance = decision.revision.publisher_acceptance
        if not acceptance or not complaint.listing_decision_subject_id:
            return False
        if user.pk in [
            decision.reviewer_id,
            acceptance.user_id,
            complaint.listing_decision_subject_id,
        ]:
            return False
        if acceptance.agency_id and (
            acceptance.agency.owner_id == user.pk
            or AgencyMember.objects.filter(agency_id=acceptance.agency_id, user=user).exists()
        ):
            return False
        return not conflict_of_interest(user, decision.revision.listing.person)
    if not complaint.decision_id:
        return True
    decision = complaint.decision
    return decision.actor_id != user.pk and report_permitted(user, decision.report)


def locked(complaint_id, candidate_id=None, candidate_listing_id=None):
    """Caller holds an atomic transaction; lock Agency→Person→Report→Complaint."""
    initial = Complaint.objects.get(pk=complaint_id)
    if initial.listing_decision_id or candidate_listing_id:
        return locked_listing(initial, candidate_listing_id)
    decision_id = initial.decision_id or candidate_id
    decision = None
    if decision_id:
        decision = (
            ReportAction.objects.select_related("report__listing__person")
            .filter(pk=decision_id)
            .first()
        )
        if not decision:
            raise ValidationError("Decision unidentified / Decisión sin identificar")
        report = decision.report
        person = report.listing.person if report.listing_id else None
        agency_ids = {
            value
            for value in [report.reported_agency_id, person.agency_id if person else None]
            if value
        }
        list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
        if person:
            current = Person.objects.select_for_update().get(pk=person.pk)
            if current.agency_id != person.agency_id:
                raise ValidationError("Management changed; reload / Gestor cambiado; recarga")
            person = current
            listing = Listing.objects.select_for_update().get(pk=report.listing_id)
        current_report = Report.objects.select_for_update().get(pk=report.pk)
        if current_report.listing_id != report.listing_id:
            raise ValidationError("Reference changed; reload / Referencia cambiada; recarga")
        if person:
            listing.person = person
            current_report.listing = listing
        decision.report = current_report
    complaint = Complaint.objects.select_for_update().get(pk=complaint_id)
    if (
        complaint.decision_id != initial.decision_id
        or complaint.listing_decision_id != initial.listing_decision_id
    ):
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if complaint.decision_id:
        complaint.decision = decision
    return complaint, decision


def locked_listing(initial, candidate_id):
    decision = (
        ModerationDecision.objects.select_related(
            "revision__listing__person", "revision__publisher_acceptance"
        )
        .filter(pk=initial.listing_decision_id or candidate_id)
        .first()
    )
    if not decision:
        raise ValidationError("Decision unidentified / Decisión sin identificar")
    revision = decision.revision
    person = revision.listing.person
    acceptance = revision.publisher_acceptance
    agency_ids = {
        value for value in [person.agency_id, acceptance.agency_id if acceptance else None] if value
    }
    list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
    current = Person.objects.select_for_update().get(pk=person.pk)
    if current.agency_id != person.agency_id:
        raise ValidationError("Management changed; reload / Gestor cambiado; recarga")
    listing = Listing.objects.select_for_update().get(pk=revision.listing_id)
    revision = Revision.objects.select_for_update().get(pk=revision.pk)
    decision = ModerationDecision.objects.select_for_update().get(pk=decision.pk)
    listing.person = current
    revision.listing = listing
    decision.revision = revision
    complaint = Complaint.objects.select_for_update().get(pk=initial.pk)
    if (
        complaint.decision_id != initial.decision_id
        or complaint.listing_decision_id != initial.listing_decision_id
    ):
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if complaint.listing_decision_id:
        complaint.listing_decision = decision
    return complaint, decision
