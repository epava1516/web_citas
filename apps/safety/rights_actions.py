import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal
from .models import RightsAction, RightsRequest
from .rights import fingerprint


@transaction.atomic
@sensitive_variables()
def act(user, case_id, key, version, operation, reason):
    if not user.has_perm("safety.review_rights_request") or not user.mfa_enabled:
        raise PermissionDenied("Rights permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_rights_assignment"):
        raise PermissionDenied("Rights coordination permission required")
    case = RightsRequest.objects.select_for_update().get(pk=case_id)
    if case.actor_id == user.pk:
        raise PermissionDenied("Cannot manage your own rights request")
    signature = fingerprint(
        json.dumps({"version": version, "operation": operation, "reason": reason}, sort_keys=True)
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
        ):
            return case
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if case.version != version or operation not in {"claim", "unassign"}:
        raise ValidationError("Request changed; reload / Solicitud cambiada; recarga")
    if not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    if operation == "claim":
        if case.status != "received" or case.assigned_to_id:
            raise ValidationError("Request already assigned / Solicitud ya asignada")
        case.assigned_to = user
        case.status = "reviewing"
    else:
        if case.status != "reviewing" or not case.assigned_to_id:
            raise ValidationError("No active assignment / No hay asignación activa")
        case.assigned_to = None
        case.status = "received"
    try:
        with transaction.atomic():
            RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation=operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error
    case.version += 1
    case.save(update_fields=["status", "assigned_to", "version"])
    return case
