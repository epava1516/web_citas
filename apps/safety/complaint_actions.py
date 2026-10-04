import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .complaint_scope import locked, permitted
from .crypto import digest, seal
from .models import ComplaintAccess, ComplaintAction


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
):
    if not user.has_perm("safety.review_complaint") or not user.mfa_enabled:
        raise PermissionDenied("Complaint permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_complaint_assignment"):
        raise PermissionDenied("Assignment coordination permission required")
    complaint, decision = locked(complaint_id, decision_id if operation == "link" else None)
    if not permitted(user, complaint):
        raise PermissionDenied("Conflict of interest")
    payload = {"version": version, "operation": operation, "reason": reason}
    if operation == "link":
        payload.update(decision_id=decision_id, decision_case_version=decision_case_version)
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
    if complaint.version != version or operation not in {"claim", "unassign", "link"}:
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
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
    else:
        if (
            complaint.decision_id
            or complaint.status != "reviewing"
            or complaint.assigned_to_id != user.pk
        ):
            raise ValidationError("Case not available for linking / Caso no disponible para enlace")
        if not ComplaintAccess.objects.filter(
            complaint=complaint, actor=user, case_version=complaint.version
        ).exists():
            raise ValidationError("Inspect current request first / Consulta la reclamación actual")
        if not decision or decision.operation not in {"restrict", "dismiss", "uphold", "lift"}:
            raise ValidationError("Decision required / Decisión obligatoria")
        if decision.report.version != decision_case_version:
            raise ValidationError(
                "Decision case changed; reload / Expediente de decisión cambiado; recarga"
            )
        complaint.decision = decision
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
                encrypted_reason=seal({"reason": reason}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting replay / Reintento incompatible") from error
    complaint.version += 1
    complaint.save(
        update_fields=["assigned_to", "status", "version", "decision", "decision_case_version"]
    )
    return complaint
