"""Independent full coverage decision; never final rights response or closure."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityCoverage, RightsPortabilityCoverageReview
from .rights import fingerprint
from .rights_exports import canonical, reviewer_case, source_copy
from .rights_portability_coverage import compile_coverage
from .rights_portability_coverage_pages import baseline_body
from .rights_portability_coverage_read_gate import require_complete_reads
from .rights_portability_review import authorize
from .rights_verification import authorized_proof


@transaction.atomic
@sensitive_variables()
def record(user, case_id, version, coverage_id, key, reason, outcome):
    if (
        outcome not in {"approved", "rejected"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 200
    ):
        raise ValidationError("Invalid coverage decision")
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    if case.kind != "portability" or case.status != "reviewing" or case.version != version:
        raise ValidationError("Current portability request required")
    row = (
        RightsPortabilityCoverage.objects.select_for_update(of=("self",))
        .select_related(
            "action",
            "selection_review__selection",
            "selection_review__read__action",
            "selection_review__action",
        )
        .filter(pk=coverage_id, request=case)
        .first()
    )
    if row is None or row.actor_id == actor.pk:
        raise PermissionDenied("Independent coverage reviewer required")
    latest = (
        RightsPortabilityCoverage.objects.filter(request=case)
        .order_by("-created_at", "-pk")
        .first()
    )
    if latest.pk != row.pk:
        raise ValidationError("Latest coverage required")
    proof = authorized_proof(case, person, case.kind)
    source = source_copy(person, listing, case)
    previous = RightsAction.objects.filter(key=key).first()
    original = (
        RightsPortabilityCoverageReview.objects.filter(action=previous).first()
        if previous
        else None
    )
    if previous and original is None:
        raise ValidationError("Conflicting coverage decision key")
    reads = require_complete_reads(
        user, case, row, source, ids=original.read_ids if original else None
    )
    # Exact audited reads have validated original coverage and current selection authority.
    body = baseline_body(
        row,
        case,
        User.objects.get(pk=row.actor_id),
        row.selection_review.selection,
        row.selection_review,
    )
    selection = unseal(row.selection_review.selection.encrypted_selection)
    assessment = unseal(
        row.selection_review.selection.assessment_review.assessment.encrypted_assessment
    )
    compile_coverage(
        source,
        assessment,
        selection["selection"],
        body["omissions"],
        selection.get("images", []),
        body["image_omissions"],
        field_evidence=selection.get("field_evidence"),
        allow_partial=outcome == "rejected",
    )
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "actor": actor.pk,
                "coverage": row.pk,
                "coverage_digest": row.coverage_digest,
                "ciphertext": fingerprint(row.encrypted_coverage),
                "source": row.source_digest,
                "proof": str(proof.pk),
                "session": user.session_version,
                "mfa": user.mfa_version,
                "reads": reads,
                "reason": reason,
                "outcome": outcome,
            }
        )
    )
    if previous is None:
        try:
            with transaction.atomic():
                previous = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    operation="coverage_review",
                    expected_version=version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage decision key") from error
    if (
        previous.request_id,
        previous.actor_id,
        previous.operation,
        previous.expected_version,
        previous.payload_digest,
    ) != (case.pk, actor.pk, "coverage_review", version, signature):
        raise ValidationError("Conflicting coverage decision key")
    try:
        if unseal(previous.encrypted_reason) != {"reason": reason}:
            raise ValidationError("Coverage decision reason changed")
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Coverage decision reason unavailable") from error
    expected = {
        "coverage_id": row.pk,
        "proof_id": proof.pk,
        "source_digest": row.source_digest,
        "coverage_digest": row.coverage_digest,
        "original_session_version": user.session_version,
        "original_mfa_version": user.mfa_version,
        "read_ids": reads,
        "outcome": outcome,
    }
    if original:
        if any(getattr(original, name) != value for name, value in expected.items()):
            raise ValidationError("Coverage decision record changed")
        result = original
    else:
        try:
            with transaction.atomic():
                result = RightsPortabilityCoverageReview.objects.create(action=previous, **expected)
        except IntegrityError as error:
            raise ValidationError("Coverage already reviewed") from error
    authorize(user, case)
    if (
        authorized_proof(case, person, case.kind).pk != proof.pk
        or fingerprint(canonical(source_copy(person, listing, case))) != row.source_digest
    ):
        raise ValidationError("Coverage decision authority or source changed")
    return result
