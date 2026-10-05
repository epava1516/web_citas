"""Development-only destination confirmation; it never applies an account correction."""

import hashlib
import json
import secrets
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import RightsAccountEmailConfirmation, RightsAction, RightsRectificationProposalRead
from .rectification_account import locked_subject, validate
from .rectification_review import current, permission
from .rights import fingerprint
from .rights_rectification import source_snapshot
from .rights_scope import locked_case, permitted


def enabled():
    return (
        not settings.PRODUCTION
        and getattr(settings, "ACCOUNT_CORRECTION_DELIVERY_BACKEND", "disabled") == "simulator"
    )


@transaction.atomic
@sensitive_variables()
def start(user, case_id, proposal_id, key, version, reason, language="es"):
    if not enabled():
        raise PermissionDenied("Account confirmation delivery disabled")
    permission(user)
    case, person, listing = locked_case(case_id, lock_listing=True)
    if not permitted(user, case) or language not in {"es", "en"}:
        raise PermissionDenied
    signature = fingerprint(
        json.dumps(
            {
                "proposal": proposal_id,
                "version": version,
                "reason": reason,
                "language": language,
            },
            sort_keys=True,
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "account_email"
            and previous.payload_digest == signature
        ):
            return RightsAccountEmailConfirmation.objects.get(action=previous)
        raise ValidationError("Conflicting confirmation key / Clave de confirmación incompatible")
    case, proposal, proof, changes = current(user, case_id, proposal_id, version)
    review = getattr(proposal, "rightsrectificationreview", None)
    if (
        not review
        or review.outcome != "approved"
        or review.action.actor_id != user.pk
        or proof.created_at <= review.created_at
        or not 20 <= len(reason.strip()) <= 2000
        or "account" not in changes
        or not RightsRectificationProposalRead.objects.filter(
            proposal=proposal,
            actor=user,
            proof=proof,
            case_version=version,
            changes_digest=fingerprint(json.dumps(changes, sort_keys=True)),
        ).exists()
    ):
        raise ValidationError(
            "Current approved account correction required / Corrección de cuenta aprobada vigente obligatoria"
        )
    destination = changes["account"].get("email")
    if not destination or destination == locked_subject(person, case).email.lower():
        raise ValidationError("A changed destination is required / Es obligatorio un destino nuevo")
    raw = secrets.token_urlsafe(32)
    now = timezone.now()
    RightsAccountEmailConfirmation.objects.filter(
        proposal=proposal,
        revoked_at__isnull=True,
        consumed_at__isnull=True,
    ).update(revoked_at=now, encrypted_delivery="")
    try:
        action = RightsAction.objects.create(
            key=key,
            request=case,
            actor=user,
            expected_version=version,
            operation="account_email",
            payload_digest=signature,
            encrypted_reason=seal({"reason": reason}),
        )
    except IntegrityError as error:
        raise ValidationError(
            "Conflicting confirmation key / Clave de confirmación incompatible"
        ) from error
    result = RightsAccountEmailConfirmation.objects.create(
        action=action,
        proposal=proposal,
        proof=proof,
        subject_id=locked_subject(person, case).pk,
        digest=hashlib.sha256(raw.encode()).hexdigest(),
        source_digest=proposal.source_digest,
        destination_digest=fingerprint(destination),
        encrypted_delivery="",
        expires_at=now + timedelta(hours=24),
    )
    url = settings.PUBLIC_ORIGIN + f"/{language}/safety/account-email/{result.pk}/{raw}/"
    result.encrypted_delivery = seal({"simulation": True, "destination": destination, "url": url})
    result.save(update_fields=["encrypted_delivery"])
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return result


@transaction.atomic
@sensitive_variables()
def inspect_token(confirmation_id, raw, confirm=False):
    if not enabled() or not isinstance(raw, str) or len(raw) > 100:
        raise ValidationError("Confirmation unavailable / Confirmación no disponible")
    initial = RightsAccountEmailConfirmation.objects.select_related("proposal__action").get(
        pk=confirmation_id
    )
    case, person, listing = locked_case(initial.proposal.action.request_id, lock_listing=True)
    if not person and not case.account_subject_id:
        raise ValidationError("Confirmation unavailable / Confirmación no disponible")
    _, source = source_snapshot(case, person, listing)
    token = RightsAccountEmailConfirmation.objects.select_for_update().get(pk=initial.pk)
    latest = (
        type(token.proposal)
        .objects.filter(action__request=case)
        .order_by("-created_at", "-pk")
        .first()
    )
    changes = unseal(token.proposal.encrypted_changes)
    account = validate(changes.get("account"), person, case)
    if (
        case.status != "reviewing"
        or not latest
        or latest.pk != token.proposal_id
        or locked_subject(person, case).pk != token.subject_id
        or token.proof.status != "passed"
        or token.revoked_at
        or token.consumed_at
        or token.expires_at <= timezone.now()
        or not constant_time_compare(token.digest, hashlib.sha256(raw.encode()).hexdigest())
        or token.source_digest != fingerprint(json.dumps(source, sort_keys=True))
        or token.destination_digest != fingerprint(account.get("email", ""))
    ):
        raise ValidationError("Confirmation unavailable / Confirmación no disponible")
    if confirm and not token.confirmed_at:
        token.confirmed_at = timezone.now()
        token.encrypted_delivery = ""
        token.save(update_fields=["confirmed_at", "encrypted_delivery"])
    return token


def purge_expired_delivery(limit=100):
    """Clear only expired link payloads, retaining the rights audit records."""
    from apps.core.models import User

    candidates = list(
        RightsAccountEmailConfirmation.objects.filter(expires_at__lte=timezone.now())
        .exclude(encrypted_delivery="")
        .order_by("expires_at", "pk")
        .values_list("pk", "proposal__action__request_id")[:limit]
    )
    cleared = 0
    for identifier, case_id in candidates:
        with transaction.atomic():
            _, person, _ = locked_case(case_id)
            if person and person.subject_id:
                User.objects.select_for_update().filter(pk=person.subject_id).first()
            token = RightsAccountEmailConfirmation.objects.select_for_update().get(pk=identifier)
            # Recheck after waiting; timestamps from the initial scan grant no authority.
            if token.expires_at <= timezone.now() and token.encrypted_delivery:
                token.encrypted_delivery = ""
                token.save(update_fields=["encrypted_delivery"])
                cleared += 1
    return cleared
