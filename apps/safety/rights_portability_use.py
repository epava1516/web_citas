"""Audited approved assessment use; selecting and delivering portable data is separate."""

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityAssessment, RightsPortabilityReview
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_portability_review import validate_approved_assessment


@transaction.atomic
@sensitive_variables()
def consume_approved(
    user, case_id, version, review_id, key, reason, *, selection_binding=None, audit_operation=None
):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Portability use reason required")
    operation = "selection_save" if selection_binding is not None else "portability_use"
    if audit_operation is not None:
        if (
            audit_operation
            not in {
                "selection_read",
                "selection_use",
                "selection_catalog",
                "selection_reset",
                "image_catalog",
            }
            or selection_binding is None
        ):
            raise ValidationError("Invalid portability audit operation")
        operation = audit_operation
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if case.version != version or case.kind != "portability" or case.status != "reviewing":
        raise ValidationError("Current portability request required")
    proof = can_prepare(actor, case, person)
    review = (
        RightsPortabilityReview.objects.select_for_update(of=("self",))
        .select_related("action", "read__action")
        .filter(pk=review_id, assessment__request=case)
        .first()
    )
    if review is None:
        raise ValidationError("Approved portability assessment unavailable")
    row = (
        RightsPortabilityAssessment.objects.select_for_update(of=("self",))
        .select_related("action")
        .get(pk=review.assessment_id)
    )
    source_digest = fingerprint(canonical(source_copy(person, listing, case)))
    signature = fingerprint(
        canonical(
            {
                "review": review.pk,
                "selection": selection_binding,
                "version": version,
                "reason": reason,
                "source": source_digest,
                "proof": str(proof.pk),
                "assessment": fingerprint(row.encrypted_assessment),
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
        or previous.operation != operation
        or previous.payload_digest != signature
    ):
        raise ValidationError("Conflicting portability use key")
    try:
        with transaction.atomic():
            previous or RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=version,
                operation=operation,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            try:
                body = unseal(row.encrypted_assessment)
            except (InvalidToken, ValueError, TypeError) as error:
                raise ValidationError("Approved portability assessment unavailable") from error
            body = validate_approved_assessment(review, row, case, proof, source_digest, body)
            fresh_authority(actor, case, session_version, mfa_version)
            if (
                can_prepare(User.objects.get(pk=actor.pk), case, person).pk != proof.pk
                or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
            ):
                raise ValidationError("Portability source changed")
            return review, body
    except IntegrityError as error:
        raise ValidationError("Conflicting portability use key") from error
