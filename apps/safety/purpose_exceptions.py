"""Prepare a bound exception for independent review; preparation permits no treatment."""

from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .erasure_inventory import canonical, source_manifest
from .erasure_plans import authorized_inventory
from .models import (
    ErasureExecution,
    ErasurePlan,
    PurposeExceptionProposal,
    PurposeExceptionRead,
    PurposeExceptionReview,
    PurposeRestriction,
    RightsAction,
)
from .processing_review import authorize
from .purpose_release import original_plan
from .rights import fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read


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


@sensitive_variables()
def proposal_contents(proposal, case, manifest, measures):
    """Call only after recording an authorized read or decision action."""
    try:
        body = unseal(proposal.encrypted_scope)
        reason = unseal(proposal.action.encrypted_reason)["reason"]
        signature = fingerprint(
            canonical(
                {
                    "plan": str(proposal.plan_id),
                    "version": proposal.action.expected_version,
                    "purposes": body["purposes"],
                    "reason": reason,
                    "basis": body["basis"],
                }
            )
        )
        if (
            fingerprint(canonical(body)) != proposal.source_digest
            or proposal.action.payload_digest != signature
            or body["schema"] != "purpose-exception-proposal-v1"
            or body["approved"] is not False
            or body["consumed"] is not False
            or body["operation"] != "erasure_execute"
            or body["purpose"] != "account_preferences"
            or body["case"] != str(case.pk)
            or body["case_version"] != case.version
            or body["subject"] != str(proposal.subject_id)
            or body["plan"] != str(proposal.plan_id)
            or body["plan_digest"] != fingerprint(proposal.plan.encrypted_decisions)
            or body["source_digest"] != proposal.plan.source_digest
            or body["manifest_digest"] != fingerprint(canonical(manifest))
            or len(body["restrictions"]) != len(measures)
            or proposal.expires_at <= timezone.now()
            or proposal.expires_at > proposal.created_at + timedelta(hours=24)
        ):
            raise ValueError
        for selected, measure in zip(body["restrictions"], measures, strict=True):
            original = original_plan(measure)
            expected = {
                "id": measure.pk,
                "version": measure.version,
                "mode": measure.mode,
                "execution": measure.execution_id,
                "case": str(measure.execution.action.request_id),
                "plan_digest": fingerprint(measure.execution.review.plan.encrypted_plan),
                "decision": next(
                    item for item in original["decisions"] if item["purpose"] == measure.purpose
                ),
            }
            if selected != expected:
                raise ValueError
        return body
    except (InvalidToken, ValueError, KeyError, TypeError, StopIteration) as error:
        raise ValidationError("Exception source changed / Fuente de excepción cambiada") from error


@transaction.atomic
@sensitive_variables()
def record(user, case_id, proposal_id, key, version, operation, reason, outcome=""):
    case, person, _ = locked_case(case_id, lock_listing=True)
    subject_id = case.account_subject_id or (person.subject_id if person else None)
    if not subject_id:
        raise ValidationError("Subject unidentified / Sujeto sin identificar")
    # Consumption also holds the subject before locking the proposal, including profiles.
    User.objects.select_for_update().get(pk=subject_id)
    fresh = authorize(user, case, review_permission=False)
    if not fresh.has_perm("safety.review_purpose_exception"):
        raise PermissionDenied
    proposal = (
        PurposeExceptionProposal.objects.select_for_update(of=("self",))
        .select_related("action", "plan__inventory", "plan__action")
        .filter(pk=proposal_id, action__request=case)
        .first()
    )
    if not proposal:
        raise PermissionDenied
    if (
        case.kind != "erase"
        or case.status != "reviewing"
        or case.version != version
        or proposal.action.expected_version != version
        or proposal.expires_at <= timezone.now()
        or not complete_read(fresh, case)
        or not complete_response_read(fresh, case)
        or operation not in {"inspect", "review"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or (operation == "inspect" and outcome)
        or (operation == "review" and outcome not in {"approved", "rejected"})
    ):
        raise ValidationError(
            "Inspect current scoped exception / Consulta excepción de ámbito vigente"
        )
    subject_id = case.account_subject_id or (person.subject_id if person else None)
    if subject_id != proposal.subject_id or (
        proposal.plan.inventory.person_id != case.person_id
        or proposal.plan.inventory.account_subject_id != case.account_subject_id
        or proposal.plan.action.request_id != case.pk
        or proposal.plan.action.actor_id != proposal.action.actor_id
        or ErasureExecution.objects.filter(plan=proposal.plan).exists()
        or (proposal.plan.review_on and proposal.plan.review_on <= timezone.localdate())
    ):
        raise ValidationError("Exception scope changed / Ámbito de excepción cambiado")
    subject = User.objects.select_for_update().get(pk=subject_id)
    measures = list(
        PurposeRestriction.objects.select_for_update(of=("self",))
        .select_related("execution__action__request", "execution__review__plan__action")
        .filter(subject=subject, purpose="account_preferences", active=True)
        .order_by("pk")
    )
    for measure in measures:
        if not permitted(fresh, measure.execution.action.request):
            raise PermissionDenied
    # Proof and source are fetched after all waits, without inheriting proposer authority.
    fresh = authorize(user, case, review_permission=False)
    if not fresh.has_perm("safety.review_purpose_exception"):
        raise PermissionDenied
    proof = authorized_proof(case, person, "erase")
    manifest = source_manifest(person, case)
    if (
        proof.pk != proposal.proof_id
        or proof.pk != proposal.plan.inventory.proof_id
        or proposal.plan.inventory.action.expected_version != version
        or proposal.plan.source_digest != proposal.plan.inventory.source_digest
        or fingerprint(canonical(manifest)) != proposal.plan.source_digest
    ):
        raise ValidationError("Plan or proof changed / Plan o comprobación cambiados")
    signature = fingerprint(
        canonical(
            {
                "proposal": proposal.pk,
                "version": version,
                "operation": operation,
                "reason": reason,
                "outcome": outcome,
                "source": proposal.source_digest,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != fresh.pk
            or previous.operation != "exception_" + operation
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting replay / Reintento incompatible")
        body = proposal_contents(proposal, case, manifest, measures)
        result = (
            PurposeExceptionRead.objects.get(action=previous)
            if operation == "inspect"
            else PurposeExceptionReview.objects.get(action=previous)
        )
        return result, body if operation == "inspect" else None
    if operation == "review":
        if fresh.pk == proposal.action.actor_id:
            raise PermissionDenied("Independent reviewer required")
        if (
            PurposeExceptionReview.objects.filter(proposal=proposal).exists()
            or not PurposeExceptionRead.objects.filter(
                proposal=proposal,
                action__actor=fresh,
                action__expected_version=version,
                proof=proof,
                source_digest=proposal.source_digest,
            ).exists()
        ):
            raise ValidationError(
                "Inspect before independent review / Consulta antes de revisión independiente"
            )
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="exception_" + operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            body = proposal_contents(proposal, case, manifest, measures)
            fields = dict(
                action=action, proposal=proposal, proof=proof, source_digest=proposal.source_digest
            )
            result = (
                PurposeExceptionRead.objects.create(**fields)
                if operation == "inspect"
                else PurposeExceptionReview.objects.create(**fields, outcome=outcome)
            )
            fresh = authorize(user, case, review_permission=False)
            if not fresh.has_perm("safety.review_purpose_exception"):
                raise PermissionDenied
            return result, body if operation == "inspect" else None
    except IntegrityError as error:
        raise ValidationError(
            "Conflicting exception decision / Decisión de excepción incompatible"
        ) from error


@sensitive_variables()
def consume(user, case, person, subject, plan, manifest, purposes, proposal_id, action):
    """Caller holds scope locks; use and deletion share the enclosing transaction."""
    from django.db import connection

    if not connection.in_atomic_block:
        raise RuntimeError("Exception consumption requires the scoped execution transaction")
    fresh = authorize(user, case, review_permission=False)
    if not fresh.has_perm("safety.review_purpose_exception"):
        raise PermissionDenied
    proposal = (
        PurposeExceptionProposal.objects.select_for_update(of=("self",))
        .select_related("action", "plan__inventory", "plan__action")
        .filter(pk=proposal_id, action__request=case, subject=subject, plan=plan)
        .first()
    )
    if not proposal:
        raise ValidationError("Scoped exception unavailable / Excepción de ámbito no disponible")
    measures = list(
        PurposeRestriction.objects.select_for_update(of=("self",))
        .select_related("execution__action__request", "execution__review__plan__action")
        .filter(subject=subject, purpose="account_preferences", active=True)
        .order_by("pk")
    )
    review = (
        PurposeExceptionReview.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(proposal=proposal)
        .first()
    )
    proof = authorized_proof(case, person, "erase")
    manifest = source_manifest(person, case)
    if (
        not measures
        or not review
        or review.outcome != "approved"
        or review.consumed_action_id
        or proposal.action.actor_id != fresh.pk
        or review.action.actor_id == proposal.action.actor_id
        or review.action.request_id != case.pk
        or review.action.expected_version != case.version
        or review.proof_id != proof.pk
        or proposal.proof_id != proof.pk
        or review.source_digest != proposal.source_digest
        or proposal.plan.inventory.proof_id != proof.pk
        or proposal.plan.inventory.person_id != case.person_id
        or proposal.plan.inventory.account_subject_id != case.account_subject_id
        or proposal.plan.action.request_id != case.pk
        or proposal.plan.action.actor_id != fresh.pk
        or proposal.plan.source_digest != proposal.plan.inventory.source_digest
        or fingerprint(canonical(manifest)) != proposal.plan.source_digest
    ):
        raise ValidationError(
            "Current unused approval required / Aprobación vigente sin usar obligatoria"
        )
    approver = User.objects.get(pk=review.action.actor_id)
    authorize(approver, case, review_permission=False)
    if not approver.has_perm("safety.review_purpose_exception"):
        raise PermissionDenied
    for measure in measures:
        if not permitted(fresh, measure.execution.action.request) or not permitted(
            approver, measure.execution.action.request
        ):
            raise PermissionDenied
        execution = measure.execution
        bound = execution.account_subject_id or (
            execution.person.subject_id if execution.person_id else None
        )
        if bound != subject.pk:
            raise ValidationError("Restriction scope changed / Ámbito de restricción cambiado")
    body = proposal_contents(proposal, case, manifest, measures)
    try:
        decisions = unseal(plan.encrypted_decisions)["decisions"]
        review_reason = unseal(review.action.encrypted_reason)["reason"]
        if (
            body["purposes"] != sorted(purposes)
            or plan.action.payload_digest
            != fingerprint(
                canonical(
                    {
                        "inventory": str(plan.inventory_id),
                        "version": plan.action.expected_version,
                        "decisions": decisions,
                    }
                )
            )
            or review.action.operation != "exception_review"
            or review.action.payload_digest
            != fingerprint(
                canonical(
                    {
                        "proposal": proposal.pk,
                        "version": case.version,
                        "operation": "review",
                        "reason": review_reason,
                        "outcome": "approved",
                        "source": proposal.source_digest,
                    }
                )
            )
        ):
            raise ValueError
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError(
            "Approval integrity changed / Integridad de aprobación cambiada"
        ) from error
    fresh = authorize(user, case, review_permission=False)
    if not fresh.has_perm("safety.review_purpose_exception"):
        raise PermissionDenied
    # Source reconstruction and approval checks may outlive the proof. Require
    # the same current scoped proof immediately before consuming authorization.
    if authorized_proof(case, person, "erase").pk != proof.pk:
        raise ValidationError("Current scoped proof required / Comprobación de ámbito vigente obligatoria")
    review.consumed_action = action
    review.save(update_fields=["consumed_action"])
    return review
