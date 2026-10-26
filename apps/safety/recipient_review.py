"""Independent audited review of recipient assessments; never closes a rights case."""

import json
import uuid
from functools import partial

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsRectificationRecipientAssessment,
    RightsRectificationRecipientReview,
)
from .recipient_assessments import validate_decisions
from .rectification_authority import capture_authority
from .rectification_recipients import execution_scope_matches, snapshot
from .rectification_review import permission as base_permission
from .rights import fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read


def permission(user):
    base_permission(user)
    if not user.has_perm("safety.review_recipient_assessment"):
        raise PermissionDenied


@sensitive_variables()
def current(user, case_id, assessment_id, version, *, entry_authority=None):
    authority = (
        entry_authority if entry_authority is not None
        else capture_authority(user, review=True, recipient_review=True)
    )
    permission(user)
    case, person, _ = locked_case(case_id, lock_listing=True)
    check_authority = partial(authority, case)
    check_authority()
    if not permitted(user, case):
        raise PermissionDenied
    assessment = (
        RightsRectificationRecipientAssessment.objects.select_for_update()
        .select_related("action", "inventory__execution")
        .filter(
            pk=assessment_id,
            action__request=case,
            inventory__execution__notification__review__proposal__person=person,
            inventory__execution__notification__review__proposal__account_subject_id=case.account_subject_id,
        )
        .first()
    )
    check_authority()
    if not assessment:
        raise ValidationError("Assessment unavailable / Evaluación no disponible")
    if assessment.action.actor_id == user.pk:
        raise PermissionDenied("Independent reviewer required")
    if (
        case.kind != "rectify"
        or case.status != "reviewing"
        or case.version != version
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
        or not complete_response_read(user, case)
        or not execution_scope_matches(
            case, person, assessment.inventory.execution, check_authority=check_authority,
        )
    ):
        raise ValidationError(
            "Inspect current assigned assessment / Consulta la evaluación asignada vigente"
        )
    latest = (
        RightsRectificationRecipientAssessment.objects.filter(
            inventory__execution=assessment.inventory.execution
        )
        .order_by("-created_at", "-pk")
        .first()
    )
    proof = authorized_proof(case, person, "rectify")
    data = snapshot(person, assessment.inventory.execution, case, check_authority=check_authority)
    check_authority()
    proof = authorized_proof(case, person, "rectify")
    source = fingerprint(json.dumps(data, sort_keys=True))
    if (
        latest.pk != assessment.pk
        or proof.created_at <= assessment.created_at
        or source != assessment.source_digest
        or source != assessment.inventory.source_digest
    ):
        raise ValidationError(
            "Fresh proof and unchanged recipient history required / Nueva comprobación e historial vigente obligatorios"
        )
    check_authority()
    decisions = validate_decisions(data, unseal(assessment.encrypted_decisions))
    check_authority()
    authorized_proof(case, person, "rectify")
    return case, assessment, proof, data, decisions


def stamp(assessment, proof, decisions):
    return fingerprint(
        json.dumps(
            {
                "assessment": assessment.pk,
                "proof": str(proof.pk),
                "source": assessment.source_digest,
                "decisions": fingerprint(json.dumps(decisions, sort_keys=True)),
            },
            sort_keys=True,
        )
    )


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, assessment_id, version, purpose):
    authority = capture_authority(user, review=True, recipient_review=True)
    case, assessment, proof, data, decisions = current(
        user, case_id, assessment_id, version, entry_authority=authority,
    )
    check_authority = partial(authority, case)
    if not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Access purpose required / Motivo de consulta obligatorio")
    check_authority()
    authorized_proof(case, case.person, "rectify")
    RightsAction.objects.create(
        key=uuid.uuid4(),
        request=case,
        actor=user,
        expected_version=version,
        operation="recipient_check_read",
        payload_digest=stamp(assessment, proof, decisions),
        encrypted_reason=seal({"purpose": purpose}),
    )
    check_authority()
    authorized_proof(case, case.person, "rectify")
    return data, decisions


@transaction.atomic
@sensitive_variables()
def review(user, case_id, assessment_id, key, version, outcome, reason):
    authority = capture_authority(user, review=True, recipient_review=True)
    permission(user)
    case, person, _ = locked_case(case_id, lock_listing=True)
    check_authority = partial(authority, case)
    check_authority()
    if not permitted(user, case):
        raise PermissionDenied
    assessment = (
        RightsRectificationRecipientAssessment.objects.filter(
            pk=assessment_id,
            action__request=case,
            inventory__execution__notification__review__proposal__person=person,
            inventory__execution__notification__review__proposal__account_subject_id=case.account_subject_id,
        )
        .select_related("action")
        .first()
    )
    if not assessment or assessment.action.actor_id == user.pk:
        raise PermissionDenied
    signature = fingerprint(
        json.dumps(
            {"assessment": assessment_id, "version": version, "outcome": outcome, "reason": reason},
            sort_keys=True,
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "recipients_review"
            and previous.payload_digest == signature
        ):
            result = RightsRectificationRecipientReview.objects.get(action=previous)
            check_authority()
            return result
        raise ValidationError("Conflicting review key / Clave incompatible")
    case, assessment, proof, _, decisions = current(
        user, case_id, assessment_id, version, entry_authority=authority,
    )
    if (
        outcome not in {"accepted", "rejected"}
        or not 20 <= len(reason.strip()) <= 2000
        or RightsRectificationRecipientReview.objects.filter(assessment=assessment).exists()
        or not RightsAction.objects.filter(
            request=case,
            actor=user,
            expected_version=version,
            operation="recipient_check_read",
            payload_digest=stamp(assessment, proof, decisions),
        ).exists()
    ):
        raise ValidationError(
            "Read assessment before motivated review / Consulta la evaluación antes de revisión motivada"
        )
    check_authority()
    authorized_proof(case, person, "rectify")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="recipients_review",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = RightsRectificationRecipientReview.objects.create(
                assessment=assessment,
                action=action,
                proof=proof,
                outcome=outcome,
                source_digest=assessment.source_digest,
                decisions_digest=fingerprint(json.dumps(decisions, sort_keys=True)),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting recipient review / Revisión incompatible") from error
    check_authority()
    authorized_proof(case, person, "rectify")
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    check_authority()
    return result
