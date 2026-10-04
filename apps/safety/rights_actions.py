import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal
from .models import RightsAccess, RightsAction
from .rights import fingerprint
from .rights_prompts import PROMPTS
from .rights_scope import locked_case, permitted


@transaction.atomic
@sensitive_variables()
def act(
    user, case_id, key, version, operation, reason, link_listing_id=None, clarification_prompt=""
):
    if not user.has_perm("safety.review_rights_request") or not user.mfa_enabled:
        raise PermissionDenied("Rights permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_rights_assignment"):
        raise PermissionDenied("Rights coordination permission required")
    case, person, candidate = locked_case(case_id, link_listing_id if operation == "link" else None)
    if not permitted(user, case):
        raise PermissionDenied("Conflict of interest")
    payload = {"version": version, "operation": operation, "reason": reason}
    if operation == "link":
        payload["link_listing_id"] = str(link_listing_id)
    if operation == "clarify":
        payload["clarification_prompt"] = clarification_prompt
    elif clarification_prompt:
        raise ValidationError(
            "Question only allowed for clarification / Pregunta solo para aclaración"
        )
    signature = fingerprint(json.dumps(payload, sort_keys=True))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
        ):
            return case
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if case.version != version or operation not in {"claim", "unassign", "link", "clarify"}:
        raise ValidationError("Request changed; reload / Solicitud cambiada; recarga")
    if not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    if operation == "claim":
        if case.status != "received" or case.assigned_to_id:
            raise ValidationError("Request already assigned / Solicitud ya asignada")
        case.assigned_to = user
        case.status = "reviewing"
    elif operation == "unassign":
        if case.status != "reviewing" or not case.assigned_to_id:
            raise ValidationError("No active assignment / No hay asignación activa")
        case.assigned_to = None
        case.status = "received"
    elif operation == "clarify":
        if case.status != "reviewing" or case.assigned_to_id != user.pk:
            raise ValidationError("Request not assigned / Solicitud no asignada")
        if clarification_prompt not in PROMPTS:
            raise ValidationError("Select a question / Selecciona una pregunta")
        if not RightsAccess.objects.filter(
            request=case, actor=user, case_version=case.version, message_before__isnull=True
        ).exists():
            raise ValidationError(
                "Inspect current evidence first / Consulta primero la evidencia actual"
            )
    else:
        if case.status != "reviewing" or case.assigned_to_id != user.pk or case.person_id:
            raise ValidationError(
                "Request not assigned or already linked / Solicitud no asignada o ya vinculada"
            )
        if (
            not candidate
            or not RightsAccess.objects.filter(
                request=case, actor=user, case_version=case.version, message_before__isnull=True
            ).exists()
        ):
            raise ValidationError("Inspect the reference first / Consulta primero la referencia")
        case.person = person
        case.referenced_revision = candidate.approved_revision
        case.manager_version = person.manager_version
        case.reported_agency_id = person.agency_id
        case.reported_individual_id = person.individual_id
        case.reported_subject_id = person.subject_id
        if not permitted(user, case):
            raise PermissionDenied("Conflict with identified profile")
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
                clarification_prompt=clarification_prompt,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error
    case.version += 1
    case.save(
        update_fields=[
            "status",
            "assigned_to",
            "version",
            "person",
            "referenced_revision",
            "manager_version",
            "reported_agency",
            "reported_individual",
            "reported_subject",
        ]
    )
    return case
