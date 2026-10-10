"""Audited preparation of final response text; never issues a response or closes."""

from copy import copy

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal, unseal
from .models import RightsAction, RightsExport, RightsPortabilityResponseDraft
from .rights import fingerprint
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case
from .rights_portability_export import one_export_validation, validate_export_binding
from .rights_response_text import checked_response_text
from .rights_responses import complete_response_read


@sensitive_variables()
def checked_body(ciphertext):
    try:
        return unseal(ciphertext)
    except (InvalidToken, ValueError, TypeError, UnicodeDecodeError) as error:
        raise ValidationError("Final response encrypted evidence unavailable") from error


@transaction.atomic
@one_export_validation
@sensitive_variables()
def prepare(user, case_id, version, response_version, export_id, key, reason, text, confirmed):
    checked_response_text(reason, text, confirmed)
    session_version, mfa_version = user.session_version, user.mfa_version
    case, person, _ = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session_version, mfa_version)
    if not actor.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    if (
        case.kind != "portability"
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != response_version
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect current request and responses before preparing final text")
    proof = can_prepare(actor, case, person)
    export = (
        RightsExport.objects.select_for_update(of=("self",))
        .select_related("action", "proof")
        .filter(pk=export_id, action__request=case, action__actor=actor)
        .first()
    )
    if export is None:
        raise ValidationError("Own covered export required")
    # Metadata lookup must precede any historical content validation.
    from .models import RightsExportPortabilityBinding

    binding = (
        RightsExportPortabilityBinding.objects.select_for_update().filter(export=export).first()
    )
    if (
        binding is None
        or binding.coverage_review_id is None
        or proof.pk == export.proof_id
        or proof.created_at <= export.created_at
        or export.channel_digest != case.receipt_digest
        or export.expires_at <= timezone.now()
        or export.purged_at is not None
    ):
        raise ValidationError("Covered export and new current authorization required")
    text_digest = fingerprint(canonical({"text": text, "simulation": True}))
    signature = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "responses": response_version,
                "actor": actor.pk,
                "session": session_version,
                "mfa": mfa_version,
                "export": str(export.pk),
                "export_digest": export.action.payload_digest,
                "coverage": binding.coverage_review_id,
                "coverage_digest": binding.coverage_digest,
                "proof": str(proof.pk),
                "text": text_digest,
                "reason": reason,
            }
        )
    )
    action = RightsAction.objects.filter(key=key).first()
    if action:
        if (
            action.request_id,
            action.actor_id,
            action.operation,
            action.expected_version,
            action.payload_digest,
        ) != (case.pk, actor.pk, "portability_draft", version, signature):
            raise ValidationError("Conflicting final response preparation key")
    else:
        try:
            with transaction.atomic():
                action = RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=version,
                    operation="portability_draft",
                    payload_digest=signature,
                    encrypted_reason=seal({"reason": reason}),
                )
        except IntegrityError as error:
            raise ValidationError("Conflicting final response preparation key") from error
    if checked_body(action.encrypted_reason) != {"reason": reason}:
        raise ValidationError("Final preparation reason changed")
    historical = copy(case)
    historical.version = export.case_version
    # Audit above precedes any decryption of the historical delivery.
    validate_export_binding(historical, person, export)
    draft = RightsPortabilityResponseDraft.objects.filter(action=action).first()
    if draft:
        expected = (
            case.pk,
            actor.pk,
            export.pk,
            binding.coverage_review_id,
            proof.pk,
            version,
            response_version,
            session_version,
            mfa_version,
            export.action.payload_digest,
            binding.coverage_digest,
            text_digest,
        )
        actual = (
            draft.request_id,
            draft.actor_id,
            draft.export_id,
            draft.coverage_review_id,
            draft.proof_id,
            draft.case_version,
            draft.response_version,
            draft.original_session_version,
            draft.original_mfa_version,
            draft.export_digest,
            draft.coverage_digest,
            draft.text_digest,
        )
        if actual != expected or draft.purged_at or draft.expires_at <= timezone.now():
            raise ValidationError("Final response draft changed or expired")
        if checked_body(draft.encrypted_response) != {"text": text, "simulation": True}:
            raise ValidationError("Final response text changed")
    else:
        draft = RightsPortabilityResponseDraft.objects.create(
            action=action,
            request=case,
            actor=actor,
            export=export,
            coverage_review_id=binding.coverage_review_id,
            proof=proof,
            case_version=version,
            response_version=response_version,
            original_session_version=session_version,
            original_mfa_version=mfa_version,
            export_digest=export.action.payload_digest,
            coverage_digest=binding.coverage_digest,
            text_digest=text_digest,
            encrypted_response=seal({"text": text, "simulation": True}),
            expires_at=min(export.expires_at, proof.expires_at),
        )
    fresh_authority(actor, case, session_version, mfa_version)
    fresh = User.objects.get(pk=actor.pk)
    if not fresh.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    if can_prepare(fresh, case, person).pk != proof.pk:
        raise ValidationError("Final response authorization changed")
    from .rights_portability_response_evidence import validate_draft

    validate_draft(draft, case, person)
    return draft
