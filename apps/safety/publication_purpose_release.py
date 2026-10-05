"""Audited inspection prerequisite for independently releasing a publication purpose."""

from types import SimpleNamespace
from uuid import uuid4

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .models import PrivacyHoldReleaseProposal, PrivacyPublicationHold, RightsAction, RightsMessage
from .privacy_release import current, source
from .processing_review import authorize
from .purpose_release import original_plan
from .rights import fingerprint
from .rights_responses import issue
from .rights_scope import locked_profile_case


@sensitive_variables()
def decision(hold):
    execution = hold.purpose_execution
    if (
        execution.review.outcome != "approved"
        or execution.review.action.actor_id == execution.review.plan.action.actor_id
        or execution.review.source_digest != execution.review.plan.source_digest
    ):
        raise ValidationError("Original independent approval unavailable")
    review = execution.review
    try:
        review_reason = unseal(review.action.encrypted_reason)["reason"]
        expected_review = fingerprint(
            canonical(
                {
                    "plan": str(review.plan_id),
                    "version": review.action.expected_version,
                    "operation": "review",
                    "reason": review_reason,
                    "outcome": "approved",
                    "plan_digest": fingerprint(review.plan.encrypted_plan),
                }
            )
        )
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError("Original approval record unavailable") from error
    if (
        review.action.payload_digest != expected_review
        or review.action.operation != "processing_review"
        or review.action.request_id != execution.action.request_id
    ):
        raise ValidationError("Original approval record changed")
    body = original_plan(
        SimpleNamespace(
            execution=execution,
            purpose="publication",
            mode=hold.ground.removeprefix("purpose_"),
        )
    )
    if execution.person_id != hold.person_id or execution.account_subject_id:
        raise ValidationError("Publication execution scope changed")
    return next(row for row in body["decisions"] if row["purpose"] == "publication")


def permission(user, case, hold):
    fresh = authorize(user, case, review_permission=False)
    if (
        not fresh.has_perm("safety.release_purpose_restriction")
        or not fresh.has_perm("safety.respond_rights_request")
        or fresh.pk == hold.action.actor_id
    ):
        raise PermissionDenied("Independent purpose release permission required")
    return fresh


def digest(case, person, listing, hold):
    return fingerprint(
        canonical(
            {
                "hold_source": source(case, person, listing, hold),
                "execution": hold.purpose_execution.pk,
                "plan": fingerprint(hold.purpose_execution.review.plan.encrypted_plan),
                "review": hold.purpose_execution.review.plan_digest,
                "outcome": hold.purpose_execution.review.outcome,
            }
        )
    )


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, hold_id, key, version, reason):
    case, person, listing = locked_profile_case(
        case_id,
        lock_listing=True,
        allow_version_change=True,
    )
    hold = (
        PrivacyPublicationHold.objects.select_for_update(of=("self",))
        .select_related("action", "purpose_execution__review__plan__action")
        .filter(pk=hold_id, action__request=case, person=person)
        .first()
    )
    if not hold or not hasattr(hold, "purpose_execution"):
        raise PermissionDenied
    fresh = permission(user, case, hold)
    proof = current(fresh, case, person, hold, version)
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Inspection reason required")
    snapshot = digest(case, person, listing, hold)
    signature = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "version": version,
                "reason": reason,
                "source": snapshot,
                "proof": str(proof.pk),
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != fresh.pk
            or previous.operation != "publication_rel_read"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting replay")
        return previous, decision(hold)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="publication_rel_read",
                payload_digest=signature,
                encrypted_reason=seal(
                    {"reason": reason, "source": snapshot, "hold": hold.pk, "proof": str(proof.pk)}
                ),
            )
            selected = decision(hold)
            permission(user, case, hold)
            return action, selected
    except IntegrityError as error:
        raise ValidationError("Conflicting inspection") from error


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, hold_id, key, version, read_id, reason, ground, resume_message_id=None):
    case, person, listing = locked_profile_case(
        case_id,
        lock_listing=True,
        allow_version_change=True,
    )
    hold = (
        PrivacyPublicationHold.objects.select_for_update(of=("self",))
        .select_related("action", "purpose_execution__review__plan__action")
        .filter(pk=hold_id, action__request=case, person=person)
        .first()
    )
    if not hold or not hasattr(hold, "purpose_execution"):
        raise PermissionDenied
    fresh = permission(user, case, hold)
    signature = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "version": version,
                "read": read_id,
                "reason": reason,
                "ground": ground,
                "resume_message": resume_message_id,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "publication_rel_plan"
            and previous.payload_digest == signature
        ):
            return PrivacyHoldReleaseProposal.objects.get(action=previous)
        raise ValidationError("Conflicting replay")
    proof = current(fresh, case, person, hold, version)
    reading = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=fresh,
        expected_version=version,
        operation="publication_rel_read",
    ).first()
    if not reading or not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Current audited purpose inspection required")
    try:
        body = unseal(reading.encrypted_reason)
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError("Purpose inspection record unavailable") from error
    snapshot = digest(case, person, listing, hold)
    expected_read = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "version": reading.expected_version,
                "reason": body.get("reason"),
                "source": body.get("source"),
                "proof": body.get("proof"),
            }
        )
    )
    if (
        reading.payload_digest != expected_read
        or body.get("source") != snapshot
        or body.get("hold") != hold.pk
        or body.get("proof") != str(proof.pk)
    ):
        raise ValidationError("Purpose inspection changed")
    selected = decision(hold)
    message = None
    if selected["operation"] == "restrict":
        if ground != "restriction_resolved" or resume_message_id:
            raise ValidationError("Reviewed restriction grounds required")
    else:
        message = RightsMessage.objects.filter(
            pk=resume_message_id,
            request=case,
            created_at__gt=hold.created_at,
        ).first()
        if (
            ground != "resume_requested"
            or not message
            or message.actor_id not in {None, person.subject_id}
        ):
            raise ValidationError("Reviewed new subject request required")
    text = (
        "Se propone levantar la medida por finalidad sobre publicación tras revisión independiente. "
        "Sigue activa hasta recepción y nueva comprobación; no se republicará automáticamente. "
        "Simulación de desarrollo; identidad no comprobada. / "
        "Release of the publication purpose measure is proposed after independent review. "
        "It remains active pending receipt and a fresh check; publication will not resume automatically. "
        "Development simulation; identity not verified."
    )
    try:
        with transaction.atomic():
            response = issue(
                fresh,
                case.pk,
                uuid4(),
                case.version,
                case.response_version,
                "progress",
                reason,
                text,
                True,
            )
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="publication_rel_plan",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            proposal = PrivacyHoldReleaseProposal.objects.create(
                hold=hold,
                action=action,
                proof=proof,
                response=response,
                source_digest=snapshot,
                purpose_read=reading,
                ground=ground,
                resume_message=message,
            )
            case.refresh_from_db()
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status"])
            permission(user, case, hold)
            return proposal
    except IntegrityError as error:
        raise ValidationError("Conflicting proposal") from error


@transaction.atomic
@sensitive_variables()
def execute(user, case_id, hold_id, proposal_id, key, version, reason):
    from django.utils import timezone

    case, person, listing = locked_profile_case(
        case_id,
        lock_listing=True,
        allow_version_change=True,
    )
    hold = (
        PrivacyPublicationHold.objects.select_for_update(of=("self",))
        .select_related("action", "purpose_execution__review__plan__action")
        .filter(pk=hold_id, action__request=case, person=person)
        .first()
    )
    if not hold or not hasattr(hold, "purpose_execution"):
        raise PermissionDenied
    fresh = permission(user, case, hold)
    proposal = (
        PrivacyHoldReleaseProposal.objects.select_for_update(of=("self",))
        .select_related("action", "proof", "response")
        .filter(pk=proposal_id, hold=hold, purpose_read__isnull=False)
        .first()
    )
    if not proposal:
        raise ValidationError("Purpose proposal unavailable")
    signature = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "proposal": proposal.pk,
                "version": version,
                "reason": reason,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "publication_rel_exec"
            and previous.payload_digest == signature
        ):
            return PrivacyHoldReleaseProposal.objects.get(released_action=previous)
        raise ValidationError("Conflicting replay")
    try:
        original_reason = unseal(proposal.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError("Proposal record unavailable") from error
    expected = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "version": proposal.action.expected_version,
                "read": proposal.purpose_read_id,
                "reason": original_reason,
                "ground": proposal.ground,
                "resume_message": proposal.resume_message_id,
            }
        )
    )
    proof = current(user, case, person, hold, version)
    proposal.proof.refresh_from_db(fields=["status"])
    ack = getattr(proposal.response, "receipt_acknowledgement", None)
    latest = hold.release_proposals.order_by("-pk").first()
    if (
        expected != proposal.action.payload_digest
        or proposal.released_at
        or proposal.action.actor_id != fresh.pk
        or not latest
        or latest.pk != proposal.pk
        or proposal.source_digest != digest(case, person, listing, hold)
        or proposal.proof.status != "passed"
        or case.response_version != proposal.response.response_version
        or not ack
        or ack.channel_digest != case.receipt_digest
        or proof.pk == proposal.proof_id
        or proof.created_at <= proposal.created_at
        or proof.created_at <= ack.created_at
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Current proposal, prior receipt and later scoped check required")
    selected = decision(hold)
    if selected["operation"] == "cease":
        message = proposal.resume_message
        if (
            proposal.ground != "resume_requested"
            or not message
            or message.request_id != case.pk
            or message.created_at <= hold.created_at
            or message.actor_id not in {None, person.subject_id}
        ):
            raise ValidationError("Reviewed new subject request required")
    elif proposal.ground != "restriction_resolved" or proposal.resume_message_id:
        raise ValidationError("Reviewed restriction grounds required")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="publication_rel_exec",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            hold.active = False
            hold.save(update_fields=["active"])
            proposal.released_action = action
            proposal.released_proof = proof
            proposal.released_at = timezone.now()
            proposal.save(update_fields=["released_action", "released_proof", "released_at"])
            if listing:
                if listing.status == "published":
                    listing.status = "paused"
                listing.available_until = None
                listing.lifecycle_version += 1
                listing.save(update_fields=["status", "available_until", "lifecycle_version"])
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status"])
            permission(user, case, hold)
            return proposal
    except IntegrityError as error:
        raise ValidationError("Conflicting release") from error
