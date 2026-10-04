import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import digest, seal
from .models import Complaint, ComplaintAction


@transaction.atomic
@sensitive_variables()
def act(user, complaint_id, key, version, operation, reason):
    if not user.has_perm("safety.review_complaint") or not user.mfa_enabled:
        raise PermissionDenied("Complaint permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_complaint_assignment"):
        raise PermissionDenied("Assignment coordination permission required")
    complaint = Complaint.objects.select_for_update().get(pk=complaint_id)
    if complaint.actor_id == user.pk:
        raise PermissionDenied("Conflict of interest")
    signature = digest(
        json.dumps({"version": version, "operation": operation, "reason": reason}, sort_keys=True)
    )
    previous = ComplaintAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.complaint_id == complaint.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
        ):
            return complaint
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if complaint.version != version or operation not in {"claim", "unassign"}:
        raise ValidationError("Case changed; reload / Caso cambiado; recarga")
    if not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    if operation == "claim":
        if complaint.status != "received" or complaint.assigned_to_id:
            raise ValidationError("Already assigned / Caso ya asignado")
        complaint.assigned_to = user
        complaint.status = "reviewing"
    else:
        if complaint.status != "reviewing" or not complaint.assigned_to_id:
            raise ValidationError("No active assignment / No hay asignación activa")
        complaint.assigned_to = None
        complaint.status = "received"
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
    complaint.save(update_fields=["assigned_to", "status", "version"])
    return complaint
