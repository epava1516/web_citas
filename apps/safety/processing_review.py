"""Audited current-plan inspection and independent decision; no enforcement."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .erasure_inventory import canonical, source_manifest
from .models import ProcessingPlanRead, ProcessingPlanReview, ProcessingPurposePlan, RightsAction
from .processing_plans import decisions_for
from .rights import fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read


def authorize(user, case):
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.mfa_enabled
        or fresh.mfa_version != user.mfa_version
        or fresh.session_version != user.session_version
        or not all(
            fresh.has_perm("safety." + p)
            for p in ["review_rights_request", "execute_rights_request", "review_processing_plan"]
        )
        or not permitted(fresh, case)
    ):
        raise PermissionDenied
    return fresh


@sensitive_variables()
def current(user, case_id, plan_id, version):
    case, person, _ = locked_case(case_id, lock_listing=True)
    fresh = authorize(user, case)
    plan = (
        ProcessingPurposePlan.objects.select_for_update(of=("self",))
        .select_related("action", "proof")
        .filter(
            pk=plan_id,
            action__request=case,
            person=person if not case.account_subject_id else None,
            account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if not plan:
        raise PermissionDenied
    if (
        case.kind not in {"restriction", "object"}
        or case.status != "reviewing"
        or case.version != version
        or not complete_read(fresh, case)
        or not complete_response_read(fresh, case)
    ):
        raise ValidationError("Inspect current request / Consulta solicitud vigente")
    proof = authorized_proof(case, person, case.kind)
    manifest = source_manifest(person, case)
    if proof.pk != plan.proof_id or fingerprint(canonical(manifest)) != plan.source_digest:
        raise ValidationError(
            "Source or proof changed; prepare again / Fuente o comprobación cambiada; prepara de nuevo"
        )
    return fresh, case, plan, proof, manifest


def contents(plan, manifest):
    try:
        body = unseal(plan.encrypted_plan)
        if (
            body["schema"] != "processing-purpose-plan-v1"
            or body["kind"] != plan.action.request.kind
            or body["enforced"] is not False
            or body["partial"] is not True
            or fingerprint(canonical(body["manifest"])) != plan.source_digest
        ):
            raise ValueError
        reason = unseal(plan.action.encrypted_reason)["reason"]
        signatures = [
            fingerprint(
                canonical(
                    {
                        "version": plan.action.expected_version,
                        "reason": reason,
                        "decisions": body["decisions"],
                        "source_digest": source,
                    }
                )
            )
            for source in [None, plan.source_digest]
        ]
        if plan.action.payload_digest not in signatures:
            raise ValueError
        reviewed = decisions_for(manifest, body["decisions"])
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Invalid plan record / Registro de plan inválido") from error
    return body | {"decisions": reviewed}


@transaction.atomic
@sensitive_variables()
def record(user, case_id, plan_id, key, version, operation, reason, outcome=""):
    fresh, case, plan, proof, manifest = current(user, case_id, plan_id, version)
    if (
        operation not in {"inspect", "review"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or (operation == "inspect" and outcome)
        or (operation == "review" and outcome not in {"approved", "rejected"})
    ):
        raise ValidationError("Invalid review action / Acción de revisión inválida")
    digest = fingerprint(plan.encrypted_plan)
    signature = fingerprint(
        canonical(
            {
                "plan": str(plan.pk),
                "version": version,
                "operation": operation,
                "reason": reason,
                "outcome": outcome,
                "plan_digest": digest,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "processing_" + operation
            and previous.payload_digest == signature
        ):
            return (
                (ProcessingPlanRead.objects.get(action=previous), contents(plan, manifest))
                if operation == "inspect"
                else (ProcessingPlanReview.objects.get(action=previous), None)
            )
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if operation == "review":
        if plan.action.actor_id == fresh.pk:
            raise PermissionDenied("Independent reviewer required")
        if (
            ProcessingPlanReview.objects.filter(plan=plan).exists()
            or not ProcessingPlanRead.objects.filter(
                plan=plan,
                action__actor=fresh,
                action__expected_version=version,
                proof=proof,
                source_digest=plan.source_digest,
                plan_digest=digest,
            ).exists()
        ):
            raise ValidationError(
                "Inspect this current plan before review / Consulta este plan vigente antes de revisar"
            )
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="processing_" + operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            body = contents(plan, manifest)
            if (
                operation == "review"
                and outcome == "approved"
                and any(item["operation"] == "review" for item in body["decisions"])
            ):
                raise ValidationError(
                    "Unresolved purposes cannot be approved / No se aprueban finalidades sin resolver"
                )
            fields = dict(
                action=action,
                plan=plan,
                proof=proof,
                plan_digest=digest,
                source_digest=plan.source_digest,
            )
            result = (
                ProcessingPlanRead.objects.create(**fields)
                if operation == "inspect"
                else ProcessingPlanReview.objects.create(**fields, outcome=outcome)
            )
            authorize(user, case)
            return result, body if operation == "inspect" else None
    except IntegrityError as error:
        raise ValidationError("Conflicting review key / Clave de revisión incompatible") from error
