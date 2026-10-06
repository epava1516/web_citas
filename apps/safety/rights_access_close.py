"""Atomic simulated final response/notice/closure bound to exact approved evidence."""

from copy import copy

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .models import (
    RightsAccessClosure,
    RightsAccessResponseReview,
    RightsAction,
    RightsNotice,
    RightsResponse,
)
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_access_response_evidence import validate_review
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case
from .rights_responses import complete_response_read


def signature(case_id, version, responses, actor_id, session, mfa, review, reason):
    return fingerprint(
        canonical(
            {
                "case": str(case_id),
                "version": version,
                "responses": responses,
                "actor": actor_id,
                "session": session,
                "mfa": mfa,
                "review": review.pk,
                "decision": review.action.payload_digest,
                "text": review.draft.text_digest,
                "reason": reason,
            }
        )
    )


def closure_for_export(case, export):
    """Metadata only; content/authority validation must follow the download audit."""
    if case.kind != "access" or case.status != "resolved":
        return None
    return (
        RightsAccessClosure.objects.select_for_update(of=("self",))
        .select_related(
            "review__draft__export",
            "review__draft__action",
            "review__action",
            "review__read_action",
            "action",
            "response",
        )
        .filter(
            action__request=case,
            review__draft__request=case,
            review__draft__export=export,
            closed_case_version=case.version,
            closed_response_version=case.response_version,
            channel_digest=case.receipt_digest,
        )
        .first()
    )


@sensitive_variables()
def validate_closure(row, case, person):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Final closure requires enclosing transaction")
    review, response, action = row.review, row.response, row.action
    draft = review.draft
    if (
        case.kind != "access"
        or case.status != "resolved"
        or case.version != row.closed_case_version
        or case.response_version != row.closed_response_version
        or row.closed_case_version != draft.case_version + 1
        or row.closed_response_version != draft.response_version + 1
        or row.channel_digest != case.receipt_digest
        or action.request_id != case.pk
        or action.actor_id != draft.actor_id
        or response.request_id != case.pk
        or response.actor_id != draft.actor_id
        or response.kind != "access_complete"
        or response.key != action.key
        or response.case_version != draft.case_version
        or response.response_version != row.closed_response_version
    ):
        raise ValidationError("Final closure binding changed")
    historical = copy(case)
    historical.version = draft.case_version
    historical.response_version = draft.response_version
    historical.status = "reviewing"
    historical.scope_status = "simulated_passed"
    body = validate_review(review, historical, person)
    require_complete_delivery(draft, body)
    reason = checked_body(action.encrypted_reason)
    if (
        not isinstance(reason, dict)
        or set(reason) != {"reason"}
        or not isinstance(reason["reason"], str)
        or not 20 <= len(reason["reason"].strip()) <= 200
    ):
        raise ValidationError("Final closure reason unavailable")
    expected = signature(
        case.pk,
        draft.case_version,
        draft.response_version,
        draft.actor_id,
        row.original_session_version,
        row.original_mfa_version,
        review,
        reason["reason"],
    )
    if (
        action.operation != "access_close"
        or action.expected_version != draft.case_version
        or action.payload_digest != expected
        or response.payload_digest != expected
        or row.original_session_version != draft.original_session_version
        or row.original_mfa_version != draft.original_mfa_version
        or checked_body(response.encrypted_reason) != reason
        or checked_body(response.encrypted_response) != body
    ):
        raise ValidationError("Final closure evidence changed")
    return body


@transaction.atomic
@sensitive_variables()
def close(user, case_id, version, response_version, review_id, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Final closure reason required")
    session, mfa = user.session_version, user.mfa_version
    case, person, _ = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session, mfa)
    if not actor.has_perm("safety.respond_rights_request") or case.assigned_to_id != actor.pk:
        raise PermissionDenied
    review = (
        RightsAccessResponseReview.objects.select_for_update(of=("self",))
        .select_related("action", "draft__action")
        .filter(pk=review_id, draft__request=case, draft__actor=actor)
        .first()
    )
    if review is None or review.outcome != "approved":
        raise ValidationError("Own independently approved final draft required")
    digest = signature(case.pk, version, response_version, actor.pk, session, mfa, review, reason)
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id,
            previous.actor_id,
            previous.expected_version,
            previous.operation,
            previous.payload_digest,
        ) != (case.pk, actor.pk, version, "access_close", digest):
            raise ValidationError("Conflicting final closure key")
        row = RightsAccessClosure.objects.filter(action=previous).first()
        if row is None or row.review_id != review.pk:
            raise ValidationError("Final closure unavailable")
        validate_closure(row, case, person)
        return row.response
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != response_version
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect current final request before closure")
    proof = can_prepare(actor, case, person)
    if proof.pk != review.draft.proof_id:
        raise ValidationError("Final closure authorization changed")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=version,
                operation="access_close",
                payload_digest=digest,
                encrypted_reason=seal({"reason": reason}),
            )
            body = validate_review(review, case, person)
            require_complete_delivery(review.draft, body)
            response = RightsResponse.objects.create(
                key=key,
                request=case,
                actor=actor,
                case_version=version,
                response_version=response_version + 1,
                kind="access_complete",
                payload_digest=digest,
                encrypted_reason=seal({"reason": reason}),
                encrypted_response=seal(body),
            )
            payload = checked_body(case.encrypted_payload)
            if payload.get("email"):
                RightsNotice.objects.create(
                    response=response,
                    encrypted_payload=seal(
                        {
                            "recipient": payload["email"],
                            "subject": "Respuesta privada / Private response",
                            "body": "Hay una respuesta disponible en tu acuse privado. A response is available in your private receipt.",
                        }
                    ),
                )
            row = RightsAccessClosure.objects.create(
                action=action,
                response=response,
                review=review,
                closed_case_version=version + 1,
                closed_response_version=response_version + 1,
                channel_digest=case.receipt_digest,
                original_session_version=session,
                original_mfa_version=mfa,
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting final closure key") from error
    case.version += 1
    case.response_version += 1
    case.status = "resolved"
    case.scope_status = "unverified"
    case.save(update_fields=["version", "response_version", "status", "scope_status"])
    fresh_authority(actor, case, session, mfa)
    if not User.objects.get(pk=actor.pk).has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    validate_closure(row, case, person)
    return response


def require_complete_delivery(draft, body):
    """Legacy partial drafts must never pass the integrated access completion gate."""
    package = body.get("access_package")
    if (
        not draft.coverage_review_id
        or not isinstance(package, dict)
        or package.get("schema") != "access-delivery-v1"
        or package.get("export") != str(draft.export_id)
        or package.get("partial") is not False
        or package.get("pending") != []
    ):
        raise ValidationError("Complete reviewed access delivery package required")
    # validate_review has already reconstructed the package from actual subject data.
    # Its pending scopes are computed by the producer; caller flags cannot clear them.
