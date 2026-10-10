"""Private export of independently approved portable fields, never a final response."""

import hashlib
import io
import zipfile
from contextvars import ContextVar
from copy import copy
from functools import wraps
from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsExport, RightsExportPortabilityBinding
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority, validate_generated_scope
from .rights_exports import canonical, reviewer_case, source_copy
from .rights_object_content import image_bytes, part_bytes, seal_binary
from .rights_portability_review import validate_approved_assessment
from .rights_portability_selected_use import consume_selected
from .rights_portability_selection import project_selected
from .rights_portability_selection_review import validate_approved_selection
from .rights_portability_selection_store import validate_selection_evidence


def payload_for(projected, coverage=None):
    if coverage is not None:
        from .rights_portability_covered_export import coverage_summary

        return {
            **projected,
            "export_schema": "covered-portability-v1",
            "partial": False,
            "simulation": True,
            "pending_review": ["final_response"],
            "coverage": coverage_summary(coverage),
        }
    return {
        **projected,
        "partial": True,
        "simulation": True,
        "pending_review": ["image_content", "final_response"],
    }


@sensitive_variables()
def stored_reason(action):
    try:
        reason = unseal(action.encrypted_reason)["reason"]
    except (InvalidToken, KeyError, ValueError, TypeError) as error:
        raise ValidationError("Portability export reason unavailable") from error
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Portability export reason unavailable")
    return reason


def legacy_signature(binding, version, reason, payload):
    return fingerprint(
        canonical(
            {
                "version": version,
                "reason": reason,
                "review": binding.review_id,
                "source": binding.source_digest,
                "selection": binding.selection_digest,
                "ciphertext": binding.ciphertext_digest,
                "inspection": binding.inspection_digest,
                "decision": binding.decision_digest,
                "payload": binding.payload_digest,
                "projection": fingerprint(canonical(payload)),
                "session": binding.original_session_version,
                "mfa": binding.original_mfa_version,
            }
        )
    )


def signature(binding, version, reason, payload):
    original = legacy_signature(binding, version, reason, payload)
    if binding.coverage_review_id is None:
        return original
    return fingerprint(
        canonical(
            {
                "schema": "covered-portability-v1",
                "original": original,
                "review": binding.coverage_review_id,
                "use": binding.coverage_use_id,
                "coverage": binding.coverage_digest,
                "ciphertext": binding.coverage_ciphertext_digest,
                "decision": binding.coverage_decision_digest,
                "reads": binding.coverage_reads_digest,
            }
        )
    )


@sensitive_variables()
def image_payload(export, declarations, person):
    """Rebuild attachment metadata only after checking approved source and snapshots.

    Each snapshot is decrypted once: the same bytes are compared with the current image and
    its declared digest and then used to rebuild its package byte for byte.
    """
    from .rights_copy_parts import PART_LIMIT, archive
    from .rights_exports import image_content

    snapshots = list(export.images.only("pk", "photo_id").order_by("created_at", "pk"))
    if len(snapshots) != len(declarations):
        raise ValidationError("Portable image snapshots changed")
    by_photo = {str(item.photo_id): item for item in snapshots}
    if len(by_photo) != len(snapshots):
        raise ValidationError("Duplicate portable image snapshots")
    by_identifier = {str(item.pk): item for item in snapshots}
    declared = {}
    for declaration in declarations:
        snapshot = by_photo.get(declaration["photo"])
        if snapshot is None:
            raise ValidationError("Portable image snapshot unavailable")
        declared[str(snapshot.pk)] = declaration

    def verified(identifier):
        snapshot, declaration = by_identifier[identifier], declared[identifier]
        _, current = image_content(person, declaration["photo"])
        try:
            content = image_bytes(snapshot)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Portable image snapshot unavailable") from error
        del snapshot.encrypted_content
        digest = hashlib.sha256(content).hexdigest()
        if content != current or digest != declaration["content_digest"]:
            raise ValidationError("Portable image content changed")
        return content, digest

    metadata, parts, seen = {}, [], []
    for position, part in enumerate(
        export.parts.exclude(attachments=[]).order_by("position").iterator(chunk_size=1), 1
    ):
        if part.position != position or not isinstance(part.attachments, list):
            raise ValidationError("Portable image package changed")
        for identifier in part.attachments:
            if not isinstance(identifier, str) or identifier not in declared or identifier in seen:
                raise ValidationError("Portable image package scope changed")
            seen.append(identifier)

        def items():
            # Rebuild in the same order without retaining all decrypted images.
            package_size = 22
            for identifier in part.attachments:
                content, digest = verified(identifier)
                name = identifier + ".webp"
                package_size += len(content) + 76 + 2 * len(name.encode("ascii"))
                if package_size > PART_LIMIT:
                    raise ValidationError("Portable image package exceeds size limit")
                metadata[identifier] = {
                    "attachment": identifier,
                    "content_type": "image/webp",
                    "sha256": digest,
                    "size": len(content),
                }
                yield identifier, name, content

        expected = archive(items(), PART_LIMIT)["content"]
        try:
            content = part_bytes(part)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Portable image package unavailable") from error
        if content != expected:
            raise ValidationError("Portable image package content changed")
        parts.append({"id": str(part.pk), "position": position, "attachments": part.attachments})
        del expected, content, part.encrypted_content
    if set(seen) != set(declared):
        raise ValidationError("Portable image packages incomplete")
    images = [metadata[str(by_photo[item["photo"]].pk)] for item in declarations]
    return {"images": images, "parts": parts} if declarations else {}


@sensitive_variables()
def validate_transport(export, payload):
    """Bind every encrypted transport fragment to the approved projection."""
    from .rights_data_parts import json_chunks

    stored = unseal(export.encrypted_payload)
    if stored == payload:
        if export.parts.filter(attachments=[]).exists():
            raise ValidationError("Unexpected portability attachments")
        return
    if not isinstance(stored, dict) or stored.get("schema") != "rights-data-manifest-v1":
        raise ValidationError("Portability transport changed")
    expected_digest, expected_size = hashlib.sha256(), 0
    for chunk in json_chunks(payload):
        expected_digest.update(chunk)
        expected_size += len(chunk)
    if (
        stored.get("document_schema") != payload["schema"]
        or stored.get("sha256") != expected_digest.hexdigest()
        or stored.get("size") != expected_size
        or stored.get("parts") != payload.get("parts", [])
    ):
        raise ValidationError("Portability transport changed")
    descriptions = stored.get("data_parts")
    if not isinstance(descriptions, list) or not descriptions:
        raise ValidationError("Portability fragments unavailable")
    fragments = list(export.parts.filter(attachments=[]).order_by("position"))
    if len(fragments) != len(descriptions):
        raise ValidationError("Portability fragments changed")
    actual_digest, actual_size = hashlib.sha256(), 0
    try:
        for position, (part, metadata) in enumerate(zip(fragments, descriptions, strict=True), 1):
            if (
                not isinstance(metadata, dict)
                or part.attachments
                or metadata.get("id") != str(part.pk)
                or part.position != position + len(payload.get("parts", []))
                or metadata.get("position") != part.position
                or metadata.get("fragment_position") != position
            ):
                raise ValidationError("Portability fragment binding changed")
            with zipfile.ZipFile(io.BytesIO(part_bytes(part))) as archive:
                entries = archive.infolist()
                if (
                    len(entries) != 1
                    or entries[0].filename != metadata.get("filename")
                    or entries[0].file_size != metadata.get("size")
                    or entries[0].file_size > expected_size
                ):
                    raise ValidationError("Portability fragment size changed")
                content = archive.read(entries[0])
            if hashlib.sha256(content).hexdigest() != metadata.get("sha256"):
                raise ValidationError("Portability fragment digest changed")
            actual_digest.update(content)
            actual_size += len(content)
    except (zipfile.BadZipFile, KeyError, TypeError, ValueError, RuntimeError) as error:
        raise ValidationError("Portability fragments unavailable") from error
    if actual_size != expected_size or actual_digest.hexdigest() != expected_digest.hexdigest():
        raise ValidationError("Portability document changed")


_operation = ContextVar("portability_export_operation", default=None)


def one_export_validation(function):
    """Within one audited operation and its transaction, an identical export validation runs
    once: a second consecutive full check of the same export, case version and subject adds no
    guarantee beyond "validated in this transaction before use". Never spans transactions."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        if _operation.get() is not None:
            return function(*args, **kwargs)
        token = _operation.set({"connection": transaction.get_connection(), "validated": set()})
        try:
            return function(*args, **kwargs)
        finally:
            _operation.reset(token)

    return wrapper


@sensitive_variables()
def validate_export_binding(case, person, export):
    """Historical evidence only; caller must authorize and audit delivery first."""
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Portability export requires enclosing transaction")
    scope = _operation.get()
    connection = transaction.get_connection()
    # The outermost atomic block identifies this transaction: a result never crosses commits.
    identity = (
        id(connection.atomic_blocks[0]),
        case.pk,
        case.version,
        case.kind,
        case.status,
        person.pk if person else None,
        export.pk,
        export.case_version,
        fingerprint(export.encrypted_payload),
    )
    if scope is not None and scope["connection"] is transaction.get_connection():
        if identity in scope["validated"]:
            return
        _sealed_or_full(case, person, export)
        scope["validated"].add(identity)
        return
    _sealed_or_full(case, person, export)


@sensitive_variables()
def _sealed_or_full(case, person, export):
    """A held seal proves identical database inputs; image bytes are still re-read and hashed."""
    from .rights_validation_seal import caller_digest, create, holds, recording

    if case.kind != "portability":
        # This guard is one query; a portability seal cannot validate another procedure.
        return _validate_export_binding(case, person, export)
    caller = {"case": case, "person": person, "export": export}
    if holds(export, caller):
        from .rights_object_content import verify_export_objects

        verify_export_objects(export)
        _verify_current_images(export, person)
        return
    initial_digest = caller_digest(*caller.values())
    with recording() as state:
        _validate_export_binding(case, person, export)
    state["caller_digest"] = initial_digest
    create(export, state, caller)


@sensitive_variables()
def _verify_current_images(export, person):
    from .rights_exports import image_content

    binding = RightsExportPortabilityBinding.objects.select_related("review__selection").get(
        export=export
    )
    declarations = unseal(binding.review.selection.encrypted_selection).get("images", [])
    for declaration in declarations:
        _, current = image_content(person, declaration["photo"])
        if hashlib.sha256(current).hexdigest() != declaration["content_digest"]:
            raise ValidationError("Portable image content changed")
        del current


@sensitive_variables()
def _validate_export_binding(case, person, export):
    binding = (
        RightsExportPortabilityBinding.objects.select_for_update(of=("self",))
        .select_related(
            "review__action",
            "review__read__action",
            "review__selection__action",
            "review__selection__assessment_review__assessment__action",
            "review__selection__assessment_review__action",
            "review__selection__assessment_review__read__action",
        )
        .filter(export=export)
        .first()
    )
    if case.kind != "portability":
        if binding:
            raise ValidationError("Unexpected portability export binding")
        return
    if not binding:
        raise ValidationError("Portability export binding required")
    decision = binding.review
    row = decision.selection
    review = row.assessment_review
    original = copy(case)
    original.version = export.action.expected_version
    from apps.listings.models import Listing

    listing = Listing.objects.select_for_update().filter(person=person).first() if person else None
    source = source_copy(person, listing, original)
    source_digest = fingerprint(canonical(source))
    if (
        export.action.request_id != case.pk
        or export.action.operation != "portability_export"
        or export.action.actor_id != row.actor_id
        or export.case_version != case.version
        or case.version != original.version + 1
        or row.request_id != case.pk
        or row.proof_id != export.proof_id
        or binding.source_digest != source_digest
        or row.source_digest != source_digest
        or binding.selection_digest != row.selection_digest
        or binding.ciphertext_digest != fingerprint(row.encrypted_selection)
        or binding.inspection_digest != decision.read.action.payload_digest
        or binding.decision_digest != decision.action.payload_digest
        or binding.payload_digest != fingerprint(export.encrypted_payload)
        or export.expires_at
        > min(row.expires_at, review.assessment.expires_at, export.proof.expires_at)
        or export.expires_at <= timezone.now()
        or export.purged_at
    ):
        raise ValidationError("Portability export binding changed")
    assessment = validate_approved_assessment(
        review,
        review.assessment,
        original,
        export.proof,
        source_digest,
        unseal(review.assessment.encrypted_assessment),
    )
    validate_approved_selection(decision, row, original, export.proof)
    selected = validate_selection_evidence(row, review, original)
    from .rights_portability_covered_export import validate_binding

    coverage = validate_binding(binding, original, export.proof, source)
    payload = payload_for(
        project_selected(
            source, assessment, selected["selection"], field_evidence=selected.get("field_evidence")
        ),
        coverage,
    )
    payload.update(image_payload(export, selected.get("images", []), person))
    reason = stored_reason(export.action)
    if export.action.payload_digest != signature(binding, original.version, reason, payload):
        raise ValidationError("Portability export signature changed")
    validate_transport(export, payload)


@transaction.atomic
@one_export_validation
@sensitive_variables()
def generate(
    user, case_id, version, selection_id, review_id, key, reason, *, coverage_review_id=None
):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Portability export reason required")
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, user.session_version, user.mfa_version)
    if not actor.is_active or case.kind != "portability" or case.status != "reviewing":
        raise ValidationError("Current portability request required")
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        export = (
            RightsExport.objects.select_related("proof", "action").filter(action=previous).first()
        )
        binding = (
            RightsExportPortabilityBinding.objects.filter(export=export).first() if export else None
        )
        if (
            not binding
            or previous.actor_id != actor.pk
            or previous.request_id != case.pk
            or previous.expected_version != version
            or previous.operation != "portability_export"
            or binding.review_id != review_id
            or binding.review.selection_id != selection_id
            or binding.coverage_review_id != coverage_review_id
            or binding.original_session_version != user.session_version
            or binding.original_mfa_version != user.mfa_version
        ):
            raise ValidationError("Conflicting portability export key")
        validate_generated_scope(
            case, person, listing, export, actor, version, binding.source_digest
        )
        validate_export_binding(case, person, export)
        if stored_reason(previous) != reason:
            raise ValidationError("Conflicting portability export reason")
        return export
    coverage_decision, coverage = None, None
    coverage_key = uuid5(key, "approved-portability-coverage-use")
    if coverage_review_id is not None:
        from .rights_portability_coverage_use import consume_approved_coverage

        coverage_decision, coverage = consume_approved_coverage(
            user,
            case.pk,
            version,
            coverage_review_id,
            coverage_key,
            "Validate full approved coverage before portability export",
        )
        if coverage_decision.coverage.selection_review_id != review_id:
            raise ValidationError("Coverage selection approval changed")
    row, projected = consume_selected(
        user,
        case_id,
        version,
        selection_id,
        review_id,
        uuid5(key, "approved-portability-selection-use"),
        reason,
    )
    payload = payload_for(projected, coverage)
    image_decisions = unseal(row.encrypted_selection).get("images", [])
    action = RightsAction.objects.create(
        key=key,
        request=case,
        actor=actor,
        expected_version=version,
        operation="portability_export",
        payload_digest="",
        encrypted_reason=seal({"reason": reason}),
    )
    export = RightsExport.objects.create(
        action=action,
        proof=row.proof,
        person=person,
        account_subject_id=case.account_subject_id,
        case_version=version + 1,
        manager_version=person.manager_version if person else None,
        subject_snapshot=str(person.subject_id or "") if person else str(case.account_subject_id),
        channel_digest=case.receipt_digest,
        encrypted_payload="",
        expires_at=min(row.expires_at, coverage_decision.coverage.expires_at)
        if coverage_decision
        else row.expires_at,
    )
    from .models import RightsPortabilitySelectionReview
    from .rights_data_parts import stored_payload

    if image_decisions:
        from .models import RightsExportImage, RightsExportPart
        from .rights_copy_parts import packages
        from .rights_exports import image_content

        def snapshots():
            for declaration in image_decisions:
                photo, content = image_content(person, declaration["photo"])
                if hashlib.sha256(content).hexdigest() != declaration["content_digest"]:
                    raise ValidationError("Portable image content changed")
                snapshot = RightsExportImage.objects.create(
                    export=export,
                    photo=photo,
                    encrypted_content=seal_binary(content, export.pk, "image", photo.pk),
                )
                yield snapshot.pk, content

        for position, package in enumerate(packages(snapshots()), 1):
            RightsExportPart.objects.create(
                export=export,
                position=position,
                attachments=package["attachments"],
                encrypted_content=seal_binary(package["content"], export.pk, "part", position),
            )
        payload.update(image_payload(export, image_decisions, person))
    export.encrypted_payload = stored_payload(export, payload)
    export.save(update_fields=["encrypted_payload"])
    decision = RightsPortabilitySelectionReview.objects.select_related(
        "action", "read__action"
    ).get(pk=review_id)
    binding = RightsExportPortabilityBinding.objects.create(
        export=export,
        review=decision,
        source_digest=row.source_digest,
        selection_digest=row.selection_digest,
        ciphertext_digest=fingerprint(row.encrypted_selection),
        inspection_digest=decision.read.action.payload_digest,
        decision_digest=decision.action.payload_digest,
        payload_digest=fingerprint(export.encrypted_payload),
        original_session_version=user.session_version,
        original_mfa_version=user.mfa_version,
    )
    if coverage_decision is not None:
        binding.coverage_review = coverage_decision
        binding.coverage_use = RightsAction.objects.get(key=coverage_key)
        binding.coverage_digest = coverage_decision.coverage.coverage_digest
        binding.coverage_ciphertext_digest = fingerprint(
            coverage_decision.coverage.encrypted_coverage
        )
        binding.coverage_decision_digest = coverage_decision.action.payload_digest
        binding.coverage_reads_digest = fingerprint(canonical(coverage_decision.read_ids))
        binding.save(
            update_fields=[
                "coverage_review",
                "coverage_use",
                "coverage_digest",
                "coverage_ciphertext_digest",
                "coverage_decision_digest",
                "coverage_reads_digest",
            ]
        )
    action.payload_digest = signature(binding, version, reason, payload)
    action.save(update_fields=["payload_digest"])
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    validate_generated_scope(case, person, listing, export, actor, version, row.source_digest)
    validate_export_binding(case, person, export)
    fresh_authority(actor, case, user.session_version, user.mfa_version)
    return export
