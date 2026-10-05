"""Audited consumption of approved information; final export wiring follows separately."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsCopyInformation, RightsCopyInformationReview
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_information_review import validate_approved_evidence


@transaction.atomic
@sensitive_variables()
def consume_approved(user, case_id, version, review_id, key, reason):
    if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Information use reason required")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if case.version != version or case.kind != "access" or case.status != "reviewing":
        raise ValidationError("Current access request required")
    proof = can_prepare(actor, case, person)
    review = (
        RightsCopyInformationReview.objects.select_for_update(of=("self",))
        .select_related("action", "read__action")
        .filter(pk=review_id, information__request=case)
        .first()
    )
    if review is None:
        raise ValidationError("Approved information unavailable")
    row = (
        RightsCopyInformation.objects.select_for_update(of=("self",))
        .select_related("action", "policy_document")
        .get(pk=review.information_id)
    )
    source_digest = fingerprint(canonical(source_copy(person, listing, case)))
    signature = fingerprint(
        canonical(
            {
                "review": review.pk,
                "version": version,
                "reason": reason,
                "source": source_digest,
                "information": fingerprint(row.encrypted_information),
                "policy": row.policy_digest,
                "inspection": review.read.action.payload_digest,
                "decision": review.action.payload_digest,
                "session": session_version,
                "mfa": mfa_version,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous and (
        previous.request_id != case.pk
        or previous.actor_id != actor.pk
        or previous.operation != "copy_info_use"
        or previous.payload_digest != signature
    ):
        raise ValidationError("Conflicting information use key")
    try:
        with transaction.atomic():
            previous or RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=version,
                operation="copy_info_use",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            try:
                body = unseal(row.encrypted_information)
            except (InvalidToken, ValueError, TypeError) as error:
                raise ValidationError("Approved information unavailable") from error
            body = validate_approved_evidence(review, row, case, proof, source_digest, body)
            fresh_authority(actor, case, session_version, mfa_version)
            if (
                can_prepare(User.objects.get(pk=actor.pk), case, person).pk != proof.pk
                or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
            ):
                raise ValidationError("Information source changed")
            return review, body
    except IntegrityError as error:
        raise ValidationError("Conflicting information use key") from error


@sensitive_variables()
def validate_export_binding(case, person, export):
    """Called after download auditing, while canonical request locks are held."""
    from copy import copy

    from apps.listings.models import Listing

    from .models import RightsExportInformationBinding

    binding = (
        RightsExportInformationBinding.objects.select_for_update().filter(export=export).first()
    )
    if binding is None:
        return
    review = (
        RightsCopyInformationReview.objects.select_for_update(of=("self",))
        .select_related("action", "read__action")
        .get(pk=binding.review_id)
    )
    row = (
        RightsCopyInformation.objects.select_for_update(of=("self",))
        .select_related("action", "policy_document")
        .get(pk=review.information_id)
    )
    if (
        export.action.request_id != case.pk
        or export.case_version != case.version
        or export.case_version != export.action.expected_version + 1
        or binding.information_digest != fingerprint(row.encrypted_information)
        or binding.policy_digest != row.policy_digest
        or binding.inspection_digest != review.read.action.payload_digest
        or binding.decision_digest != review.action.payload_digest
    ):
        raise ValidationError("Export information binding changed")
    listing = Listing.objects.select_for_update().filter(person=person).first() if person else None
    original = copy(case)
    original.version = export.action.expected_version
    source_digest = fingerprint(canonical(source_copy(person, listing, original)))
    if source_digest != binding.source_digest:
        raise ValidationError("Export information source changed")
    try:
        body = unseal(row.encrypted_information)
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Export information unavailable") from error
    validate_approved_evidence(review, row, original, export.proof, source_digest, body)
