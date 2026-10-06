"""Historical draft validation; caller must authorize/audit and hold canonical locks."""

from copy import copy

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .models import RightsExportInformationBinding
from .rights import fingerprint
from .rights_access_response_draft import checked_body
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical
from .rights_response_text import checked_response_text
from .rights_responses import complete_response_read
from .rights_verification import authorized_proof, complete_read


@sensitive_variables()
def validate_draft(draft, case, person):
    """case is the exact preparation snapshot, never a replacement for caller authority."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Final draft validation requires enclosing transaction")
    if (
        draft.request_id != case.pk
        or case.kind != "access"
        or case.status != "reviewing"
        or draft.case_version != case.version
        or draft.response_version != case.response_version
        or case.assigned_to_id != draft.actor_id
        or draft.purged_at
        or draft.expires_at <= timezone.now()
    ):
        raise ValidationError("Final response preparation context changed")
    actor = User.objects.get(pk=draft.actor_id)
    fresh_authority(actor, case, draft.original_session_version, draft.original_mfa_version)
    if not actor.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    if not complete_response_read(actor, case):
        raise ValidationError("Final preparation response reads unavailable")
    proof = can_prepare(actor, case, person)
    export = draft.export
    binding = (
        RightsExportInformationBinding.objects.select_for_update().filter(export=export).first()
    )
    binding_digest = (
        fingerprint(
            canonical(
                {
                    field: getattr(binding, field)
                    for field in [
                        "source_digest",
                        "information_digest",
                        "policy_digest",
                        "inspection_digest",
                        "decision_digest",
                    ]
                }
            )
        )
        if binding
        else None
    )
    if (
        binding is None
        or binding.review_id is None
        or draft.proof_id != proof.pk
        or proof.pk == export.proof_id
        or proof.created_at <= export.created_at
        or export.action.request_id != case.pk
        or export.action.actor_id != actor.pk
        or draft.export_digest != export.action.payload_digest
        or draft.information_review_id != binding.review_id
        or draft.binding_digest != binding_digest
        or export.channel_digest != case.receipt_digest
        or draft.expires_at > min(export.expires_at, proof.expires_at)
    ):
        raise ValidationError("Final response preparation references changed")
    accounting_signature = {}
    if draft.coverage_review_id:
        review = draft.coverage_review
        if (
            review.coverage.export_id != export.pk
            or review.coverage.proof_id != proof.pk
            or review.coverage.actor_id != actor.pk
            or review.coverage.request_id != case.pk
            or draft.expires_at > review.coverage.expires_at
        ):
            raise ValidationError("Final response accounting references changed")
        from .rights_access_coverage_use import validate_approval
        from .rights_exports import reviewer_case

        _, scoped_person, listing = reviewer_case(actor, case.pk)
        validate_approval(review, case, scoped_person, listing)
        accounting_signature = {
            "access_accounting_review": review.pk,
            "access_accounting_decision": review.action.payload_digest,
            "access_accounting_digest": review.coverage.accounting_digest,
        }
    body, reason_body = (
        checked_body(draft.encrypted_response),
        checked_body(draft.action.encrypted_reason),
    )
    if (
        not isinstance(body, dict)
        or set(body) != {"text", "simulation"}
        or body["simulation"] is not True
        or not isinstance(reason_body, dict)
        or set(reason_body) != {"reason"}
    ):
        raise ValidationError("Final response preparation body changed")
    checked_response_text(reason_body["reason"], body["text"], True)
    text_digest = fingerprint(canonical(body))
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "responses": case.response_version,
                "actor": actor.pk,
                "session": draft.original_session_version,
                "mfa": draft.original_mfa_version,
                "export": str(export.pk),
                "export_digest": export.action.payload_digest,
                "information_review": binding.review_id,
                "information_binding_digest": binding_digest,
                "proof": str(proof.pk),
                "text": text_digest,
                "reason": reason_body["reason"],
                **accounting_signature,
            }
        )
    )
    action = draft.action
    if (
        draft.text_digest != text_digest
        or action.request_id != case.pk
        or action.actor_id != actor.pk
        or action.expected_version != case.version
        or action.operation != "access_draft"
        or action.payload_digest != signature
    ):
        raise ValidationError("Final response preparation signature changed")
    historical = copy(case)
    historical.version = export.case_version
    from .rights_access_response_draft import validate_export_binding

    validate_export_binding(historical, person, export)
    fresh_authority(actor, case, draft.original_session_version, draft.original_mfa_version)
    if not User.objects.get(pk=actor.pk).has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    if can_prepare(actor, case, person).pk != proof.pk:
        raise ValidationError("Final preparation authorization changed")
    return body


@sensitive_variables()
def validate_review(review, case, person, *, require_approved=True):
    """Validate exact original inspection/decision on the audited preparation snapshot."""
    if type(require_approved) is not bool:
        raise ValidationError("Invalid final response review mode")
    draft = review.draft
    body = validate_draft(draft, case, person)
    from .rights_access_response_review import authorize_reviewer

    actor = User.objects.get(pk=review.action.actor_id)
    actor.session_version = review.original_session_version
    actor.mfa_version = review.original_mfa_version
    authorize_reviewer(actor, case)
    if (
        actor.pk == draft.actor_id
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Independent current final response review required")
    proof = authorized_proof(case, person, case.kind)
    if (
        proof.pk != draft.proof_id
        or review.outcome not in {"approved", "rejected"}
        or (require_approved and review.outcome != "approved")
    ):
        raise ValidationError("Approved final response review required")
    read, action = review.read_action, review.action
    read_reason, decision_reason = (
        checked_body(read.encrypted_reason),
        checked_body(action.encrypted_reason),
    )
    for reason in (read_reason, decision_reason):
        if (
            not isinstance(reason, dict)
            or set(reason) != {"reason"}
            or not isinstance(reason["reason"], str)
            or not 20 <= len(reason["reason"].strip()) <= 200
        ):
            raise ValidationError("Final response review reason changed")
    ciphertext_digest = fingerprint(draft.encrypted_response)
    read_signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "responses": case.response_version,
                "actor": actor.pk,
                "session": actor.session_version,
                "mfa": actor.mfa_version,
                "draft": draft.pk,
                "draft_action": draft.action.payload_digest,
                "text": draft.text_digest,
                "ciphertext": ciphertext_digest,
                "export": str(draft.export_id),
                "export_digest": draft.export_digest,
                "information_review": draft.information_review_id,
                "information_binding_digest": draft.binding_digest,
                "proof": str(proof.pk),
                "reason": read_reason["reason"],
            }
        )
    )
    decision_signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "actor": actor.pk,
                "session": actor.session_version,
                "mfa": actor.mfa_version,
                "draft": draft.pk,
                "draft_action": draft.action.payload_digest,
                "read": read.pk,
                "read_digest": read.payload_digest,
                "text": draft.text_digest,
                "ciphertext": ciphertext_digest,
                "reason": decision_reason["reason"],
                "outcome": review.outcome,
            }
        )
    )
    if (
        review.text_digest != draft.text_digest
        or review.ciphertext_digest != ciphertext_digest
        or (
            read.request_id,
            read.actor_id,
            read.expected_version,
            read.operation,
            read.payload_digest,
        )
        != (case.pk, actor.pk, case.version, "access_draft_read", read_signature)
        or (
            action.request_id,
            action.actor_id,
            action.expected_version,
            action.operation,
            action.payload_digest,
        )
        != (case.pk, actor.pk, case.version, "access_draft_review", decision_signature)
    ):
        raise ValidationError("Final response review signatures changed")
    authorize_reviewer(actor, case)
    return body
