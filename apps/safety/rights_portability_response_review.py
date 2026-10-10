"""Independent audited final draft inspection; no approval or closure yet."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .models import RightsAction, RightsPortabilityResponseDraft, RightsPortabilityResponseReview
from .rights import fingerprint
from .rights_exports import canonical, reviewer_case
from .rights_portability_export import one_export_validation
from .rights_portability_response_draft import checked_body, prepare
from .rights_portability_review import authorize
from .rights_responses import complete_response_read
from .rights_verification import authorized_proof, complete_read


def authorize_reviewer(user, case):
    actor = authorize(user, case)
    if not actor.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    return actor


@transaction.atomic
@one_export_validation
@sensitive_variables()
def inspect(user, case_id, version, draft_id, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Final draft inspection reason required")
    case, person, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.kind != "portability"
        or case.status != "reviewing"
        or case.version != version
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect current request and responses first")
    proof = authorized_proof(case, person, case.kind)
    draft = (
        RightsPortabilityResponseDraft.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=draft_id, request=case)
        .first()
    )
    if draft is None or draft.actor_id == actor.pk:
        raise PermissionDenied("Independent final response reviewer required")
    if (
        draft.case_version != version
        or draft.response_version != case.response_version
        or draft.proof_id != proof.pk
        or draft.expires_at <= timezone.now()
        or draft.purged_at
    ):
        raise ValidationError("Current final draft unavailable")
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "responses": case.response_version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "draft": draft.pk,
                "draft_action": draft.action.payload_digest,
                "text": draft.text_digest,
                "ciphertext": fingerprint(draft.encrypted_response),
                "export": str(draft.export_id),
                "export_digest": draft.export_digest,
                "coverage": draft.coverage_review_id,
                "coverage_digest": draft.coverage_digest,
                "proof": str(proof.pk),
                "reason": reason,
            }
        )
    )
    action = RightsAction.objects.filter(key=key).first()
    if action:
        if (
            action.request_id,
            action.actor_id,
            action.operation,
            action.expected_version,
            action.payload_digest,
        ) != (case.pk, actor.pk, "final_draft_read", version, signature):
            raise ValidationError("Conflicting final draft inspection key")
    else:
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=version,
                    operation="final_draft_read",
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting final draft inspection key") from error
    if checked_body(action.encrypted_reason) != {"reason": reason}:
        raise ValidationError("Final inspection reason changed")
    # Preserve original author epochs: a refreshed user must not bypass revocation.
    author = User.objects.get(pk=draft.actor_id)
    author.session_version = draft.original_session_version
    author.mfa_version = draft.original_mfa_version
    body = checked_body(draft.encrypted_response)
    if (
        not isinstance(body, dict)
        or set(body) != {"text", "simulation"}
        or body["simulation"] is not True
    ):
        raise ValidationError("Final response body changed")
    author_reason = checked_body(draft.action.encrypted_reason)
    if not isinstance(author_reason, dict) or set(author_reason) != {"reason"}:
        raise ValidationError("Final preparation reason changed")
    prepared = prepare(
        author,
        case.pk,
        version,
        case.response_version,
        draft.export_id,
        draft.action.key,
        author_reason["reason"],
        body["text"],
        True,
    )
    if prepared.pk != draft.pk:
        raise ValidationError("Final response draft changed")
    authorize_reviewer(user, case)
    if authorized_proof(case, person, case.kind).pk != proof.pk:
        raise ValidationError("Final review authorization changed")
    return draft, {"text": body["text"], "simulation": True, "export": str(draft.export_id)}


@transaction.atomic
@one_export_validation
@sensitive_variables()
def record(user, case_id, version, draft_id, read_id, key, reason, outcome):
    if (
        outcome not in {"approved", "rejected"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 200
    ):
        raise ValidationError("Final response review outcome and reason required")
    case, _, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=actor,
        expected_version=version,
        operation="final_draft_read",
    ).first()
    if read is None:
        raise ValidationError("Inspect the exact final response draft first")
    read_reason = checked_body(read.encrypted_reason)
    if not isinstance(read_reason, dict) or set(read_reason) != {"reason"}:
        raise ValidationError("Final inspection evidence changed")
    draft, _ = inspect(user, case.pk, version, draft_id, read.key, read_reason["reason"])
    ciphertext_digest = fingerprint(draft.encrypted_response)
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "draft": draft.pk,
                "draft_action": draft.action.payload_digest,
                "read": read.pk,
                "read_digest": read.payload_digest,
                "text": draft.text_digest,
                "ciphertext": ciphertext_digest,
                "reason": reason,
                "outcome": outcome,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id,
            previous.actor_id,
            previous.operation,
            previous.expected_version,
            previous.payload_digest,
        ) != (case.pk, actor.pk, "final_draft_review", version, signature):
            raise ValidationError("Conflicting final response review key")
        review = RightsPortabilityResponseReview.objects.filter(action=previous).first()
        if (
            review is None
            or review.draft_id != draft.pk
            or review.read_action_id != read.pk
            or review.text_digest != draft.text_digest
            or review.ciphertext_digest != ciphertext_digest
            or review.outcome != outcome
            or review.original_session_version != user.session_version
            or review.original_mfa_version != user.mfa_version
            or checked_body(previous.encrypted_reason) != {"reason": reason}
        ):
            raise ValidationError("Final response review evidence changed")
    else:
        if RightsPortabilityResponseReview.objects.filter(draft=draft).exists():
            raise ValidationError("Final response draft already reviewed")
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=version,
                    operation="final_draft_review",
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
                review = RightsPortabilityResponseReview.objects.create(
                    action=action,
                    draft=draft,
                    read_action=read,
                    text_digest=draft.text_digest,
                    ciphertext_digest=ciphertext_digest,
                    original_session_version=user.session_version,
                    original_mfa_version=user.mfa_version,
                    outcome=outcome,
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting final response review key") from error
    authorize_reviewer(user, case)
    from .rights_portability_response_evidence import validate_review

    validate_review(
        review,
        case,
        person=None if case.account_subject_id else case.person,
        require_approved=False,
    )
    return review
