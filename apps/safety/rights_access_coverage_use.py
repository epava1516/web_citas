"""Consume exact independently approved accounting; no complete-access authority."""

from copy import copy

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .models import RightsAccessCoverageReview, RightsExportInformationBinding
from .rights import fingerprint
from .rights_access_coverage import compile_coverage
from .rights_access_coverage_review import audit, signature
from .rights_access_coverage_store import required_references
from .rights_access_evidence_refs import bind_references
from .rights_access_reference_bodies import validated_bodies
from .rights_access_response_draft import checked_body
from .rights_access_response_review import authorize_reviewer
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_information_export import validate_export_binding
from .rights_portability_export import validate_transport
from .rights_responses import complete_response_read
from .rights_verification import complete_read


@sensitive_variables()
def validate_approval(review, case, person, listing):
    """Caller has authorized/audited and locked canonical subject and request.

    Accepts the exact reviewing snapshot; a future closure must supply its bound
    historical snapshot, never use this accounting approval as whole-access proof.
    """
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Approval validation requires enclosing transaction")
    row, export = review.coverage, review.coverage.export
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or row.request_id != case.pk
        or case.version != row.case_version
        or case.response_version != row.response_version
        or case.assigned_to_id != row.actor_id
        or row.purged_at
        or row.expires_at <= timezone.now()
        or review.outcome != "approved"
    ):
        raise ValidationError("Current approved access accounting required")
    author = User.objects.get(pk=row.actor_id)
    author.session_version, author.mfa_version = (
        row.original_session_version,
        row.original_mfa_version,
    )
    fresh_authority(author, case, author.session_version, author.mfa_version)
    if (
        not author.is_active
        or not author.has_perm("safety.respond_rights_request")
        or not complete_response_read(author, case)
    ):
        raise PermissionDenied
    proof = can_prepare(author, case, person)
    binding = (
        RightsExportInformationBinding.objects.select_for_update().filter(export=export).first()
    )
    if (
        not binding
        or binding.review_id != row.information_review_id
        or export.action.request_id != case.pk
        or export.action.actor_id != author.pk
        or proof.pk != row.proof_id
        or proof.pk == export.proof_id
        or proof.created_at <= export.created_at
        or row.expires_at > min(export.expires_at, proof.expires_at)
        or row.export_digest != export.action.payload_digest
        or export.channel_digest != case.receipt_digest
        or export.purged_at
        or export.expires_at <= timezone.now()
    ):
        raise ValidationError("Access accounting references changed")
    body = checked_body(row.encrypted_coverage)
    reason = checked_body(row.action.encrypted_reason)
    if (
        not isinstance(body, dict)
        or set(body)
        != {
            "delivered",
            "declarations",
            "references",
            "source",
            "delivery",
            "accounting",
            "bound_references",
        }
        or not isinstance(reason, dict)
        or set(reason) != {"reason"}
    ):
        raise ValidationError("Access accounting encrypted evidence changed")
    payload = {
        field: body[field]
        for field in ["delivered", "declarations", "references", "source", "delivery"]
    }
    binding_digest = fingerprint(
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
    prepared_digest = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "responses": case.response_version,
                "actor": author.pk,
                "session": author.session_version,
                "mfa": author.mfa_version,
                "export": str(export.pk),
                "export_digest": export.action.payload_digest,
                "information": binding.review_id,
                "binding": binding_digest,
                "proof": str(proof.pk),
                "payload": payload,
                "reason": reason["reason"],
            }
        )
    )
    if row.binding_digest != binding_digest or (
        row.action.request_id,
        row.action.actor_id,
        row.action.expected_version,
        row.action.operation,
        row.action.payload_digest,
    ) != (case.pk, author.pk, case.version, "access_coverage", prepared_digest):
        raise ValidationError("Access accounting preparation signature changed")
    historical = copy(case)
    historical.version = export.case_version
    validate_export_binding(historical, person, export)
    validate_transport(export, body["delivered"])
    source = source_copy(person, listing, case)
    accounting = compile_coverage(
        source, body["delivered"], body["declarations"], body["source"], body["delivery"]
    )
    if (
        body["source"] != binding.source_digest
        or row.accounting_digest != accounting["accounting_digest"]
        or body["accounting"] != accounting
        or not isinstance(body["references"], dict)
        or set(body["references"]) != required_references(body["declarations"])
    ):
        raise ValidationError("Access accounting scope changed")
    facts = bind_references(case, export, body["references"])
    if facts != body["bound_references"]:
        raise ValidationError("Access accounting referenced evidence changed")
    evidence = validated_bodies(case, row, author, source, facts)
    reviewer = User.objects.get(pk=review.action.actor_id)
    reviewer.session_version, reviewer.mfa_version = (
        review.original_session_version,
        review.original_mfa_version,
    )
    authorize_reviewer(reviewer, case)
    if (
        reviewer.pk == author.pk
        or not complete_read(reviewer, case)
        or not complete_response_read(reviewer, case)
    ):
        raise ValidationError("Independent current accounting review required")
    read, action = review.read_action, review.action
    read_reason, decision_reason = (
        checked_body(read.encrypted_reason),
        checked_body(action.encrypted_reason),
    )
    for item in [read_reason, decision_reason]:
        if (
            not isinstance(item, dict)
            or set(item) != {"reason"}
            or not isinstance(item["reason"], str)
            or not 20 <= len(item["reason"].strip()) <= 200
        ):
            raise ValidationError("Access accounting review reason changed")
    read_digest = signature(case, reviewer, row, reviewer, read_reason["reason"])
    decision_digest = fingerprint(
        canonical(
            {
                "read": read.pk,
                "read_digest": read.payload_digest,
                "inspection": signature(case, reviewer, row, reviewer, decision_reason["reason"]),
                "outcome": review.outcome,
            }
        )
    )
    if (
        (read.request_id, read.actor_id, read.expected_version, read.operation, read.payload_digest)
        != (case.pk, reviewer.pk, case.version, "access_cover_read", read_digest)
        or (
            action.request_id,
            action.actor_id,
            action.expected_version,
            action.operation,
            action.payload_digest,
        )
        != (case.pk, reviewer.pk, case.version, "access_cover_review", decision_digest)
        or review.accounting_digest != row.accounting_digest
        or review.ciphertext_digest != fingerprint(row.encrypted_coverage)
    ):
        raise ValidationError("Access accounting review signatures changed")
    fresh_authority(author, case, author.session_version, author.mfa_version)
    authorize_reviewer(reviewer, case)
    return body | {"original": source, "evidence_bodies": evidence}


@transaction.atomic
@sensitive_variables()
def consume(user, case_id, version, response_version, review_id, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated approval consumption required")
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.assigned_to_id != actor.pk
        or case.version != version
        or case.response_version != response_version
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Current assigned access response context required")
    review = (
        RightsAccessCoverageReview.objects.select_for_update(of=("self",))
        .select_related("coverage__action", "coverage__export__action", "action", "read_action")
        .filter(pk=review_id, coverage__request=case, coverage__actor=actor, outcome="approved")
        .first()
    )
    if not review:
        raise ValidationError("Own independently approved accounting required")
    digest = fingerprint(
        canonical(
            {
                "review": review.pk,
                "decision": review.action.payload_digest,
                "coverage": review.coverage.accounting_digest,
                "ciphertext": fingerprint(review.coverage.encrypted_coverage),
                "version": version,
                "responses": response_version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "reason": reason,
            }
        )
    )
    audit(case, actor, version, key, "access_cover_use", digest, reason)
    body = validate_approval(review, case, person, listing)
    authorize_reviewer(user, case)
    return review, body
