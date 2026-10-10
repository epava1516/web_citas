"""Historical coverage evidence; caller authorizes and audits access before use."""

from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import unseal
from .models import (
    RightsPortabilityCoverage,
    RightsPortabilityCoverageRead,
    RightsPortabilitySelectionRead,
)
from .rights import fingerprint
from .rights_exports import canonical
from .rights_portability_coverage import compile_coverage
from .rights_portability_coverage_page import coverage_page
from .rights_portability_coverage_pages import baseline_body
from .rights_portability_coverage_read_gate import required_pages
from .rights_portability_review import authorize, validate_approved_assessment
from .rights_portability_selection_review import validate_approved_selection, validate_evidence
from .rights_portability_selection_store import validate_selection_evidence


def checked_reason(action):
    try:
        body = unseal(action.encrypted_reason)
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Coverage evidence reason unavailable") from error
    return checked_reason_body(body)


def checked_reason_body(body):
    try:
        reason = body["reason"]
    except (KeyError, TypeError) as error:
        raise ValidationError("Coverage evidence reason unavailable") from error
    if (
        not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 200
        or body != {"reason": reason}
    ):
        raise ValidationError("Coverage evidence reason changed")
    return reason


def checked_action(action, case, actor_id, operation, signature):
    if (
        action.request_id,
        action.actor_id,
        action.expected_version,
        action.operation,
        action.payload_digest,
    ) != (case.pk, actor_id, case.version, operation, signature):
        raise ValidationError("Coverage evidence action changed")


@sensitive_variables()
def validate_coverage_pages(row, case, proof, source, user, ids, *, allow_partial=False):
    """Validate original page evidence against one locked source; never create reads."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Coverage page evidence requires enclosing transaction")
    actor = authorize(user, case)
    if (
        row.request_id != case.pk
        or row.proof_id != proof.pk
        or actor.pk == row.actor_id
        or fingerprint(canonical(source)) != row.source_digest
    ):
        raise ValidationError("Coverage page source or authority changed")
    selected_review = row.selection_review
    selection = selected_review.selection
    assessment_review = selection.assessment_review
    assessment = validate_approved_assessment(
        assessment_review,
        assessment_review.assessment,
        case,
        proof,
        row.source_digest,
        unseal(assessment_review.assessment.encrypted_assessment),
    )
    validate_approved_selection(selected_review, selection, case, proof)
    facts = validate_selection_evidence(selection, assessment_review, case)
    body = baseline_body(row, case, User.objects.get(pk=row.actor_id), selection, selected_review)
    compiled = compile_coverage(
        source,
        assessment,
        facts["selection"],
        body["omissions"],
        facts.get("images", []),
        body["image_omissions"],
        field_evidence=facts.get("field_evidence"),
        allow_partial=allow_partial,
    )
    # Identical arguments when partial coverage is already allowed: same deterministic result.
    summary = compiled if allow_partial else compile_coverage(
        source,
        assessment,
        facts["selection"],
        body["omissions"],
        facts.get("images", []),
        body["image_omissions"],
        field_evidence=facts.get("field_evidence"),
        allow_partial=True,
    )
    if (
        not isinstance(ids, list)
        or any(type(pk) is not int for pk in ids)
        or len(set(ids)) != len(ids)
    ):
        raise ValidationError("Invalid coverage read references")
    reads = {
        read.pk: read
        for read in RightsPortabilityCoverageRead.objects.select_related("action").filter(
            pk__in=ids
        )
    }
    required = required_pages(source)
    if len(reads) != len(ids) or len(ids) != len(required):
        raise ValidationError("Every original coverage page required")
    child_keys = [
        uuid5(
            read.action.key,
            f"coverage-inspection:{read.dataset}:{read.row_index}:{read.field_page}:{read.binary}",
        )
        for read in reads.values()
    ]
    children = {
        child.action.key: child
        for child in RightsPortabilitySelectionRead.objects.select_related("action").filter(
            action__key__in=child_keys
        )
    }
    # Loop invariants over one locked row each: computed once, not once per page.
    coverage_ciphertext = fingerprint(row.encrypted_coverage)
    selection_body = fingerprint(selection.encrypted_selection)
    for read_id, page in zip(ids, required, strict=True):
        read = reads[read_id]
        dataset, row_index, field_page, binary = page
        if (
            read.coverage_id != row.pk
            or read.proof_id != proof.pk
            or read.source_digest != row.source_digest
            or read.coverage_digest != row.coverage_digest
            or read.original_session_version != actor.session_version
            or read.original_mfa_version != actor.mfa_version
            or (read.dataset, read.row_index, read.field_page, read.binary) != page
        ):
            raise ValidationError("Original coverage page record changed")
        purpose = checked_reason(read.action)
        signature = fingerprint(
            canonical(
                {
                    "case": str(case.pk),
                    "version": case.version,
                    "actor": actor.pk,
                    "session": actor.session_version,
                    "mfa": actor.mfa_version,
                    "coverage": row.pk,
                    "coverage_digest": row.coverage_digest,
                    "ciphertext": coverage_ciphertext,
                    "proof": str(proof.pk),
                    "selection": selection.pk,
                    "source": row.source_digest,
                    "dataset": dataset,
                    "row": row_index,
                    "page": field_page,
                    "binary": binary,
                    "purpose": purpose,
                }
            )
        )
        checked_action(read.action, case, actor.pk, "coverage_inspect", signature)
        child_key = uuid5(
            read.action.key, f"coverage-inspection:{dataset}:{row_index}:{field_page}:{binary}"
        )
        child = children.get(child_key)
        if child is None or child.action.actor_id != actor.pk:
            raise ValidationError("Original selection inspection required")
        if (
            child.original_session_version != actor.session_version
            or child.original_mfa_version != actor.mfa_version
        ):
            raise ValidationError("Original selection reader epochs changed")
        # Decrypt once; keep the original order: evidence validation, then the strict reason check.
        try:
            child_body = unseal(child.action.encrypted_reason)
            child_reason = child_body["reason"]
        except (InvalidToken, ValueError, TypeError, KeyError) as error:
            raise ValidationError("Selection review evidence unavailable") from error
        validate_evidence(child, selection, case, proof, _body_digest=selection_body,
                          _reason=child_reason)
        if checked_reason_body(child_body) != purpose:
            raise ValidationError("Original selection inspection purpose changed")
        result = coverage_page(
            source, assessment, facts, body, summary, dataset, row_index, field_page, binary=binary
        )
        if read.page_digest != fingerprint(canonical(result)):
            raise ValidationError("Original coverage page digest changed")
    authorize(user, case)
    return compiled


@sensitive_variables()
def validate_approved_coverage(decision, case, proof, source):
    """Use original case version and audited locked source; never authorize a new closure."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Coverage evidence requires enclosing transaction")
    row = decision.coverage
    actor = User.objects.get(pk=decision.action.actor_id)
    if (
        case.kind != "portability"
        or decision.outcome != "approved"
        or row.request_id != case.pk
        or decision.proof_id != proof.pk
        or row.proof_id != proof.pk
        or decision.source_digest != row.source_digest
        or decision.coverage_digest != row.coverage_digest
        or fingerprint(canonical(source)) != row.source_digest
        or actor.pk == row.actor_id
        or actor.session_version != decision.original_session_version
        or actor.mfa_version != decision.original_mfa_version
    ):
        raise ValidationError("Coverage approval evidence changed")
    authorize(actor, case)
    latest = (
        RightsPortabilityCoverage.objects.filter(request=case)
        .order_by("-created_at", "-pk")
        .first()
    )
    if latest is None or latest.pk != row.pk:
        raise ValidationError("Latest coverage required")
    compiled = validate_coverage_pages(row, case, proof, source, actor, decision.read_ids)
    ids = decision.read_ids
    reason = checked_reason(decision.action)
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "actor": actor.pk,
                "coverage": row.pk,
                "coverage_digest": row.coverage_digest,
                "ciphertext": fingerprint(row.encrypted_coverage),
                "source": row.source_digest,
                "proof": str(proof.pk),
                "session": decision.original_session_version,
                "mfa": decision.original_mfa_version,
                "reads": ids,
                "reason": reason,
                "outcome": "approved",
            }
        )
    )
    checked_action(decision.action, case, actor.pk, "coverage_review", signature)
    authorize(actor, case)
    return compiled
