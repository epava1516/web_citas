"""Independent audited information review; no final response or case closure."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsCopyInformation,
    RightsCopyInformationRead,
    RightsCopyInformationReview,
)
from .rights import fingerprint
from .rights_copy_information import validate_saved_evidence
from .rights_exports import canonical, reviewer_case, source_copy
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
                "review_copy_information",
            ]
        )
        or not permitted(fresh, case)
    ):
        raise PermissionDenied
    return fresh


@transaction.atomic
@sensitive_variables()
def record(user, case_id, information_id, key, version, operation, reason, outcome=""):
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    if (
        case.kind not in {"access", "portability"}
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
        RightsCopyInformation.objects.select_for_update(of=("self",))
        .select_related("action", "proof", "policy_document")
        .filter(pk=information_id, request=case)
        .first()
    )
    if row is None:
        raise PermissionDenied
    if row.actor_id == actor.pk:
        raise PermissionDenied("Independent reviewer required")
    proof = authorized_proof(case, person, case.kind)
    source_digest = fingerprint(canonical(source_copy(person, listing, case)))
    body_digest = fingerprint(row.encrypted_information)
    signature = fingerprint(
        canonical(
            {
                "information": row.pk,
                "version": version,
                "operation": operation,
                "reason": reason,
                "outcome": outcome,
                "source": source_digest,
                "body": body_digest,
                "policy": row.policy_digest,
                "session": user.session_version,
                "mfa": user.mfa_version,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous and (
        previous.request_id != case.pk
        or previous.actor_id != actor.pk
        or previous.operation != "copy_info_" + operation
        or previous.payload_digest != signature
    ):
        raise ValidationError("Conflicting information review key")
    read = None
    if operation == "review":
        read = (
            RightsCopyInformationRead.objects.filter(
                information=row,
                action__actor=actor,
                action__expected_version=version,
                proof=proof,
                source_digest=source_digest,
                information_digest=body_digest,
                policy_digest=row.policy_digest,
            )
            .order_by("-pk")
            .first()
        )
        if not read:
            raise ValidationError("Inspect this current information draft before review")
        if not previous and RightsCopyInformationReview.objects.filter(information=row).exists():
            raise ValidationError("Information draft already reviewed")
    try:
        with transaction.atomic():
            action = previous or RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=version,
                operation="copy_info_" + operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            # Audit exists before any private draft is decrypted; failure rolls it back.
            try:
                body = unseal(row.encrypted_information)
            except (InvalidToken, ValueError, TypeError) as error:
                raise ValidationError("Information unavailable") from error
            body = validate_saved_evidence(row, case, proof, source_digest, body)
            if (
                operation == "review"
                and outcome == "approved"
                and (
                    not row.policy_document_id
                    or case.kind == "portability"
                    or any(item["status"] != "reviewed" for item in body["access"].values())
                )
            ):
                raise ValidationError("Unresolved information or portability cannot be approved")
            fields = dict(
                action=action,
                original_session_version=user.session_version,
                original_mfa_version=user.mfa_version,
                information=row,
                proof=proof,
                source_digest=source_digest,
                information_digest=body_digest,
                policy_digest=row.policy_digest,
            )
            if previous:
                model = (
                    RightsCopyInformationRead
                    if operation == "inspect"
                    else RightsCopyInformationReview
                )
                result = model.objects.filter(
                    action=previous,
                    information=row,
                    proof=proof,
                    source_digest=source_digest,
                    information_digest=body_digest,
                    policy_digest=row.policy_digest,
                ).first()
                if not result or (operation == "review" and result.outcome != outcome):
                    raise ValidationError("Information review evidence unavailable")
            elif operation == "inspect":
                result = RightsCopyInformationRead.objects.create(**fields)
            else:
                result = RightsCopyInformationReview.objects.create(
                    **fields, read=read, outcome=outcome
                )
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
def validate_action_evidence(evidence, row, case, proof):
    """Validate an inspection/decision signature; caller retains access authorization."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Review evidence requires an atomic transaction")
    action = evidence.action
    operation = "review" if isinstance(evidence, RightsCopyInformationReview) else "inspect"
    outcome = evidence.outcome if operation == "review" else ""
    if (
        evidence.original_session_version is None
        or evidence.original_mfa_version is None
        or evidence.information_id != row.pk
        or evidence.proof_id != proof.pk
        or evidence.source_digest != row.source_digest
        or evidence.information_digest != fingerprint(row.encrypted_information)
        or evidence.policy_digest != row.policy_digest
        or action.request_id != case.pk
        or action.expected_version != case.version
        or action.actor_id == row.actor_id
        or action.operation != "copy_info_" + operation
        or (operation == "review" and outcome not in {"approved", "rejected"})
    ):
        raise ValidationError("Review evidence unavailable")
    try:
        reason = unseal(action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Review evidence unavailable") from error
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Review evidence unavailable")
    signature = fingerprint(
        canonical(
            {
                "information": row.pk,
                "version": action.expected_version,
                "operation": operation,
                "reason": reason,
                "outcome": outcome,
                "source": evidence.source_digest,
                "body": evidence.information_digest,
                "policy": evidence.policy_digest,
                "session": evidence.original_session_version,
                "mfa": evidence.original_mfa_version,
            }
        )
    )
    if signature != action.payload_digest:
        raise ValidationError("Review evidence changed")


@sensitive_variables()
def validate_approved_evidence(review, row, case, proof, source_digest, information):
    """Validate linked approval evidence; caller must audit and authorize delivery."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Approval evidence requires an atomic transaction")
    latest = (
        RightsCopyInformation.objects.filter(request=case).order_by("-created_at", "-pk").first()
    )
    if (
        case.kind != "access"
        or review.outcome != "approved"
        or review.information_id != row.pk
        or not row.policy_document_id
        or latest is None
        or latest.pk != row.pk
    ):
        raise ValidationError("Current approved access information required")
    inspection = (
        RightsCopyInformationRead.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=review.read_id)
        .first()
    )
    if (
        inspection is None
        or inspection.information_id != row.pk
        or inspection.action.actor_id != review.action.actor_id
        or inspection.action.expected_version != review.action.expected_version
    ):
        raise ValidationError("Approval inspection evidence unavailable")
    validate_action_evidence(inspection, row, case, proof)
    validate_action_evidence(review, row, case, proof)
    cleaned = validate_saved_evidence(row, case, proof, source_digest, information)
    if any(item["status"] != "reviewed" for item in cleaned["access"].values()):
        raise ValidationError("Unresolved access information")
    return cleaned
