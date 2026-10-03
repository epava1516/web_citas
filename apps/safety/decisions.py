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
def act(
    user,
    report_id,
    key,
    version,
    operation,
    reason,
    manager_version=None,
    revision_id=None,
    link_listing_id=None,
):
    from .views import permitted

    if not user.has_perm("safety.review_report") or not user.mfa_enabled:
        raise PermissionDenied("Report permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_report_assignment"):
        raise PermissionDenied("Assignment management permission required")
    initial = Report.objects.select_related("listing__person").get(pk=report_id)
    candidate = None
    if operation == "link":
        candidate = Listing.objects.select_related("person").filter(pk=link_listing_id).first()
        if not candidate:
            raise ValidationError("Publication unidentified / Publicación sin identificar")
        if initial.listing_id and initial.listing_id != candidate.pk:
            raise ValidationError("Reference already linked / Referencia ya enlazada")
        if not initial.listing_id:
            initial.listing = candidate
    person = initial.listing.person if initial.listing_id else None
    agency_ids = {
        value
        for value in [initial.reported_agency_id, person.agency_id if person else None]
        if value
    }
    if candidate and candidate.approved_revision_id:
        acceptance = candidate.approved_revision.publisher_acceptance
        if acceptance and acceptance.agency_id:
            agency_ids.add(acceptance.agency_id)
    list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
    listing = None
    if person:
        previous_agency = person.agency_id
        person = Person.objects.select_for_update().get(pk=person.pk)
        if person.agency_id != previous_agency:
            raise ValidationError("Management changed; reload / Gestor cambiado; recarga")
        listing = Listing.objects.select_for_update().get(pk=initial.listing_id)
    report = Report.objects.select_for_update().get(pk=report_id)
    if listing and report.listing_id == listing.pk:
        listing.person = person
        report.listing = listing
    if not permitted(user, report):
        raise PermissionDenied("Conflict of interest")
    action_payload = {
        "version": version,
        "operation": operation,
        "reason": reason,
        "manager_version": manager_version,
        "revision_id": str(revision_id) if revision_id else None,
    }
    if operation == "link":
        action_payload["link_listing_id"] = str(link_listing_id)
    fingerprint = digest(json.dumps(action_payload, sort_keys=True))
    previous = ReportAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.actor_id == user.pk
            and previous.report_id == report.pk
            and previous.payload_digest == fingerprint
        ):
            return report
        raise ValidationError("Conflicting action replay / Reintento incompatible")
    if report.version != version or operation not in {
        "claim",
        "link",
        "restrict",
        "dismiss",
        "unassign",
    }:
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    if operation == "claim":
        if report.status != "received" or report.assigned_to_id:
            raise ValidationError("Case already assigned / Caso ya asignado")
        report.assigned_to = user
        report.status = "reviewing"
    elif operation == "unassign":
        if report.status != "reviewing" or not report.assigned_to_id:
            raise ValidationError("No active assignment / No hay asignación activa")
        report.assigned_to = None
        report.status = "received"
    else:
        if report.status != "reviewing" or report.assigned_to_id != user.pk:
            raise ValidationError("Case not assigned to you / Caso no asignado")
        if not ReportAccess.objects.filter(report=report, actor=user).exists():
            raise ValidationError("Inspect evidence first / Consulta primero la evidencia")
        if operation == "link":
            if report.listing_id or not listing or not listing.approved_revision_id:
                raise ValidationError(
                    "Reference already linked or publication unidentified / Referencia enlazada o publicación sin identificar"
                )
            revision = listing.approved_revision
            if revision.status != "approved" or not revision.publisher_acceptance_id:
                raise ValidationError(
                    "Published revision required / Revisión publicada obligatoria"
                )
            acceptance = revision.publisher_acceptance
            report.listing = listing
            listing.person = person
            report.revision = revision
            report.reported_agency_id = acceptance.agency_id
            report.reported_individual_id = acceptance.user_id if not acceptance.agency_id else None
            report.reported_subject_id = (
                person.verificationcheck_set.filter(
                    manager_version=revision.manager_version, status="passed"
                )
                .order_by("-created_at")
                .values_list("subject_id", flat=True)
                .first()
            )
            report.manager_version = revision.manager_version
            if not permitted(user, report):
                raise PermissionDenied("Conflict of interest with identified publication")
        elif operation == "restrict":
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
    report.save(
        update_fields=[
            "status",
            "assigned_to",
            "version",
            "listing",
            "revision",
            "reported_agency",
            "reported_individual",
            "reported_subject",
            "manager_version",
        ]
    )
    return report
