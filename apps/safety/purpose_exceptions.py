"""Prepare a bound exception for independent review; preparation permits no treatment."""

from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .erasure_plans import authorized_inventory
from .models import (
    ErasureExecution,
    ErasurePlan,
    PurposeExceptionProposal,
    PurposeRestriction,
    RightsAction,
)
from .processing_review import authorize
from .purpose_release import original_plan
from .rights import fingerprint
from .rights_scope import locked_case, permitted


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, plan_id, key, version, purposes, reason, basis):
    case, person, _ = locked_case(case_id, lock_listing=True)
    fresh = authorize(user, case, review_permission=False)
    if not fresh.has_perm("safety.review_purpose_exception"):
        raise PermissionDenied
    if (
        case.kind != "erase"
        or case.status != "reviewing"
        or case.assigned_to_id != fresh.pk
        or case.version != version
        or not isinstance(purposes, list)
        or not purposes
        or any(not isinstance(value, str) for value in purposes)
        or len(purposes) != len(set(purposes))
        or "account_preferences" not in purposes
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or not isinstance(basis, str)
        or not 20 <= len(basis.strip()) <= 1000
    ):
        raise ValidationError(
            "Current scoped exception required / Excepción de ámbito vigente obligatoria"
        )
    signature = fingerprint(
        canonical(
            {
                "plan": str(plan_id),
                "version": version,
                "purposes": sorted(purposes),
                "reason": reason,
                "basis": basis,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "exception_prepare"
            and previous.payload_digest == signature
        ):
            return PurposeExceptionProposal.objects.get(action=previous)
        raise ValidationError("Conflicting replay / Reintento incompatible")
    plan = (
        ErasurePlan.objects.select_for_update(of=("self",))
        .filter(
            pk=plan_id,
            action__request=case,
            action__actor=fresh,
            inventory__person=person,
            inventory__account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if (
        not plan
        or ErasureExecution.objects.filter(plan=plan).exists()
        or (plan.review_on and plan.review_on <= timezone.localdate())
    ):
        raise ValidationError(
            "Current unexecuted plan required / Plan vigente sin ejecutar obligatorio"
        )
    _, manifest = authorized_inventory(fresh, case, person, plan.inventory_id)
    if plan.source_digest != plan.inventory.source_digest:
        raise ValidationError("Plan source changed / Fuente del plan cambiada")
    try:
        decisions = unseal(plan.encrypted_decisions)["decisions"]
        if plan.action.payload_digest != fingerprint(
            canonical(
                {
                    "inventory": str(plan.inventory_id),
                    "version": plan.action.expected_version,
                    "decisions": decisions,
                }
            )
        ):
            raise ValueError
        operations = {item["purpose"]: item["operation"] for item in decisions}
        if not set(purposes) <= {p for p, op in operations.items() if op == "erase"}:
            raise ValueError
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError(
            "Reviewed erasure scopes required / Ámbitos de supresión revisados obligatorios"
        ) from error
    subject_id = case.account_subject_id or (person.subject_id if person else None)
    if not subject_id:
        raise ValidationError("Subject unidentified / Sujeto sin identificar")
    subject = User.objects.select_for_update().get(pk=subject_id)
    restrictions = list(
        PurposeRestriction.objects.select_for_update(of=("self",))
        .select_related("execution__action__request", "execution__review__plan__action")
        .filter(subject=subject, purpose="account_preferences", active=True)
        .order_by("pk")
    )
    if not restrictions:
        raise ValidationError("No active restriction / No hay restricción activa")
    # Authorization is checked before reading any original restricted-purpose grounds.
    for measure in restrictions:
        if not permitted(fresh, measure.execution.action.request):
            raise PermissionDenied
        if measure.execution.account_subject_id:
            bound_subject = measure.execution.account_subject_id
        else:
            bound_subject = (
                measure.execution.person.subject_id if measure.execution.person_id else None
            )
        if bound_subject != subject.pk:
            raise ValidationError("Restriction scope changed / Ámbito de restricción cambiado")
    now = timezone.now()
    snapshot = {
        "schema": "purpose-exception-proposal-v1",
        "operation": "erasure_execute",
        "purpose": "account_preferences",
        "subject": str(subject.pk),
        "case": str(case.pk),
        "case_version": version,
        "plan": str(plan.pk),
        "plan_digest": fingerprint(plan.encrypted_decisions),
        "source_digest": plan.source_digest,
        "manifest_digest": fingerprint(canonical(manifest)),
        "purposes": sorted(purposes),
        "basis": basis,
        "approved": False,
        "consumed": False,
        "restrictions": [],
    }
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                request=case,
                actor=fresh,
                key=key,
                expected_version=version,
                operation="exception_prepare",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            for measure in restrictions:
                body = original_plan(measure)
                snapshot["restrictions"].append(
                    {
                        "id": measure.pk,
                        "version": measure.version,
                        "mode": measure.mode,
                        "execution": measure.execution_id,
                        "case": str(measure.execution.action.request_id),
                        "plan_digest": fingerprint(measure.execution.review.plan.encrypted_plan),
                        "decision": next(
                            item for item in body["decisions"] if item["purpose"] == measure.purpose
                        ),
                    }
                )
            result = PurposeExceptionProposal.objects.create(
                action=action,
                subject=subject,
                plan=plan,
                proof=plan.inventory.proof,
                source_digest=fingerprint(canonical(snapshot)),
                encrypted_scope=seal(snapshot),
                expires_at=now + timedelta(hours=24),
            )
            authorize(user, case, review_permission=False)
            if not User.objects.get(pk=user.pk).has_perm("safety.review_purpose_exception"):
                raise PermissionDenied
            return result
    except IntegrityError as error:
        raise ValidationError("Conflicting action / Acción incompatible") from error
