"""Scoped information drafts; saving never resolves an access or portability request."""

from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsCopyInformation
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy

FIELDS = (
    "processing",
    "purposes",
    "categories",
    "recipients",
    "retention",
    "rights",
    "complaint",
    "origins",
    "automation",
    "transfers",
)


def checked_information(kind, value):
    if not isinstance(value, dict) or set(value) != {"access", "portability"}:
        raise ValidationError("Invalid information schema")
    access = value["access"]
    if not isinstance(access, dict) or set(access) != set(FIELDS):
        raise ValidationError("Review every information field")
    for item in access.values():
        if not isinstance(item, dict) or set(item) != {"status", "text", "source"}:
            raise ValidationError("Invalid information field")
        if not isinstance(item["status"], str) or not isinstance(item["source"], str):
            raise ValidationError("Invalid information provenance")
        if not isinstance(item["text"], str) or len(item["text"]) > 4000:
            raise ValidationError("Invalid information text")
        if item["status"] == "pending":
            if item["text"] or item["source"] != "unknown":
                raise ValidationError("Pending information cannot assert facts")
        elif item["status"] == "reviewed":
            if not item["text"].strip() or item["source"] not in {
                "configuration",
                "inventory",
                "reviewer",
            }:
                raise ValidationError("Reviewed information requires provenance")
        else:
            raise ValidationError("Invalid information status")
    portability = value["portability"]
    if kind == "access":
        if portability is not None:
            raise ValidationError("Access does not imply portability assessment")
    elif not isinstance(portability, dict) or set(portability) != {"status", "reason"}:
        raise ValidationError("Separate portability assessment required")
    elif portability["status"] != "pending" or portability["reason"] != "":
        # Eligibility/dataset decisions require a dedicated reviewed workflow, still pending.
        raise ValidationError("Portability eligibility workflow not yet available")
    return value


@transaction.atomic
@sensitive_variables()
def record(
    user,
    case_id,
    case_version,
    key,
    information_version,
    policy_version,
    reason,
    information,
    *,
    expected_source_digest=None,
):
    if (
        type(information_version) is not int
        or information_version < 0
        or not isinstance(policy_version, str)
        or not 1 <= len(policy_version.strip()) <= 80
        or not isinstance(reason, str)
        or not 10 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Invalid information draft")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if case.version != case_version:
        raise ValidationError("Request changed")
    proof = can_prepare(actor, case, person)
    cleaned = checked_information(case.kind, information)
    digest = fingerprint(canonical(source_copy(person, listing, case)))
    if expected_source_digest is not None and expected_source_digest != digest:
        raise ValidationError("Information source changed")
    signature = fingerprint(
        canonical(
            {
                "version": case_version,
                "information_version": information_version,
                "policy": policy_version,
                "reason": reason,
                "information": cleaned,
                "source": digest,
                "proof": str(proof.pk),
                "session": session_version,
                "mfa": mfa_version,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_info_save"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting information key")
        row = RightsCopyInformation.objects.filter(
            action=previous,
            proof=proof,
            source_digest=digest,
            purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
        if not row or not row.encrypted_information:
            raise ValidationError("Information unavailable")
    else:
        latest = (
            RightsCopyInformation.objects.filter(request=case, actor=actor)
            .order_by("-version")
            .first()
        )
        if information_version != (latest.version if latest else 0):
            raise ValidationError("Information version changed")
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=case_version,
                    operation="copy_info_save",
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
                row = RightsCopyInformation.objects.create(
                    request=case,
                    actor=actor,
                    action=action,
                    proof=proof,
                    source_digest=digest,
                    policy_version=policy_version,
                    version=information_version + 1,
                    encrypted_information=seal(cleaned),
                    expires_at=min(proof.expires_at, timezone.now() + timedelta(hours=24)),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting information draft") from error
    try:
        stored = unseal(row.encrypted_information)
    except (InvalidToken, ValueError, TypeError) as error:
        raise ValidationError("Information unavailable") from error
    if (
        canonical(stored) != canonical(cleaned)
        or row.policy_version != policy_version
        or row.version != information_version + 1
    ):
        raise ValidationError("Information evidence changed")
    if (
        can_prepare(User.objects.get(pk=actor.pk), case, person).pk != proof.pk
        or fingerprint(canonical(source_copy(person, listing, case))) != digest
    ):
        raise ValidationError("Information source changed")
    fresh_authority(actor, case, session_version, mfa_version)
    return row


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, case_version, key, information_id, purpose):
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Invalid information access purpose")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if case.version != case_version:
        raise ValidationError("Request changed")
    proof = can_prepare(actor, case, person)
    digest = fingerprint(canonical(source_copy(person, listing, case)))
    row = (
        RightsCopyInformation.objects.select_for_update()
        .filter(
            pk=information_id,
            request=case,
            actor=actor,
            proof=proof,
            source_digest=digest,
            purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if not row or not row.encrypted_information:
        raise ValidationError("Information unavailable")
    signature = fingerprint(
        canonical(
            {
                "information": row.pk,
                "version": row.version,
                "source": digest,
                "purpose": purpose,
                "session": session_version,
                "mfa": mfa_version,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_info_read"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting information access key")
    else:
        try:
            with transaction.atomic():
                RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=case_version,
                    operation="copy_info_read",
                    payload_digest=signature,
                    encrypted_reason=seal({"purpose": purpose}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting information access key") from error
    try:
        information = unseal(row.encrypted_information)
        reason = unseal(row.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Information unavailable") from error
    record(
        user,
        case_id,
        case_version,
        row.action.key,
        row.version - 1,
        row.policy_version,
        reason,
        information,
    )
    fresh_authority(actor, case, session_version, mfa_version)
    return row, information
