"""Decision linkage never grants access to the underlying notifier's payload."""

from django.core.exceptions import ValidationError

from apps.core.models import Agency, Person

from .models import Complaint, Report, ReportAction


def permitted(user, complaint):
    from .views import permitted as report_permitted

    if complaint.actor_id == user.pk:
        return False
    if not complaint.decision_id:
        return True
    decision = complaint.decision
    return decision.actor_id != user.pk and report_permitted(user, decision.report)


def locked(complaint_id, candidate_id=None):
    """Caller holds an atomic transaction; lock Agency→Person→Report→Complaint."""
    initial = Complaint.objects.get(pk=complaint_id)
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
        current_report = Report.objects.select_for_update().get(pk=report.pk)
        if current_report.listing_id != report.listing_id:
            raise ValidationError("Reference changed; reload / Referencia cambiada; recarga")
        if person:
            current_report.listing.person = person
        decision.report = current_report
    complaint = Complaint.objects.select_for_update().get(pk=complaint_id)
    if complaint.decision_id != initial.decision_id:
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if complaint.decision_id:
        complaint.decision = decision
    return complaint, decision
