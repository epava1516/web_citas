"""Purpose-specific preparation for restriction/objection; never enforces or closes."""

from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .erasure_inventory import canonical, source_manifest
from .models import ProcessingPurposePlan, RightsAction
from .rights import fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read


def decisions_for(manifest, decisions):
    purposes = {item["purpose"] for item in manifest["entries"]}
    fields = {"purpose", "operation", "basis", "reason", "scope", "review_on"}
    if not isinstance(decisions, list) or len(decisions) != len(purposes):
        raise ValidationError("Review every selected purpose / Revisa cada finalidad seleccionada")
    seen, result = set(), []
    for item in decisions:
        if not isinstance(item, dict) or set(item) != fields:
            raise ValidationError("Invalid purpose decision / Decisión de finalidad inválida")
        purpose = item["purpose"]
        if (
            not isinstance(purpose, str)
            or purpose not in purposes
            or purpose in seen
            or not isinstance(item["operation"], str)
            or item["operation"] not in {"restrict", "cease", "continue", "review"}
        ):
            raise ValidationError("Invalid or repeated purpose / Finalidad inválida o repetida")
        seen.add(purpose)
        for field, maximum in [("basis", 1000), ("reason", 2000), ("scope", 1000)]:
            if not isinstance(item[field], str) or not 20 <= len(item[field].strip()) <= maximum:
                raise ValidationError(
                    "Minimized grounds, scope and reason required / Fundamento, ámbito y motivo obligatorios"
                )
        try:
            reviewed = date.fromisoformat(item["review_on"])
            if not timezone.localdate() < reviewed <= timezone.localdate() + timedelta(days=365):
                raise ValueError
        except (ValueError, TypeError) as error:
            raise ValidationError(
                "Future review date required / Fecha futura de revisión obligatoria"
            ) from error
        result.append(item | {"review_on": reviewed.isoformat()})
    return sorted(result, key=lambda item: item["purpose"])


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, key, version, reason, decisions, expected_source_digest=None):
    case, person, _ = locked_case(case_id, lock_listing=True)
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.mfa_enabled
        or fresh.mfa_version != user.mfa_version
        or fresh.session_version != user.session_version
        or not all(
            fresh.has_perm("safety." + permission)
            for permission in ["review_rights_request", "execute_rights_request"]
        )
        or not permitted(fresh, case)
    ):
        raise PermissionDenied
    signature = fingerprint(
        canonical(
            {
                "version": version,
                "reason": reason,
                "decisions": decisions,
                "source_digest": expected_source_digest,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "processing_prepare"
            and previous.payload_digest == signature
        ):
            return ProcessingPurposePlan.objects.get(action=previous)
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if (
        case.kind not in {"restriction", "object"}
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or case.version != version
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect current assigned restriction or objection / Consulta limitación u oposición asignada vigente"
        )
    proof = authorized_proof(case, person, case.kind)
    manifest = source_manifest(person, case)
    reviewed = decisions_for(manifest, decisions)
    source_digest = fingerprint(canonical(manifest))
    if expected_source_digest is not None and expected_source_digest != source_digest:
        raise ValidationError("Source changed; inspect again / Fuente cambiada; consulta de nuevo")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="processing_prepare",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            return ProcessingPurposePlan.objects.create(
                action=action,
                proof=proof,
                person=person if not case.account_subject_id else None,
                account_subject_id=case.account_subject_id,
                source_digest=source_digest,
                encrypted_plan=seal(
                    {
                        "schema": "processing-purpose-plan-v1",
                        "kind": case.kind,
                        "manifest": manifest,
                        "decisions": reviewed,
                        "enforced": False,
                        "partial": True,
                    }
                ),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error


@transaction.atomic
@sensitive_variables()
def preview(user, case_id, key, version, reason):
    case, person, _ = locked_case(case_id, lock_listing=True)
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.mfa_enabled
        or fresh.mfa_version != user.mfa_version
        or fresh.session_version != user.session_version
        or not all(
            fresh.has_perm("safety." + permission)
            for permission in ["review_rights_request", "execute_rights_request"]
        )
        or not permitted(fresh, case)
    ):
        raise PermissionDenied
    signature = fingerprint(canonical({"version": version, "reason": reason}))
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "processing_preview"
            and previous.payload_digest == signature
        ):
            return unseal(previous.encrypted_reason)["manifest"]
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if (
        case.kind not in {"restriction", "object"}
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or case.version != version
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect current assigned request / Consulta solicitud asignada vigente"
        )
    authorized_proof(case, person, case.kind)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="processing_preview",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            manifest = source_manifest(person, case)
            action.encrypted_reason = seal({"reason": reason, "manifest": manifest})
            action.save(update_fields=["encrypted_reason"])
            return manifest
    except IntegrityError as error:
        raise ValidationError("Conflicting action key / Clave incompatible") from error
