import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import Agency, Person
from apps.listings.models import Listing

from .crypto import digest, seal
from .models import Report, ReportAccess, ReportAction, Restriction


@transaction.atomic
@sensitive_variables()
def act(user, report_id, key, version, operation, reason, manager_version=None, revision_id=None):
    from .views import permitted

    if not user.has_perm("safety.review_report") or not user.mfa_enabled:
        raise PermissionDenied("Report permission and MFA required")
    initial = Report.objects.select_related("listing__person").get(pk=report_id)
    person = initial.listing.person if initial.listing_id else None
    agency_ids = {
        value
        for value in [initial.reported_agency_id, person.agency_id if person else None]
        if value
    }
    list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
    listing = None
    if person:
        previous_agency = person.agency_id
        person = Person.objects.select_for_update().get(pk=person.pk)
        if person.agency_id != previous_agency:
            raise ValidationError("Management changed; reload / Gestor cambiado; recarga")
        listing = Listing.objects.select_for_update().get(pk=initial.listing_id)
    report = Report.objects.select_for_update().get(pk=report_id)
    if listing:
        listing.person = person
        report.listing = listing
    if not permitted(user, report):
        raise PermissionDenied("Conflict of interest")
    fingerprint = digest(
        json.dumps(
            {
                "version": version,
                "operation": operation,
                "reason": reason,
                "manager_version": manager_version,
                "revision_id": str(revision_id) if revision_id else None,
            },
            sort_keys=True,
        )
    )
    previous = ReportAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.actor_id == user.pk
            and previous.report_id == report.pk
            and previous.payload_digest == fingerprint
        ):
            return report
        raise ValidationError("Conflicting action replay / Reintento incompatible")
    if report.version != version or operation not in {"claim", "restrict", "dismiss"}:
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    if operation == "claim":
        if report.status != "received" or report.assigned_to_id:
            raise ValidationError("Case already assigned / Caso ya asignado")
        report.assigned_to = user
        report.status = "reviewing"
    else:
        if report.status != "reviewing" or report.assigned_to_id != user.pk:
            raise ValidationError("Case not assigned to you / Caso no asignado")
        if not ReportAccess.objects.filter(report=report, actor=user).exists():
            raise ValidationError("Inspect evidence first / Consulta primero la evidencia")
        if operation == "restrict":
            if (
                not listing
                or not revision_id
                or listing.approved_revision_id != revision_id
                or person.manager_version != manager_version
            ):
                raise ValidationError(
                    "Publication changed or unidentified / Publicación cambiada o sin identificar"
                )
            report.status = "restricted"
        else:
            report.status = "dismissed"
    try:
        with transaction.atomic():
            action = ReportAction.objects.create(
                key=key,
                report=report,
                actor=user,
                expected_version=version,
                operation=operation,
                payload_digest=fingerprint,
                encrypted_reason=seal({"reason": reason}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action replay / Reintento incompatible") from error
    if operation == "restrict":
        Restriction.objects.create(
            report=report,
            listing=listing,
            revision_id=revision_id,
            manager_version=manager_version,
            action=action,
        )
        if listing.status == "published":
            listing.status = "paused"
        listing.available_until = None
        listing.lifecycle_version += 1
        listing.save(update_fields=["status", "available_until", "lifecycle_version"])
    report.version += 1
    report.save(update_fields=["status", "assigned_to", "version"])
    return report
