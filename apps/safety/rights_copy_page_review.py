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
    if section == "personal_contacts":
        scoped = {
            "profile": None,
            "subject_account": None,
            "revisions": [],
            "account_activity": {"personal_contacts": original},
        }
        value = {**scoped, "account_activity": {"personal_contacts": proposed}}
        return reviewed_copy(scoped, value)["account_activity"]["personal_contacts"]
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


@transaction.atomic
@sensitive_variables()
def compile_pages(user, case_id, case_version, key, reason):
    """Compile every latest reviewed page; retain the projection's partial-copy flags."""
    from uuid import uuid5

    from .models import RightsExportPreview

    if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Invalid compilation reason")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if case.version != case_version:
        raise ValidationError("Request changed")
    proof = can_prepare(actor, case, person)
    source = source_copy(person, listing, case)
    digest = fingerprint(canonical(source))
    candidates = RightsCopyPageReview.objects.filter(
        request=case, actor=actor, source_digest=digest
    ).order_by("section", "page", "-version")
    latest = {}
    for row in candidates:
        latest.setdefault((row.section, row.page), row)
    required = [
        (section, page)
        for section, projection in SECTIONS.items()
        for page in range(1, max(1, (len(projection(source)) + PAGE_SIZE - 1) // PAGE_SIZE) + 1)
    ]
    if any(position not in latest for position in required):
        raise ValidationError("Review every current section page first")
    selected = [latest[position] for position in required]
    signature = fingerprint(
        canonical(
            {
                "source": digest,
                "version": case_version,
                "reason": reason,
                "reviews": [(row.pk, row.version) for row in selected],
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_pages_compile"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting compilation key")
    compiled = deepcopy(source)
    for section in SECTIONS:
        entries = []
        for position in required:
            if position[0] != section:
                continue
            row = latest[position]
            if row.proof_id != proof.pk:
                raise ValidationError("Page review proof changed")
            recovered = inspect_saved(
                user,
                case.pk,
                case.version,
                uuid5(key, "compiled-review:" + str(row.pk)),
                row.pk,
                "Compile current reviewed copy page",
            )
            entries.extend(recovered["entries"])
        if section in {"profile", "subject_account"}:
            compiled[section] = entries[0] if entries else None
        elif section in {"favorites", "personal_contacts", "agency_relationships"}:
            compiled["account_activity"][section] = entries
        elif section in {"verifications", "representation_history"}:
            if compiled["representation"] is not None:
                compiled["representation"][
                    "history" if section == "representation_history" else section
                ] = entries
        else:
            compiled[section] = entries
    cleaned = reviewed_copy(source, compiled)
    if not previous:
        try:
            with transaction.atomic():
                RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=case.version,
                    operation="copy_pages_compile",
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
                RightsExportPreview.objects.create(
                    request=case,
                    actor=actor,
                    case_version=case.version,
                    source_digest=digest,
                    purpose="Compiled all current reviewed section pages",
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting compilation key") from error
    fresh_authority(actor, case, session_version, mfa_version)
    return cleaned


@sensitive_variables()
def validate_generated_scope(case, person, listing, export, actor, version, source_digest):
    from .rights_verification import PROCEDURE, compatible, enabled

    case.refresh_from_db()
    proof = case.proofs.order_by("-created_at", "-pk").first()
    if (
        not enabled()
        or not proof
        or proof.pk != export.proof_id
        or proof.status != "passed"
        or proof.provider != "simulator"
        or proof.procedure != PROCEDURE
        or not compatible(case, person, proof, case_version=version)
        or case.assigned_to_id != actor.pk
        or case.version != export.case_version
        or export.case_version != version + 1
        or export.person_id != case.person_id
        or export.account_subject_id != case.account_subject_id
        or export.manager_version != case.manager_version
        or export.subject_snapshot != proof.subject_id_snapshot
        or export.channel_digest != case.receipt_digest
        or export.expires_at <= timezone.now()
        or export.purged_at
        or not export.encrypted_payload
        or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
    ):
        raise ValidationError("Page export no longer available")


@transaction.atomic
@sensitive_variables()
def generate_pages(user, case_id, case_version, key, reason, *, information_review_id=None):
    """Generate server-side from latest decisions; retry returns only a still-valid export."""
    from uuid import uuid5

    from .models import RightsExport
    from .rights_exports import generate
    from .rights_verification import PROCEDURE, compatible, enabled

    if not isinstance(reason, str) or not 10 <= len(reason.strip()) <= 2000:
        raise ValidationError("Invalid page export reason")
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    signature_input = {"version": case_version, "reason": reason}
    if information_review_id is not None:
        signature_input["information_review"] = information_review_id
    signature = fingerprint(canonical(signature_input))
    previous = RightsAction.objects.filter(key=key).first()
    export_key = uuid5(key, "reviewed-pages-export")
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.operation != "copy_pages_export"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting page export key")
        export = (
            RightsExport.objects.select_related("proof")
            .filter(
                action__key=export_key,
                action__request=case,
                action__actor=actor,
                action__operation="export",
            )
            .first()
        )
        try:
            facts = unseal(previous.encrypted_reason)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Page export evidence unavailable") from error
        if not isinstance(facts, dict):
            raise ValidationError("Page export evidence unavailable")
        latest_proof = case.proofs.order_by("-created_at", "-pk").first()
        if (
            not export
            or not enabled()
            or case.assigned_to_id != actor.pk
            or case.kind not in {"access", "portability"}
            or case.version != export.case_version
            or export.case_version != case_version + 1
            or export.expires_at <= timezone.now()
            or export.purged_at
            or not export.encrypted_payload
            or export.channel_digest != case.receipt_digest
            or not latest_proof
            or latest_proof.pk != export.proof_id
            or export.proof.provider != "simulator"
            or export.proof.procedure != PROCEDURE
            or export.proof.status != "passed"
            or not compatible(case, person, export.proof, case_version=case_version)
            or facts.get("session") != session_version
            or facts.get("mfa") != mfa_version
            or facts.get("source") != fingerprint(canonical(source_copy(person, listing, case)))
        ):
            raise ValidationError("Page export no longer available")
        validate_generated_scope(
            case, person, listing, export, actor, case_version, facts["source"]
        )
        if information_review_id is not None:
            from .models import RightsExportInformationBinding
            from .rights_information_export import validate_export_binding

            if not RightsExportInformationBinding.objects.filter(
                export=export, review_id=information_review_id
            ).exists():
                raise ValidationError("Export information binding unavailable")
            validate_export_binding(case, person, export)
        fresh_authority(actor, case, session_version, mfa_version)
        return export
    compiled = compile_pages(user, case_id, case_version, uuid5(key, "compile-pages"), reason)
    source_digest = fingerprint(canonical(source_copy(person, listing, case)))
    export = generate(
        actor,
        case_id,
        export_key,
        case_version,
        reason,
        compiled,
        information_review_id=information_review_id,
    )
    try:
        with transaction.atomic():
            RightsAction.objects.create(
                key=key,
                request=case,
                actor=actor,
                expected_version=case_version,
                operation="copy_pages_export",
                payload_digest=signature,
                encrypted_reason=seal(
                    {
                        "reason": reason,
                        "session": session_version,
                        "mfa": mfa_version,
                        "source": source_digest,
                    }
                ),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting page export key") from error
    validate_generated_scope(case, person, listing, export, actor, case_version, source_digest)
    fresh_authority(actor, case, session_version, mfa_version)
    return export
