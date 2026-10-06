"""Versioned coverage binding for private portability exports; no final closure."""

from uuid import uuid5

from django.core.exceptions import ValidationError

from .rights import fingerprint
from .rights_exports import canonical
from .rights_portability_coverage_evidence import (
    checked_action,
    checked_reason,
    validate_approved_coverage,
)


def coverage_summary(compiled):
    return {key: value for key, value in compiled.items() if key not in {"projection", "schema"}}


def validate_binding(binding, case, proof, source):
    if binding.coverage_review_id is None:
        if binding.coverage_use_id or any(
            (
                binding.coverage_digest,
                binding.coverage_ciphertext_digest,
                binding.coverage_decision_digest,
                binding.coverage_reads_digest,
            )
        ):
            raise ValidationError("Unexpected coverage export binding")
        return None
    decision = binding.coverage_review
    row = decision.coverage
    action = binding.coverage_use
    if (
        action is None
        or row.selection_review_id != binding.review_id
        or binding.coverage_digest != row.coverage_digest
        or binding.coverage_ciphertext_digest != fingerprint(row.encrypted_coverage)
        or binding.coverage_decision_digest != decision.action.payload_digest
        or binding.coverage_reads_digest != fingerprint(canonical(decision.read_ids))
        or action.key != uuid5(binding.export.action.key, "approved-portability-coverage-use")
        or row.actor_id != binding.export.action.actor_id
        or binding.export.expires_at > row.expires_at
    ):
        raise ValidationError("Covered export binding changed")
    reason = checked_reason(action)
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "actor": row.actor_id,
                "review": decision.pk,
                "coverage": row.pk,
                "decision": decision.action.payload_digest,
                "reads": decision.read_ids,
                "coverage_digest": row.coverage_digest,
                "ciphertext": fingerprint(row.encrypted_coverage),
                "source": binding.source_digest,
                "proof": str(proof.pk),
                "session": binding.original_session_version,
                "mfa": binding.original_mfa_version,
                "reason": reason,
            }
        )
    )
    checked_action(action, case, row.actor_id, "coverage_use", signature)
    return validate_approved_coverage(decision, case, proof, source)
