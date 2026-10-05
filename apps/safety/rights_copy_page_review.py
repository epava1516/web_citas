"""Versioned encrypted page decisions; no implicit whole-copy approval or release."""

from copy import deepcopy
from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsCopyPageReview
from .rights import fingerprint
from .rights_copy_inspection import PAGE_SIZE, SECTIONS, inspection_binding
from .rights_exports import can_prepare, canonical, reviewed_copy, reviewer_case, source_copy
from .rights_scope import permitted


@sensitive_variables()
def checked_entries(source, section, original, proposed):
    if not isinstance(proposed, list):
        raise ValidationError("Invalid reviewed page")
    if section in {"profile", "subject_account"}:
        if len(proposed) != len(original) or len(original) > 1:
            raise ValidationError("Invalid reviewed header")
        if not original:
            return []
        scoped = {"profile": None, "subject_account": None, "revisions": []}
        scoped[section] = original[0]
        value = {**scoped, section: proposed[0]}
        return [reviewed_copy(scoped, value)[section]]
    if section == "revisions":
        # Reuse the established text/image redaction rules on just this revision batch.
        scoped = {"profile": None, "subject_account": None, "revisions": original}
        result = reviewed_copy(scoped, {**scoped, "revisions": proposed})
        return result["revisions"]
    if canonical(original) != canonical(proposed):
        raise ValidationError("This section is immutable")
    return deepcopy(original)


def fresh_authority(actor, case, session_version, mfa_version):
    fresh = User.objects.get(pk=actor.pk)
    if (
        not fresh.has_perm("safety.review_rights_request")
        or not fresh.has_perm("safety.execute_rights_request")
        or not fresh.mfa_enabled
        or fresh.session_version != session_version
        or fresh.mfa_version != mfa_version
        or not permitted(fresh, case)
    ):
        raise PermissionDenied


@transaction.atomic
@sensitive_variables()
def record(user, case_id, case_version, key, read_id, page_version, reason, entries):
    if type(page_version) is not int or page_version < 0 or not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Invalid page review")
    original_session, original_mfa = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    if (
        not actor.has_perm("safety.review_rights_request")
        or not actor.mfa_enabled
        or actor.session_version != original_session
        or actor.mfa_version != original_mfa
        or not permitted(actor, case)
    ):
        raise PermissionDenied
    if case.version != case_version:
        raise ValidationError("Request changed")
    proof = can_prepare(actor, case, person)
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=actor,
        operation="copy_page_read",
        expected_version=case.version,
    ).first()
    if not read:
        raise ValidationError("Inspect the current page first")
    try:
        facts = unseal(read.encrypted_reason)
        section, page, purpose = facts["section"], facts["page"], facts["purpose"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Inspection evidence unavailable") from error
    if (
        not isinstance(section, str)
        or section not in SECTIONS
        or type(page) is not int
        or page < 1
        or not isinstance(purpose, str)
    ):
        raise ValidationError("Invalid inspection evidence")
    source = source_copy(person, listing, case)
    binding = inspection_binding(actor, case, proof, source, section)
    if read.payload_digest != fingerprint(
        canonical({"binding": binding, "page": page, "purpose": purpose})
    ):
        raise ValidationError("Inspection source changed")
    rows = SECTIONS[section](source)
    start = (page - 1) * PAGE_SIZE
    if start >= len(rows) and page != 1:
        raise ValidationError("Page unavailable")
    cleaned = checked_entries(source, section, rows[start : start + PAGE_SIZE], entries)
    signature = fingerprint(
        canonical(
            {
                "binding": binding,
                "read": read.pk,
                "page": page,
                "page_version": page_version,
                "reason": reason,
                "entries": cleaned,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_page_save"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting page review key")
        existing = RightsCopyPageReview.objects.filter(
            action=previous,
            proof=proof,
            source_digest=binding["source"],
            purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        ).first()
        if not existing or not existing.encrypted_entries:
            raise ValidationError("Page review unavailable")
        try:
            saved = unseal(existing.encrypted_entries)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Page review unavailable") from error
        if (
            canonical(saved) != canonical(cleaned)
            or existing.read_action_id != read.pk
            or existing.request_id != case.pk
            or existing.actor_id != actor.pk
            or existing.section != section
            or existing.page != page
            or existing.version != page_version + 1
        ):
            raise ValidationError("Page review evidence changed")
        fresh_authority(actor, case, original_session, original_mfa)
        return existing
    latest = (
        RightsCopyPageReview.objects.filter(
            request=case, actor=actor, source_digest=binding["source"], section=section, page=page
        )
        .order_by("-version")
        .first()
    )
    if page_version != (latest.version if latest else 0):
        raise ValidationError("Page review version changed")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=case.version,
                operation="copy_page_save",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = RightsCopyPageReview.objects.create(
                request=case,
                actor=actor,
                action=action,
                read_action=read,
                proof=proof,
                source_digest=binding["source"],
                section=section,
                page=page,
                version=page_version + 1,
                encrypted_entries=seal(cleaned),
                expires_at=min(proof.expires_at, timezone.now() + timedelta(hours=24)),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting page review") from error
    fresh_authority(actor, case, original_session, original_mfa)
    return result


@transaction.atomic
@sensitive_variables()
def inspect_saved(user, case_id, case_version, key, review_id, purpose):
    """Audit before decrypting; a stored decision never grants its own authority."""
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Invalid review access purpose")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if case.version != case_version:
        raise ValidationError("Request changed")
    proof = can_prepare(actor, case, person)
    row = (
        RightsCopyPageReview.objects.select_for_update()
        .filter(
            pk=review_id,
            request=case,
            actor=actor,
            proof=proof,
            purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .first()
    )
    if not row or not row.encrypted_entries or row.section not in SECTIONS:
        raise ValidationError("Page review unavailable")
    source = source_copy(person, listing, case)
    binding = inspection_binding(actor, case, proof, source, row.section)
    if binding["source"] != row.source_digest:
        raise ValidationError("Page review source changed")
    signature = fingerprint(
        canonical(
            {"binding": binding, "review": row.pk, "version": row.version, "purpose": purpose}
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_review_read"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting review access key")
    else:
        try:
            with transaction.atomic():
                RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=case.version,
                    operation="copy_review_read",
                    payload_digest=signature,
                    encrypted_reason=seal({"purpose": purpose, "review": row.pk}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting review access key") from error
    try:
        entries = unseal(row.encrypted_entries)
        reason = unseal(row.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Page review unavailable") from error
    if not isinstance(reason, str):
        raise ValidationError("Page review evidence changed")
    # Exact replay revalidates the original read, source, content and save signature.
    record(
        user,
        case.pk,
        case.version,
        row.action.key,
        row.read_action_id,
        row.version - 1,
        reason,
        entries,
    )
    fresh_authority(actor, case, session_version, mfa_version)
    return {
        "review_id": row.pk,
        "section": row.section,
        "page": row.page,
        "version": row.version,
        "entries": entries,
    }
