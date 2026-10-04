import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .complaint_scope import locked, permitted
from .crypto import digest, seal
from .models import ComplaintAction


@transaction.atomic
@sensitive_variables()
def act(
    user,
    complaint_id,
    key,
    version,
    operation,
    reason,
    decision_id=None,
    decision_case_version=None,
    clarification_prompt="",
):
    if not user.has_perm("safety.review_complaint") or not user.mfa_enabled:
        raise PermissionDenied("Complaint permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_complaint_assignment"):
        raise PermissionDenied("Assignment coordination permission required")
    complaint, decision = locked(
        complaint_id,
        decision_id if operation == "link" else None,
        decision_id if operation == "link_listing" else None,
    )
    if not permitted(user, complaint):
        raise PermissionDenied("Conflict of interest")
    if operation == "reassess":
        from .complaint_resolutions import source_permission

        if not user.has_perm("safety.resolve_complaint") or not source_permission(user, complaint):
            raise PermissionDenied("Independent source reassessment permission required")
    payload = {"version": version, "operation": operation, "reason": reason}
    if operation in {"link", "link_listing", "reassess"}:
        payload.update(decision_id=decision_id, decision_case_version=decision_case_version)
    if operation == "clarify":
        payload["clarification_prompt"] = clarification_prompt
    signature = digest(json.dumps(payload, sort_keys=True))
    previous = ComplaintAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.complaint_id == complaint.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
        ):
            return complaint
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if complaint.version != version or operation not in {
        "claim",
        "unassign",
        "link",
        "link_listing",
        "clarify",
        "reassess",
    }:
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    previous_source_version = complaint.decision_case_version
    if operation == "claim":
        if complaint.status != "received" or complaint.assigned_to_id:
            raise ValidationError("Already assigned / Caso ya asignado")
        complaint.assigned_to = user
        complaint.status = "reviewing"
    elif operation == "unassign":
        if complaint.status != "reviewing" or not complaint.assigned_to_id:
            raise ValidationError("No active assignment / No hay asignación activa")
        complaint.assigned_to = None
        complaint.status = "received"
    elif operation == "reassess":
        from .complaint_reassessment import validate

        validate(user, complaint, decision, decision_id, decision_case_version)
        complaint.decision_case_version = decision_case_version
    elif operation == "clarify":
        from .complaint_messages import PROMPTS, complete_read
        from .complaint_resolutions import source_permission, source_version

        linked = bool(complaint.decision_id or complaint.listing_decision_id)
        current_source = source_version(complaint) if source_permission(user, complaint) else None
        if (
            complaint.status != "reviewing"
            or complaint.assigned_to_id != user.pk
            or clarification_prompt not in PROMPTS
            or not complete_read(user, complaint, current_source)
            or (clarification_prompt == "reference_unknown" and linked)
            or (
                clarification_prompt == "reference_stale"
                and (
                    not linked
                    or current_source is None
                    or current_source == complaint.decision_case_version
                )
            )
        ):
            raise ValidationError(
                "Inspect the current assigned reference / Consulta la referencia asignada vigente"
            )
    else:
        if (
            complaint.decision_id
            or complaint.listing_decision_id
            or complaint.status != "reviewing"
            or complaint.assigned_to_id != user.pk
        ):
            raise ValidationError("Case not available for linking / Caso no disponible para enlace")
        from .complaint_messages import complete_read

        if not complete_read(user, complaint):
            raise ValidationError("Inspect current request first / Consulta la reclamación actual")
        if operation == "link":
            if not decision or decision.operation not in {"restrict", "dismiss", "uphold", "lift"}:
                raise ValidationError("Decision required / Decisión obligatoria")
            if decision.report.version != decision_case_version:
                raise ValidationError(
                    "Decision case changed; reload / Expediente de decisión cambiado; recarga"
                )
            complaint.decision = decision
        else:
            if (
                not decision
                or decision.outcome not in {"approved", "rejected"}
                or decision.revision.edit_version != decision_case_version
            ):
                raise ValidationError(
                    "Revision decision changed or unidentified / Decisión de revisión cambiada o sin identificar"
                )
            complaint.listing_decision = decision
            complaint.listing_decision_subject_id = (
                decision.revision.listing.person.verificationcheck_set.filter(
                    manager_version=decision.revision.manager_version, status="passed"
                )
                .order_by("-created_at")
                .values_list("subject_id", flat=True)
                .first()
            )
        complaint.decision_case_version = decision_case_version
        if not permitted(user, complaint):
            raise PermissionDenied("Conflict of interest with decision")
    try:
        with transaction.atomic():
            ComplaintAction.objects.create(
                key=key,
                complaint=complaint,
                actor=user,
                expected_version=version,
                operation=operation,
                payload_digest=signature,
                encrypted_reason=seal(
                    {
                        "reason": reason,
                        "previous_source_version": previous_source_version,
                        "reviewed_source_version": decision_case_version,
                    }
                    if operation == "reassess"
                    else {"reason": reason}
                ),
                clarification_prompt=clarification_prompt if operation == "clarify" else "",
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting replay / Reintento incompatible") from error
    complaint.version += 1
    complaint.save(
        update_fields=[
            "assigned_to",
            "status",
            "version",
            "decision",
            "decision_case_version",
            "listing_decision",
            "listing_decision_subject",
        ]
    )
    return complaint
