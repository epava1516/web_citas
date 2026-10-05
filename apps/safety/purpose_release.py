"""Independent notified release of one purpose block; no automatic expiry."""

import uuid

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User
from apps.listings.models import Favorite

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .models import (
    PurposeReleaseProposal,
    PurposeRestriction,
    PurposeRestrictionRead,
    RightsAction,
    RightsMessage,
)
from .processing_review import authorize
from .rights import fingerprint
from .rights_responses import complete_response_read, issue
from .rights_scope import locked_case
from .rights_verification import authorized_proof, complete_read


def source(case, restriction, subject):
    return fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "kind": case.kind,
                "payload": case.encrypted_payload,
                "channel": case.receipt_digest,
                "person": str(case.person_id or ""),
                "account": str(case.account_subject_id or ""),
                "manager": case.manager_version,
                "messages": list(
                    case.messages.order_by("pk").values(
                        "pk", "actor_id", "encrypted_payload", "created_at"
                    )
                ),
                "subject": list(
                    User.objects.filter(pk=subject.pk).values(
                        "pk",
                        "email",
                        "session_version",
                        "mfa_version",
                        "is_active",
                        "account_erased_at",
                    )
                ),
                "restriction": list(
                    PurposeRestriction.objects.filter(pk=restriction.pk).values(
                        "pk", "execution_id", "subject_id", "purpose", "mode", "active", "review_on"
                    )
                ),
                "other_active": list(
                    PurposeRestriction.objects.filter(
                        subject=subject, purpose=restriction.purpose, active=True
                    )
                    .order_by("pk")
                    .values_list("pk", flat=True)
                ),
                "favorites": list(
                    Favorite.objects.filter(user=subject)
                    .order_by("pk")
                    .values("pk", "listing_id", "created_at")
                ),
                "plan_digest": fingerprint(restriction.execution.review.plan.encrypted_plan),
            }
        )
    )


@sensitive_variables()
def original_plan(restriction):
    plan = restriction.execution.review.plan
    try:
        body = unseal(plan.encrypted_plan)
        reason = unseal(plan.action.encrypted_reason)["reason"]
        signatures = [
            fingerprint(
                canonical(
                    {
                        "version": plan.action.expected_version,
                        "reason": reason,
                        "decisions": body["decisions"],
                        "source_digest": digest,
                    }
                )
            )
            for digest in [None, plan.source_digest]
        ]
        selected = [row for row in body["decisions"] if row["purpose"] == restriction.purpose]
        if (
            len(selected) != 1
            or selected[0]["operation"] != restriction.mode
            or restriction.mode not in {"restrict", "cease"}
            or body["schema"] != "processing-purpose-plan-v1"
            or body["enforced"] is not False
            or body["partial"] is not True
            or fingerprint(canonical(body["manifest"])) != plan.source_digest
            or plan.action.payload_digest not in signatures
            or restriction.execution.review.plan_digest != fingerprint(plan.encrypted_plan)
        ):
            raise ValueError
        return body
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError("Original plan unavailable / Plan original no disponible") from error


def permission(user, case, restriction):
    fresh = authorize(user, case, review_permission=False)
    if (
        not fresh.has_perm("safety.release_purpose_restriction")
        or not fresh.has_perm("safety.respond_rights_request")
        or fresh.pk == restriction.execution.action.actor_id
    ):
        raise PermissionDenied("Independent purpose release permission required")
    return fresh


@sensitive_variables()
def locked(user, case_id, restriction_id):
    case, person, _ = locked_case(case_id, lock_listing=True, allow_version_change=True)
    restriction = (
        PurposeRestriction.objects.select_for_update(of=("self",))
        .select_related("execution__action", "execution__review__plan")
        .filter(pk=restriction_id, execution__action__request=case)
        .first()
    )
    if not restriction:
        raise PermissionDenied
    subject_id = case.account_subject_id or (person.subject_id if person else None)
    if (
        restriction.subject_id != subject_id
        or restriction.execution.person_id != case.person_id
        or restriction.execution.account_subject_id != case.account_subject_id
    ):
        raise PermissionDenied
    if restriction.purpose != "account_preferences":
        raise ValidationError(
            "Unsupported release purpose / Finalidad de levantamiento no implementada"
        )
    subject = User.objects.select_for_update(no_key=True).get(pk=subject_id)
    fresh = permission(user, case, restriction)
    return fresh, case, person, subject, restriction


def current(user, case, person, restriction, version):
    fresh = permission(user, case, restriction)
    if (
        case.kind not in {"restriction", "object"}
        or case.status != "reviewing"
        or case.version != version
        or case.assigned_to_id != fresh.pk
        or not restriction.active
        or not complete_read(fresh, case)
        or not complete_response_read(fresh, case)
    ):
        raise ValidationError(
            "Inspect current assigned active restriction / Consulta restricción activa asignada vigente"
        )
    return authorized_proof(case, person, case.kind)


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, restriction_id, key, version, reason):
    fresh, case, person, subject, restriction = locked(user, case_id, restriction_id)
    proof = current(user, case, person, restriction, version)
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Inspection reason required / Motivo de consulta obligatorio")
    digest = source(case, restriction, subject)
    signature = fingerprint(
        canonical(
            {"restriction": restriction.pk, "version": version, "reason": reason, "source": digest}
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "purpose_rel_inspect"
            and previous.payload_digest == signature
        ):
            return PurposeRestrictionRead.objects.get(action=previous), unseal(
                restriction.execution.review.plan.encrypted_plan
            )
        raise ValidationError("Conflicting replay / Reintento incompatible")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="purpose_rel_inspect",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            reading = PurposeRestrictionRead.objects.create(
                action=action, restriction=restriction, proof=proof, source_digest=digest
            )
            body = original_plan(restriction)
            permission(user, case, restriction)
            return reading, body
    except IntegrityError as error:
        raise ValidationError("Conflicting inspection / Consulta incompatible") from error


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, restriction_id, key, version, reason, ground, resume_message_id=None):
    fresh, case, person, subject, restriction = locked(user, case_id, restriction_id)
    signature = fingerprint(
        canonical(
            {
                "restriction": restriction.pk,
                "version": version,
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
            and previous.operation == "purpose_rel_propose"
            and previous.payload_digest == signature
        ):
            return PurposeReleaseProposal.objects.get(action=previous)
        raise ValidationError("Conflicting replay / Reintento incompatible")
    proof = current(user, case, person, restriction, version)
    digest = source(case, restriction, subject)
    if (
        not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or not PurposeRestrictionRead.objects.filter(
            restriction=restriction,
            action__actor=fresh,
            action__expected_version=version,
            proof=proof,
            source_digest=digest,
        ).exists()
    ):
        raise ValidationError(
            "Inspect current restriction before proposal / Consulta restricción vigente antes de proponer"
        )
    message = None
    if restriction.mode == "restrict":
        if ground != "restriction_resolved" or resume_message_id:
            raise ValidationError(
                "Reviewed restriction grounds required / Fundamento de limitación revisado obligatorio"
            )
    else:
        message = RightsMessage.objects.filter(
            pk=resume_message_id, request=case, created_at__gt=restriction.execution.created_at
        ).first()
        if (
            ground != "resume_requested"
            or not message
            or message.actor_id not in {None, subject.pk}
        ):
            raise ValidationError(
                "Reviewed new subject request required / Nueva solicitud del sujeto revisada obligatoria"
            )
    text = "Se propone levantar la restricción sobre preferencias de cuenta tras revisión independiente. La medida sigue activa hasta nueva comprobación y ejecución; los favoritos se conservan. Simulación de desarrollo; identidad no comprobada. / Release of the account preferences restriction is proposed after independent review. The restriction remains active pending a fresh check and execution; favorites are preserved. Development simulation; identity not verified."
    try:
        with transaction.atomic():
            response = issue(
                fresh,
                case.pk,
                uuid.uuid4(),
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
                operation="purpose_rel_propose",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = PurposeReleaseProposal.objects.create(
                restriction=restriction,
                action=action,
                proof=proof,
                response=response,
                source_digest=digest,
                ground=ground,
                resume_message=message,
            )
            case.refresh_from_db()
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status"])
            permission(user, case, restriction)
            return result
    except IntegrityError as error:
        raise ValidationError("Conflicting proposal / Propuesta incompatible") from error


@transaction.atomic
@sensitive_variables()
def execute(user, case_id, restriction_id, key, version, proposal_id, reason):
    fresh, case, person, subject, restriction = locked(user, case_id, restriction_id)
    proposal = (
        PurposeReleaseProposal.objects.select_for_update(of=("self",))
        .select_related("response", "proof")
        .filter(pk=proposal_id, restriction=restriction, action__request=case)
        .first()
    )
    if not proposal:
        raise ValidationError(
            "Release proposal unavailable / Propuesta de levantamiento no disponible"
        )
    signature = fingerprint(
        canonical(
            {
                "restriction": restriction.pk,
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
            and previous.operation == "purpose_rel_execute"
            and previous.payload_digest == signature
        ):
            return PurposeReleaseProposal.objects.get(released_action=previous)
        raise ValidationError("Conflicting replay / Reintento incompatible")
    proposal.proof.refresh_from_db(fields=["status"])
    try:
        original_reason = unseal(proposal.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError("Proposal record invalid / Registro de propuesta inválido") from error
    expected = fingerprint(
        canonical(
            {
                "restriction": restriction.pk,
                "version": proposal.action.expected_version,
                "reason": original_reason,
                "ground": proposal.ground,
                "resume_message": proposal.resume_message_id,
            }
        )
    )
    if expected != proposal.action.payload_digest:
        raise ValidationError("Proposal record changed / Registro de propuesta cambiado")
    # Read authority and proof after every explicit scope/proposal lock.
    proof = current(user, case, person, restriction, version)
    ack = getattr(proposal.response, "receipt_acknowledgement", None)
    latest = restriction.release_proposals.order_by("-pk").first()
    if (
        proposal.released_at
        or proposal.action.actor_id != fresh.pk
        or not latest
        or latest.pk != proposal.pk
        or proposal.source_digest != source(case, restriction, subject)
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
        raise ValidationError(
            "Current proposal, prior receipt and later scoped check required / Propuesta vigente, recepción previa y comprobación posterior obligatorias"
        )
    original_plan(restriction)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="purpose_rel_execute",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            restriction.active = False
            restriction.save(update_fields=["active"])
            proposal.released_action = action
            proposal.released_proof = proof
            proposal.released_at = timezone.now()
            proposal.save(update_fields=["released_action", "released_proof", "released_at"])
            case.version += 1
            case.scope_status = "unverified"
            case.save(update_fields=["version", "scope_status"])
            permission(user, case, restriction)
            return proposal
    except IntegrityError as error:
        raise ValidationError(
            "Conflicting release key / Clave de levantamiento incompatible"
        ) from error
