"""Store explicit portable selectors; independent selection approval remains separate."""

from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilitySelection, RightsPortabilitySelectionReview
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_inspection_source import shared_source
from .rights_inspection_source import source_digest as shared_or_computed
from .rights_portability_selection import project_selected
from .rights_portability_use import consume_approved


@transaction.atomic
@sensitive_variables()
def save_selection(
    user,
    case_id,
    case_version,
    review_id,
    key,
    version,
    reason,
    selection,
    *,
    field_evidence=None,
    images=None,
    _inspection_source=None,
):
    if (
        type(version) is not int
        or version < 0
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Invalid portability selection version or reason")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    selection_facts = {"version": version, "selection": selection}
    if field_evidence is not None:
        selection_facts["field_evidence"] = field_evidence
    if images is not None:
        selection_facts["images"] = images
    # The same globally unique action records assessment use before decryption.
    review, assessment = consume_approved(
        actor,
        case_id,
        case_version,
        review_id,
        key,
        reason,
        selection_binding=fingerprint(canonical(selection_facts)),
        _inspection_source=_inspection_source,
    )
    action = RightsAction.objects.get(key=key)
    def current_source():
        return (shared_source(_inspection_source, person, listing, case)
                if _inspection_source is not None else source_copy(person, listing, case))

    source = current_source()
    source_digest = shared_or_computed(_inspection_source, person, listing, case, source)
    project_selected(source, assessment, selection, field_evidence=field_evidence)
    if images is not None:
        from .rights_portability_images import audited_images

        images = audited_images(actor, case, person, source, assessment, images)
    if source_digest != review.source_digest:
        raise ValidationError("Portability selection source changed")
    binding = {
        "schema": "portability-selection-draft-v1",
        "selection": selection,
        "version": version,
        "assessment_review": review.pk,
        "source": source_digest,
        "assessment": fingerprint(review.assessment.encrypted_assessment),
        "inspection": review.read.action.payload_digest,
        "decision": review.action.payload_digest,
        "session": session_version,
        "mfa": mfa_version,
    }
    if field_evidence is not None:
        binding["field_evidence"] = field_evidence
    if images is not None:
        binding["images"] = images
    previous = RightsPortabilitySelection.objects.select_for_update().filter(action=action).first()
    if previous:
        if previous.purged_at or previous.expires_at <= timezone.now():
            raise ValidationError("Portability selection expired")
        try:
            stored = unseal(previous.encrypted_selection)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Portability selection unavailable") from error
        if (
            canonical(stored) != canonical(binding)
            or previous.selection_digest != fingerprint(canonical(binding))
            or previous.version != version + 1
            or previous.assessment_review_id != review.pk
            or previous.proof_id != review.proof_id
            or previous.source_digest != source_digest
            or previous.assessment_digest != binding["assessment"]
            or previous.inspection_digest != binding["inspection"]
            or previous.decision_digest != binding["decision"]
            or previous.original_session_version != session_version
            or previous.original_mfa_version != mfa_version
        ):
            raise ValidationError("Conflicting portability selection key")
        row = previous
    else:
        latest = (
            RightsPortabilitySelection.objects.filter(request=case, actor=actor)
            .order_by("-version")
            .first()
        )
        if version != (latest.version if latest else 0):
            raise ValidationError("Portability selection version changed")
        try:
            with transaction.atomic():
                row = RightsPortabilitySelection.objects.create(
                    request=case,
                    actor=actor,
                    action=action,
                    assessment_review=review,
                    proof=review.proof,
                    source_digest=source_digest,
                    assessment_digest=binding["assessment"],
                    inspection_digest=binding["inspection"],
                    decision_digest=binding["decision"],
                    original_session_version=session_version,
                    original_mfa_version=mfa_version,
                    version=version + 1,
                    selection_digest=fingerprint(canonical(binding)),
                    encrypted_selection=seal(binding),
                    expires_at=min(
                        review.assessment.expires_at,
                        review.proof.expires_at,
                        timezone.now() + timedelta(hours=24),
                    ),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting portability selection") from error
    fresh_authority(actor, case, session_version, mfa_version)
    if (
        can_prepare(User.objects.get(pk=actor.pk), case, person).pk != review.proof_id
        or shared_or_computed(_inspection_source, person, listing, case) != source_digest
    ):
        raise ValidationError("Portability selection authority or source changed")
    return row


@transaction.atomic
@sensitive_variables()
def inspect_selection(
    user, case_id, case_version, selection_id, key, purpose, *, approved_review_id=None,
    _inspection_source=None,
):
    if not isinstance(purpose, str) or not 20 <= len(purpose.strip()) <= 200:
        raise ValidationError("Portability selection inspection purpose required")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    row = (
        RightsPortabilitySelection.objects.select_for_update(of=("self",))
        .select_related(
            "action",
            "assessment_review__assessment",
            "assessment_review__read__action",
            "assessment_review__action",
        )
        .filter(pk=selection_id, request=case, actor=actor)
        .first()
    )
    if not row or row.purged_at or row.expires_at <= timezone.now() or not row.encrypted_selection:
        raise ValidationError("Portability selection unavailable")
    selection_decision = None
    if approved_review_id is not None:
        selection_decision = (
            RightsPortabilitySelectionReview.objects.select_for_update(of=("self",))
            .select_related("action")
            .filter(pk=approved_review_id, selection=row)
            .first()
        )
        if selection_decision is None:
            raise ValidationError("Approved portability selection required")
    review, assessment = consume_approved(
        actor,
        case_id,
        case_version,
        row.assessment_review_id,
        key,
        purpose,
        selection_binding=fingerprint(
            canonical(
                {
                    "selection_id": row.pk,
                    "digest": row.selection_digest,
                    "ciphertext": fingerprint(row.encrypted_selection),
                    "approval": selection_decision.pk if selection_decision else None,
                    "decision": selection_decision.action.payload_digest
                    if selection_decision
                    else None,
                }
            )
        ),
        audit_operation="selection_use" if selection_decision else "selection_read",
        _inspection_source=_inspection_source,
    )
    if selection_decision is not None:
        from .rights_portability_selection_review import validate_approved_selection

        validate_approved_selection(selection_decision, row, case, row.proof)
    expected = validate_selection_evidence(row, review, case)

    def current_source():
        # Only the caller's active context may defer the fresh DB comparison to its exit.
        return (shared_source(_inspection_source, person, listing, case)
                if _inspection_source is not None else source_copy(person, listing, case))

    source = current_source()
    if expected.get("images"):
        from .rights_portability_images import audited_images

        audited_images(row.actor, case, person, source, assessment, expected["images"])
    projected = project_selected(
        source, assessment, expected["selection"], field_evidence=expected.get("field_evidence")
    )
    fresh_authority(actor, case, session_version, mfa_version)
    if (
        can_prepare(User.objects.get(pk=actor.pk), case, person).pk != row.proof_id
        or shared_or_computed(_inspection_source, person, listing, case) != row.source_digest
    ):
        raise ValidationError("Portability selection source changed")
    return row, projected


@sensitive_variables()
def validate_selection_evidence(row, review, case):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Selection evidence requires enclosing transaction")
    case_version = case.version
    if (
        row.request_id != case.pk
        or row.assessment_review_id != review.pk
        or row.purged_at
        or row.expires_at <= timezone.now()
        or not row.encrypted_selection
    ):
        raise ValidationError("Portability selection unavailable")
    try:
        body = unseal(row.encrypted_selection)
        reason = unseal(row.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Portability selection unavailable") from error
    if not isinstance(body, dict):
        raise ValidationError("Portability selection unavailable")
    expected = {
        "schema": "portability-selection-draft-v1",
        "selection": body.get("selection"),
        "version": row.version - 1,
        "assessment_review": review.pk,
        "source": row.source_digest,
        "assessment": row.assessment_digest,
        "inspection": row.inspection_digest,
        "decision": row.decision_digest,
        "session": row.original_session_version,
        "mfa": row.original_mfa_version,
    }
    selection_facts = {"version": row.version - 1, "selection": expected["selection"]}
    if "field_evidence" in body:
        expected["field_evidence"] = body["field_evidence"]
        selection_facts["field_evidence"] = body["field_evidence"]
    if "images" in body:
        expected["images"] = body["images"]
        selection_facts["images"] = body["images"]
    signature = fingerprint(
        canonical(
            {
                "review": review.pk,
                "selection": fingerprint(canonical(selection_facts)),
                "version": case_version,
                "reason": reason,
                "source": row.source_digest,
                "proof": str(row.proof_id),
                "assessment": row.assessment_digest,
                "inspection": row.inspection_digest,
                "decision": row.decision_digest,
                "session": row.original_session_version,
                "mfa": row.original_mfa_version,
            }
        )
    )
    canonical_body = canonical(body)
    canonical_expected = canonical(expected)
    if (
        canonical_body != canonical_expected
        or row.selection_digest != fingerprint(canonical_expected)
        or row.action.request_id != case.pk
        or row.action.actor_id != row.actor_id
        or row.action.operation != "selection_save"
        or row.action.expected_version != case_version
        or row.action.payload_digest != signature
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or row.source_digest != review.source_digest
        or row.proof_id != review.proof_id
        or row.assessment_digest != fingerprint(review.assessment.encrypted_assessment)
        or row.inspection_digest != review.read.action.payload_digest
        or row.decision_digest != review.action.payload_digest
    ):
        raise ValidationError("Portability selection evidence changed")
    return expected
