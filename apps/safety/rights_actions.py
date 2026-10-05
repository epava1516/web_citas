import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .crypto import seal
from .models import RightsAccess, RightsAction, RightsExtension, RightsWithdrawal
from .rights import calendar_months, fingerprint
from .rights_prompts import PROMPTS
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read


@transaction.atomic
@sensitive_variables()
def act(
    user,
    case_id,
    key,
    version,
    operation,
    reason,
    link_listing_id=None,
    clarification_prompt="",
    additional_months=None,
    extension_reason="",
    link_person_id=None,
    link_account_id=None,
):
    if not user.has_perm("safety.review_rights_request") or not user.mfa_enabled:
        raise PermissionDenied("Rights permission and MFA required")
    if operation == "unassign" and not user.has_perm("safety.manage_rights_assignment"):
        raise PermissionDenied("Rights coordination permission required")
    if operation == "withdraw" and not user.has_perm("safety.execute_rights_request"):
        raise PermissionDenied("Rights execution permission required")
    if operation == "extend" and not user.has_perm("safety.extend_rights_deadline"):
        raise PermissionDenied("Deadline extension permission required")
    if (link_person_id or link_account_id) and operation != "link":
        raise ValidationError("Profile reference only for linking / Referencia solo para vincular")
    case, person, candidate = locked_case(
        case_id,
        link_listing_id if operation == "link" else None,
        lock_listing=operation == "withdraw",
        allow_version_change=operation == "withdraw",
        link_person_id=link_person_id if operation == "link" else None,
        link_account_id=link_account_id if operation == "link" else None,
        allow_erased_account=operation != "link",
    )
    if not permitted(user, case):
        raise PermissionDenied("Conflict of interest")
    payload = {"version": version, "operation": operation, "reason": reason}
    if operation == "extend":
        payload.update(additional_months=additional_months, extension_reason=extension_reason)
    elif additional_months is not None or extension_reason:
        raise ValidationError("Extension fields only for extension / Campos solo para ampliación")
    if operation == "link":
        payload["link_listing_id"] = str(link_listing_id)
        if link_person_id:
            payload["link_person_id"] = str(link_person_id)
        if link_account_id:
            payload["link_account_id"] = str(link_account_id)
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
    if case.version != version or operation not in {
        "claim",
        "unassign",
        "link",
        "clarify",
        "withdraw",
        "extend",
    }:
        raise ValidationError("Request changed; reload / Solicitud cambiada; recarga")
    if not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    proof = None
    if operation == "extend":
        if (
            case.status != "reviewing"
            or case.assigned_to_id != user.pk
            or additional_months not in {1, 2}
            or extension_reason not in {"complexity", "volume"}
            or case.initial_due_at <= timezone.now()
            or hasattr(case, "extension")
            or not complete_read(user, case)
        ):
            raise ValidationError(
                "Extension unavailable; inspect current request / Ampliación no disponible; consulta la solicitud actual"
            )
    elif operation == "withdraw":
        if (
            case.kind != "representation"
            or case.assigned_to_id != user.pk
            or not complete_read(user, case)
        ):
            raise ValidationError(
                "Inspect assigned representation request / Consulta la reclamación asignada"
            )
        proof = authorized_proof(case, person, "representation")
    elif operation == "claim":
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
        if (
            case.status != "reviewing"
            or case.assigned_to_id != user.pk
            or case.person_id
            or case.account_subject_id
        ):
            raise ValidationError(
                "Request not assigned or already linked / Solicitud no asignada o ya vinculada"
            )
        if (
            (not person or (not candidate and not link_person_id)) and not link_account_id
        ) or not RightsAccess.objects.filter(
            request=case, actor=user, case_version=case.version, message_before__isnull=True
        ).exists():
            raise ValidationError("Inspect the reference first / Consulta primero la referencia")
        if link_account_id:
            if case.kind == "representation":
                raise ValidationError(
                    "Representation requires a profile / Representación requiere perfil"
                )
            case.account_subject_id = link_account_id
            case.reported_subject_id = link_account_id
        else:
            case.person = person
            case.referenced_revision = candidate.approved_revision if candidate else None
            case.manager_version = person.manager_version
            case.reported_agency_id = person.agency_id
            case.reported_individual_id = person.individual_id
            case.reported_subject_id = person.subject_id
        if not permitted(user, case):
            raise PermissionDenied("Conflict with identified profile")
    try:
        with transaction.atomic():
            recorded_action = RightsAction.objects.create(
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
    if operation == "extend":
        RightsExtension.objects.create(
            request=case,
            action=recorded_action,
            additional_months=additional_months,
            reason_code=extension_reason,
            new_due_at=calendar_months(case.received_at, 1 + additional_months),
        )
    if proof:
        RightsWithdrawal.objects.create(
            action=recorded_action,
            proof=proof,
            person=person,
            previous_manager_version=person.manager_version,
            resulting_manager_version=person.manager_version + 1,
            previous_listing_status=candidate.status if candidate else "",
            previous_lifecycle_version=candidate.lifecycle_version if candidate else None,
        )
        person.manager_version += 1
        person.consent_version = 0
        person.consent_revoked_at = timezone.now()
        person.age_status = "pending"
        person.manager_review_status = "pending"
        person.assigned_editor = None
        person.phone_claim = None
        person.save(
            update_fields=[
                "manager_version",
                "consent_version",
                "consent_revoked_at",
                "age_status",
                "manager_review_status",
                "assigned_editor",
                "phone_claim",
            ]
        )
        if candidate:
            candidate.status = "withdrawn"
            candidate.available_until = None
            candidate.lifecycle_version += 1
            candidate.save(update_fields=["status", "available_until", "lifecycle_version"])
            candidate.revisions.filter(status="pending").update(status="withdrawn")
        case.status = "withdrawn"
        case.scope_status = "unverified"
    case.version += 1
    case.save(
        update_fields=[
            "status",
            "assigned_to",
            "version",
            "scope_status",
            "person",
            "account_subject",
            "referenced_revision",
            "manager_version",
            "reported_agency",
            "reported_individual",
            "reported_subject",
        ]
    )
    return case
