"""Independent audited portability assessment review; no final response or case closure."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsPortabilityAssessment,
    RightsPortabilityRead,
    RightsPortabilityReview,
)
from .rights import fingerprint
from .rights_exports import canonical, reviewer_case, source_copy
from .rights_portability import validate_assessment_evidence
from .rights_responses import complete_response_read
from .rights_scope import permitted
from .rights_verification import authorized_proof, complete_read


def authorize(user, case):
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.mfa_enabled
        or fresh.session_version != user.session_version
        or fresh.mfa_version != user.mfa_version
        or not all(
            fresh.has_perm("safety." + name)
            for name in [
                "review_rights_request",
                "execute_rights_request",
                "review_portability",
            ]
        )
        or not permitted(fresh, case)
    ):
        raise PermissionDenied
    return fresh


@transaction.atomic
@sensitive_variables()
def record(user, case_id, assessment_id, key, version, operation, reason, outcome=""):
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    if (
        case.kind != "portability"
        or case.status != "reviewing"
        or case.version != version
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
        or operation not in {"inspect", "review"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or (operation == "inspect" and outcome)
        or (operation == "review" and outcome not in {"approved", "rejected"})
    ):
        raise ValidationError("Inspect current request and provide a valid review action")
    row = (
        RightsPortabilityAssessment.objects.select_for_update(of=("self",))
        .select_related("action", "proof")
        .filter(pk=assessment_id, request=case)
        .first()
    )
    if row is None:
        raise PermissionDenied
    if row.actor_id == actor.pk:
        raise PermissionDenied("Independent reviewer required")
    proof = authorized_proof(case, person, case.kind)
    source_digest = fingerprint(canonical(source_copy(person, listing, case)))
    body_digest = fingerprint(row.encrypted_assessment)
    previous = RightsAction.objects.filter(key=key).first()
    read = None
    if operation == "review":
        reads = RightsPortabilityRead.objects.filter(
            assessment=row,
            action__actor=actor,
            action__expected_version=version,
            proof=proof,
            source_digest=source_digest,
            assessment_digest=body_digest,
        )
        if previous:
            reads = reads.filter(
                pk__in=RightsPortabilityReview.objects.filter(action=previous).values("read_id")
            )
        read = reads.order_by("-pk").first()
        if not read:
            raise ValidationError("Inspect this current assessment before review")
        validate_review_evidence(read, row, case, proof)
    signature = fingerprint(
        canonical(
            {
                "assessment": row.pk,
                "version": version,
                "operation": operation,
                "reason": reason,
                "outcome": outcome,
                "source": source_digest,
                "body": body_digest,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "read": read.pk if read else None,
            }
        )
    )
    if previous and (
        previous.request_id != case.pk
        or previous.actor_id != actor.pk
        or previous.operation != "portability_" + operation
        or previous.payload_digest != signature
    ):
        raise ValidationError("Conflicting portability review key")
    if (
        operation == "review"
        and not previous
        and RightsPortabilityReview.objects.filter(assessment=row).exists()
    ):
        raise ValidationError("Assessment already reviewed")
    try:
        with transaction.atomic():
            action = previous or RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=version,
                operation="portability_" + operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            # Audit exists before any private draft is decrypted; failure rolls it back.
            try:
                body = unseal(row.encrypted_assessment)
            except (InvalidToken, ValueError, TypeError) as error:
                raise ValidationError("Information unavailable") from error
            body = validate_assessment_evidence(row, case, proof, source_digest, body)
            if (
                operation == "review"
                and outcome == "approved"
                and any(item["status"] == "pending" for item in body.values())
            ):
                raise ValidationError("Pending portability datasets cannot be approved")

            fields = dict(
                action=action,
                original_session_version=user.session_version,
                original_mfa_version=user.mfa_version,
                assessment=row,
                proof=proof,
                source_digest=source_digest,
                assessment_digest=body_digest,
            )
            if previous:
                model = RightsPortabilityRead if operation == "inspect" else RightsPortabilityReview
                result = model.objects.filter(
                    action=previous,
                    assessment=row,
                    proof=proof,
                    source_digest=source_digest,
                    assessment_digest=body_digest,
                ).first()
                if not result or (operation == "review" and result.outcome != outcome):
                    raise ValidationError("Information review evidence unavailable")
            elif operation == "inspect":
                result = RightsPortabilityRead.objects.create(**fields)
            else:
                result = RightsPortabilityReview.objects.create(
                    **fields, read=read, outcome=outcome
                )
            validate_review_evidence(result, row, case, proof)
            authorize(user, case)
            if (
                authorized_proof(case, person, case.kind).pk != proof.pk
                or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
            ):
                raise ValidationError("Information source changed")
            return result, body if operation == "inspect" else None
    except IntegrityError as error:
        raise ValidationError("Conflicting information review") from error


@sensitive_variables()
def validate_review_evidence(evidence, row, case, proof):
    """Validate a historical read/decision signature; does not grant access."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Portability evidence validation requires atomic transaction")
    action = evidence.action
    operation = "review" if isinstance(evidence, RightsPortabilityReview) else "inspect"
    outcome = evidence.outcome if operation == "review" else ""
    if (
        evidence.assessment_id != row.pk
        or evidence.proof_id != proof.pk
        or evidence.source_digest != row.source_digest
        or evidence.assessment_digest != fingerprint(row.encrypted_assessment)
        or action.request_id != case.pk
        or action.expected_version != case.version
        or action.actor_id == row.actor_id
        or action.operation != "portability_" + operation
        or (operation == "review" and outcome not in {"approved", "rejected"})
    ):
        raise ValidationError("Portability review evidence unavailable")
    try:
        reason = unseal(action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Portability review evidence unavailable") from error
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Portability review evidence unavailable")
    signature = fingerprint(
        canonical(
            {
                "assessment": row.pk,
                "version": action.expected_version,
                "operation": operation,
                "reason": reason,
                "outcome": outcome,
                "source": evidence.source_digest,
                "body": evidence.assessment_digest,
                "session": evidence.original_session_version,
                "mfa": evidence.original_mfa_version,
                "read": evidence.read_id if operation == "review" else None,
            }
        )
    )
    if action.payload_digest != signature:
        raise ValidationError("Portability review evidence changed")


@sensitive_variables()
def validate_approved_assessment(review, row, case, proof, source_digest, body):
    """Validate approved draft evidence; caller must separately authorize and audit use."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Approval validation requires atomic transaction")
    from .evidence_chain import require_runtime_chain

    require_runtime_chain(case)
    latest = (
        RightsPortabilityAssessment.objects.filter(request=case)
        .order_by("-created_at", "-pk")
        .first()
    )
    if (
        review.outcome != "approved"
        or review.assessment_id != row.pk
        or latest is None
        or latest.pk != row.pk
    ):
        raise ValidationError("Current approved portability assessment required")
    inspection = (
        RightsPortabilityRead.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=review.read_id)
        .first()
    )
    if (
        not inspection
        or inspection.assessment_id != row.pk
        or inspection.action.actor_id != review.action.actor_id
        or inspection.action.expected_version != review.action.expected_version
    ):
        raise ValidationError("Portability approval inspection unavailable")
    validate_review_evidence(inspection, row, case, proof)
    validate_review_evidence(review, row, case, proof)
    cleaned = validate_assessment_evidence(row, case, proof, source_digest, body)
    if any(item["status"] == "pending" for item in cleaned.values()):
        raise ValidationError("Unresolved portability datasets")
    return cleaned
