"""Audited use of exact independently approved coverage; no delivery or closure."""

from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityCoverageReview
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_portability_coverage import compile_coverage
from .rights_portability_coverage_pages import baseline_body
from .rights_portability_coverage_review import record
from .rights_portability_selected_use import consume_selected


@transaction.atomic
@sensitive_variables()
def consume_approved_coverage(user, case_id, version, review_id, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Coverage use reason required")
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, user.session_version, user.mfa_version)
    if case.version != version or case.kind != "portability" or case.status != "reviewing":
        raise ValidationError("Current portability request required")
    decision = (
        RightsPortabilityCoverageReview.objects.select_for_update(of=("self",))
        .select_related(
            "action",
            "coverage__action",
            "coverage__selection_review__selection",
            "coverage__selection_review__action",
            "coverage__selection_review__read__action",
        )
        .filter(pk=review_id, coverage__request=case)
        .first()
    )
    if decision is None or decision.outcome != "approved":
        raise ValidationError("Approved coverage required")
    row = decision.coverage
    if row.actor_id != actor.pk or decision.action.actor_id == actor.pk:
        raise PermissionDenied("Own independently approved coverage required")
    reviewer = User.objects.get(pk=decision.action.actor_id)
    if (
        reviewer.session_version != decision.original_session_version
        or reviewer.mfa_version != decision.original_mfa_version
    ):
        raise PermissionDenied("Coverage reviewer authority changed")
    proof = can_prepare(actor, case, person)
    source = source_copy(person, listing, case)
    source_digest = fingerprint(canonical(source))
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "actor": actor.pk,
                "review": decision.pk,
                "coverage": row.pk,
                "decision": decision.action.payload_digest,
                "reads": decision.read_ids,
                "coverage_digest": row.coverage_digest,
                "ciphertext": fingerprint(row.encrypted_coverage),
                "source": source_digest,
                "proof": str(proof.pk),
                "session": user.session_version,
                "mfa": user.mfa_version,
                "reason": reason,
            }
        )
    )
    action = RightsAction.objects.filter(key=key).first()
    if action is None:
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    operation="coverage_use",
                    expected_version=version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage use key") from error
    if (
        action.request_id,
        action.actor_id,
        action.operation,
        action.expected_version,
        action.payload_digest,
    ) != (case.pk, actor.pk, "coverage_use", version, signature):
        raise ValidationError("Conflicting coverage use key")
    try:
        if unseal(action.encrypted_reason) != {"reason": reason}:
            raise ValidationError("Coverage use reason changed")
        review_reason = unseal(decision.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Coverage use reason unavailable") from error
    # The use intent exists before any coverage unsealing, including review replay.
    # Replay the original decision and exact original reads, never replace them.
    validated = record(
        reviewer, case.pk, version, row.pk, decision.action.key, review_reason, "approved"
    )
    if validated.pk != decision.pk:
        raise ValidationError("Coverage approval changed")
    selected, _ = consume_selected(
        user,
        case.pk,
        version,
        row.selection_review.selection_id,
        row.selection_review_id,
        uuid5(key, "coverage-approved-selection-use"),
        "Validate approved selection before consuming coverage",
    )
    body = baseline_body(row, case, actor, selected, row.selection_review)
    facts = unseal(selected.encrypted_selection)
    assessment = unseal(selected.assessment_review.assessment.encrypted_assessment)
    compiled = compile_coverage(
        source,
        assessment,
        facts["selection"],
        body["omissions"],
        facts.get("images", []),
        body["image_omissions"],
        field_evidence=facts.get("field_evidence"),
    )
    fresh_authority(actor, case, user.session_version, user.mfa_version)
    from .rights_portability_review import authorize

    authorize(reviewer, case)
    if (
        can_prepare(User.objects.get(pk=actor.pk), case, person).pk != proof.pk
        or row.proof_id != proof.pk
        or row.source_digest != source_digest
        or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
    ):
        raise ValidationError("Coverage use authority or source changed")
    return decision, compiled
