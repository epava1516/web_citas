"""Dataset eligibility validation; this alone never authorizes portable delivery."""

from copy import deepcopy

from django.core.exceptions import ValidationError
from django.views.decorators.debug import sensitive_variables

DATASETS = (
    "profile",
    "subject_account",
    "revisions",
    "legal_acceptances",
    "favorites",
    "personal_contacts",
    "agency_relationships",
    "verifications",
    "representation_history",
)
BASES = {"unknown", "consent", "contract", "legal_obligation", "legitimate_interest", "other"}
ORIGINS = {"unknown", "provided", "observed", "inferred", "third_party", "mixed"}


def checked_assessment(value):
    """Require an explicit decision for every dataset; unknown facts stay pending."""
    if not isinstance(value, dict) or set(value) != set(DATASETS):
        raise ValidationError("Assess every portability dataset")
    fields = {
        "status",
        "basis",
        "origin",
        "automated",
        "subject_related",
        "third_party_reviewed",
        "reason",
        "evidence",
    }
    for item in value.values():
        if not isinstance(item, dict) or set(item) != fields:
            raise ValidationError("Invalid portability decision schema")
        if any(not isinstance(item[field], str) for field in ("status", "basis", "origin")):
            raise ValidationError("Invalid portability labels")
        if item["status"] not in {"pending", "eligible", "excluded", "granular"}:
            raise ValidationError("Invalid portability status")
        if item["basis"] not in BASES or item["origin"] not in ORIGINS:
            raise ValidationError("Invalid portability provenance")
        if any(
            type(item[field]) is not bool and item[field] is not None
            for field in ("automated", "subject_related", "third_party_reviewed")
        ):
            raise ValidationError("Portability facts require boolean or unknown")
        if any(
            not isinstance(item[field], str) or len(item[field]) > 2000
            for field in ("reason", "evidence")
        ):
            raise ValidationError("Invalid portability evidence text")
        if item["status"] == "pending":
            continue
        if not 20 <= len(item["reason"].strip()) or not 20 <= len(item["evidence"].strip()):
            raise ValidationError("Decided portability requires evidence and reason")
        if item["status"] == "granular" and not (
            item["origin"] == "mixed" and item["automated"] is True
        ):
            raise ValidationError(
                "Granular assessment requires documented mixed automated processing"
            )
        if item["status"] == "excluded" and not (
            item["basis"] in {"legal_obligation", "legitimate_interest", "other"}
            or item["origin"] in {"inferred", "third_party"}
            or item["automated"] is False
            or item["subject_related"] is False
        ):
            raise ValidationError("Unknown or mixed provenance requires further assessment")
        if item["status"] == "eligible" and not (
            item["basis"] in {"consent", "contract"}
            and item["origin"] in {"provided", "observed"}
            and item["automated"] is True
            and item["subject_related"] is True
            and item["third_party_reviewed"] is True
        ):
            raise ValidationError("Dataset does not meet portability delivery conditions")
    return deepcopy(value)


@sensitive_variables()
def save_assessment(
    user, case_id, case_version, key, version, reason, assessment, *, expected_source_digest=None
):
    """Store a draft only; independent approval and delivery are separate operations."""
    from datetime import timedelta

    from cryptography.fernet import InvalidToken
    from django.db import IntegrityError, transaction
    from django.utils import timezone

    from apps.core.models import User

    from .crypto import seal, unseal
    from .models import RightsAction, RightsPortabilityAssessment
    from .rights import fingerprint
    from .rights_copy_page_review import fresh_authority
    from .rights_exports import can_prepare, canonical, reviewer_case, source_copy

    if (
        type(version) is not int
        or version < 0
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Invalid portability draft version or reason")
    cleaned = checked_assessment(assessment)
    session_version, mfa_version = user.session_version, user.mfa_version
    with transaction.atomic():
        case, person, listing = reviewer_case(user, case_id)
        actor = User.objects.get(pk=user.pk)
        fresh_authority(actor, case, session_version, mfa_version)
        if case.kind != "portability" or case.status != "reviewing" or case.version != case_version:
            raise ValidationError("Current portability request required")
        proof = can_prepare(actor, case, person)
        source_digest = fingerprint(canonical(source_copy(person, listing, case)))
        if expected_source_digest is not None and expected_source_digest != source_digest:
            raise ValidationError("Portability source changed")
        signature = fingerprint(
            canonical(
                {
                    "version": case_version,
                    "assessment_version": version,
                    "reason": reason,
                    "assessment": cleaned,
                    "source": source_digest,
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
                or previous.expected_version != case_version
                or previous.operation != "portability_save"
                or previous.payload_digest != signature
            ):
                raise ValidationError("Conflicting portability draft key")
            row = RightsPortabilityAssessment.objects.filter(
                action=previous,
                proof=proof,
                source_digest=source_digest,
                purged_at__isnull=True,
                expires_at__gt=timezone.now(),
            ).first()
            if not row or not row.encrypted_assessment:
                raise ValidationError("Portability assessment unavailable")
        else:
            latest = (
                RightsPortabilityAssessment.objects.filter(request=case, actor=actor)
                .order_by("-version")
                .first()
            )
            if version != (latest.version if latest else 0):
                raise ValidationError("Portability assessment version changed")
            try:
                with transaction.atomic():
                    action = RightsAction.objects.create(
                        key=key,
                        request=case,
                        actor=actor,
                        expected_version=case_version,
                        operation="portability_save",
                        payload_digest=signature,
                        encrypted_reason=seal({"reason": reason}),
                    )
                    row = RightsPortabilityAssessment.objects.create(
                        request=case,
                        actor=actor,
                        action=action,
                        proof=proof,
                        source_digest=source_digest,
                        original_session_version=session_version,
                        original_mfa_version=mfa_version,
                        version=version + 1,
                        encrypted_assessment=seal(cleaned),
                        expires_at=min(proof.expires_at, timezone.now() + timedelta(hours=24)),
                    )
            except IntegrityError as error:
                raise ValidationError("Conflicting portability draft") from error
        try:
            stored = unseal(row.encrypted_assessment)
        except (InvalidToken, ValueError, TypeError) as error:
            raise ValidationError("Portability assessment unavailable") from error
        if (
            canonical(stored) != canonical(cleaned)
            or row.version != version + 1
            or row.original_session_version != session_version
            or row.original_mfa_version != mfa_version
        ):
            raise ValidationError("Portability assessment evidence changed")
        fresh_authority(actor, case, session_version, mfa_version)
        if (
            can_prepare(User.objects.get(pk=actor.pk), case, person).pk != proof.pk
            or fingerprint(canonical(source_copy(person, listing, case))) != source_digest
        ):
            raise ValidationError("Portability source changed")
        return row


@sensitive_variables()
def inspect_assessment(user, case_id, case_version, assessment_id, key, purpose):
    """Audited inspection of the assigned author's draft; independent review follows separately."""
    from cryptography.fernet import InvalidToken
    from django.db import IntegrityError, transaction
    from django.utils import timezone

    from apps.core.models import User

    from .crypto import seal, unseal
    from .models import RightsAction, RightsPortabilityAssessment
    from .rights import fingerprint
    from .rights_copy_page_review import fresh_authority
    from .rights_exports import can_prepare, canonical, reviewer_case, source_copy

    if not isinstance(purpose, str) or not 20 <= len(purpose.strip()) <= 200:
        raise ValidationError("Portability inspection purpose required")
    session_version, mfa_version = user.session_version, user.mfa_version
    with transaction.atomic():
        case, person, listing = reviewer_case(user, case_id)
        actor = User.objects.get(pk=user.pk)
        fresh_authority(actor, case, session_version, mfa_version)
        if case.kind != "portability" or case.status != "reviewing" or case.version != case_version:
            raise ValidationError("Current portability request required")
        proof = can_prepare(actor, case, person)
        source_digest = fingerprint(canonical(source_copy(person, listing, case)))
        row = (
            RightsPortabilityAssessment.objects.select_for_update(of=("self",))
            .select_related("action")
            .filter(
                pk=assessment_id,
                request=case,
                actor=actor,
                proof=proof,
                source_digest=source_digest,
                expires_at__gt=timezone.now(),
                purged_at__isnull=True,
            )
            .first()
        )
        if not row or not row.encrypted_assessment:
            raise ValidationError("Portability assessment unavailable")
        signature = fingerprint(
            canonical(
                {
                    "assessment": row.pk,
                    "version": row.version,
                    "case_version": case_version,
                    "source": source_digest,
                    "body": fingerprint(row.encrypted_assessment),
                    "purpose": purpose,
                    "session": session_version,
                    "mfa": mfa_version,
                }
            )
        )
        previous = RightsAction.objects.filter(key=key).first()
        if previous and (
            previous.request_id != case.pk
            or previous.actor_id != actor.pk
            or previous.expected_version != case_version
            or previous.operation != "portability_read"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting portability inspection key")
        try:
            with transaction.atomic():
                previous or RightsAction.objects.create(
                    key=key,
                    request=case,
                    actor=actor,
                    expected_version=case_version,
                    operation="portability_read",
                    payload_digest=signature,
                    encrypted_reason=seal({"purpose": purpose}),
                )
                try:
                    body = unseal(row.encrypted_assessment)
                except (InvalidToken, ValueError, TypeError, KeyError) as error:
                    raise ValidationError("Portability assessment unavailable") from error
                body = validate_assessment_evidence(row, case, proof, source_digest, body)
                fresh_authority(actor, case, session_version, mfa_version)
                return row, body
        except IntegrityError as error:
            raise ValidationError("Conflicting portability inspection key") from error


@sensitive_variables()
def validate_assessment_evidence(row, case, proof, source_digest, body):
    """Evidence only; caller must authorize and audit access before decryption."""
    from cryptography.fernet import InvalidToken
    from django.db import transaction
    from django.utils import timezone

    from .crypto import unseal
    from .rights import fingerprint
    from .rights_exports import canonical

    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Assessment validation requires atomic transaction")
    action = row.action
    if (
        case.kind != "portability"
        or row.request_id != case.pk
        or action.request_id != case.pk
        or action.actor_id != row.actor_id
        or action.operation != "portability_save"
        or action.expected_version != case.version
        or row.proof_id != proof.pk
        or row.source_digest != source_digest
        or row.expires_at <= timezone.now()
        or row.purged_at
        or not row.encrypted_assessment
    ):
        raise ValidationError("Portability assessment evidence unavailable")
    try:
        reason = unseal(action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Portability assessment evidence unavailable") from error
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Portability assessment evidence unavailable")
    cleaned = checked_assessment(body)
    signature = fingerprint(
        canonical(
            {
                "version": action.expected_version,
                "assessment_version": row.version - 1,
                "reason": reason,
                "assessment": cleaned,
                "source": source_digest,
                "proof": str(proof.pk),
                "session": row.original_session_version,
                "mfa": row.original_mfa_version,
            }
        )
    )
    if signature != action.payload_digest:
        raise ValidationError("Portability assessment evidence changed")
    return cleaned
