"""Encrypted declarations bound to current approved selection; never approve or close."""

from copy import deepcopy
from datetime import timedelta
from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityCoverage, RightsPortabilitySelectionReview
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_inspection_source import shared_source
from .rights_inspection_source import source_digest as shared_or_computed
from .rights_portability_coverage import compile_coverage
from .rights_portability_selected_use import consume_selected


@transaction.atomic
@sensitive_variables()
def save_coverage(
    user,
    case_id,
    case_version,
    review_id,
    key,
    version,
    reason,
    omissions,
    image_omissions,
    *,
    allow_partial=False,
    _inspection_source=None,
):
    if (
        type(allow_partial) is not bool
        or type(version) is not int
        or version < 0
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 200
    ):
        raise ValidationError("Invalid coverage version or reason")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    decision = (
        RightsPortabilitySelectionReview.objects.select_related(
            "selection", "action", "read__action"
        )
        .filter(pk=review_id, selection__request=case, selection__actor=actor)
        .first()
    )
    if decision is None:
        raise ValidationError("Own approved selection required")
    row, _ = consume_selected(
        actor,
        case.pk,
        case_version,
        decision.selection_id,
        decision.pk,
        uuid5(key, "coverage-selection-use"),
        "Validate approved selection before recording coverage",
        _inspection_source=_inspection_source,
    )
    facts = unseal(row.encrypted_selection)
    assessment = unseal(row.assessment_review.assessment.encrypted_assessment)

    def current_source():
        # Only the caller's active context may defer the fresh DB comparison to its exit.
        return (shared_source(_inspection_source, person, listing, case)
                if _inspection_source is not None else source_copy(person, listing, case))

    source = current_source()
    source_digest = shared_or_computed(_inspection_source, person, listing, case, source)
    if source_digest != row.source_digest:
        raise ValidationError("Coverage source changed")
    body = {
        "schema": "portability-coverage-draft-v1",
        "version": version,
        "selection": row.pk,
        "review": decision.pk,
        "source": source_digest,
        "selection_digest": row.selection_digest,
        "selection_ciphertext": fingerprint(row.encrypted_selection),
        "inspection": decision.read.action.payload_digest,
        "decision": decision.action.payload_digest,
        "session": session_version,
        "mfa": mfa_version,
        "omissions": deepcopy(omissions),
        "image_omissions": deepcopy(image_omissions),
    }
    if allow_partial:
        body["allow_partial"] = True
    digest = fingerprint(canonical(body))
    signature = fingerprint(
        canonical(
            {
                "case_version": case_version,
                "proof": str(row.proof_id),
                "body": digest,
                "reason": reason,
            }
        )
    )
    action = RightsAction.objects.filter(key=key).first()
    if action is not None:
        if (
            action.request_id,
            action.actor_id,
            action.operation,
            action.expected_version,
            action.payload_digest,
        ) != (case.pk, actor.pk, "coverage_save", case_version, signature):
            raise ValidationError("Conflicting coverage key")
    else:
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    operation="coverage_save",
                    expected_version=case_version,
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage key") from error
    try:
        recorded_reason = unseal(action.encrypted_reason)
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Coverage reason unavailable") from error
    if recorded_reason != {"reason": reason}:
        raise ValidationError("Coverage reason changed")
    # Both selection-use and coverage intent are audited before compiling/decrypting coverage.
    compile_coverage(
        source,
        assessment,
        facts["selection"],
        omissions,
        facts.get("images", []),
        image_omissions,
        field_evidence=facts.get("field_evidence"),
        allow_partial=allow_partial,
    )
    previous = RightsPortabilityCoverage.objects.select_for_update().filter(action=action).first()
    if previous:
        if previous.purged_at or previous.expires_at <= timezone.now():
            raise ValidationError("Coverage expired")
        try:
            stored = unseal(previous.encrypted_coverage)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Coverage unavailable") from error
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or canonical(stored) != canonical(body)
            or previous.coverage_digest != digest
            or previous.version != version + 1
            or previous.selection_review_id != decision.pk
            or previous.proof_id != row.proof_id
            or previous.source_digest != source_digest
            or previous.selection_digest != row.selection_digest
            or previous.original_session_version != session_version
            or previous.original_mfa_version != mfa_version
        ):
            raise ValidationError("Conflicting stored coverage")
        result = previous
    else:
        latest = (
            RightsPortabilityCoverage.objects.filter(request=case, actor=actor)
            .order_by("-version")
            .first()
        )
        if version != (latest.version if latest else 0):
            raise ValidationError("Coverage version changed")
        try:
            with transaction.atomic():
                result = RightsPortabilityCoverage.objects.create(
                    request=case,
                    actor=actor,
                    action=action,
                    selection_review=decision,
                    proof=row.proof,
                    source_digest=source_digest,
                    selection_digest=row.selection_digest,
                    coverage_digest=digest,
                    original_session_version=session_version,
                    original_mfa_version=mfa_version,
                    version=version + 1,
                    encrypted_coverage=seal(body),
                    expires_at=min(
                        row.expires_at, row.proof.expires_at, timezone.now() + timedelta(hours=24)
                    ),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting coverage version") from error
    fresh_authority(actor, case, session_version, mfa_version)
    if (
        can_prepare(User.objects.get(pk=actor.pk), case, person).pk != row.proof_id
        or shared_or_computed(_inspection_source, person, listing, case) != source_digest
    ):
        raise ValidationError("Coverage authority or source changed")
    return result
