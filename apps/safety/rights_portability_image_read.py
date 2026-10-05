"""Independent audited binary reads bound to the exact selected image and draft."""

import hashlib
from uuid import uuid5

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import RightsAction, RightsPortabilityImageRead
from .rights import fingerprint
from .rights_exports import canonical, image_content, reviewer_case, source_copy
from .rights_portability_review import authorize
from .rights_portability_selection_review import record, validate_evidence
from .rights_verification import authorized_proof


def signature(row, case, purpose):
    return fingerprint(
        canonical(
            {
                "selection": row.selection_id,
                "read": row.selection_read_id,
                "photo": str(row.photo_id),
                "content": row.content_digest,
                "version": case.version,
                "source": row.source_digest,
                "digest": row.selection_digest,
                "proof": str(row.proof_id),
                "session": row.original_session_version,
                "mfa": row.original_mfa_version,
                "purpose": purpose,
            }
        )
    )


@sensitive_variables()
def validate_read(evidence, selection, case, proof, decision, actor_id):
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Binary image evidence requires enclosing transaction")
    try:
        purpose = unseal(evidence.action.encrypted_reason)["reason"]
    except (InvalidToken, ValueError, TypeError, KeyError) as error:
        raise ValidationError("Binary image evidence unavailable") from error
    if (
        not isinstance(purpose, str)
        or not 20 <= len(purpose.strip()) <= 200
        or evidence.selection_id != selection.pk
        or evidence.proof_id != proof.pk
        or evidence.source_digest != selection.source_digest
        or evidence.selection_digest != selection.selection_digest
        or str(evidence.photo_id) != decision["photo"]
        or evidence.content_digest != decision["content_digest"]
        or evidence.action.actor_id != actor_id
        or actor_id == selection.actor_id
        or evidence.action.request_id != case.pk
        or evidence.action.expected_version != case.version
        or evidence.action.operation != "port_image_inspect"
        or evidence.action.payload_digest != signature(evidence, case, purpose)
        or evidence.selection_read.action.actor_id != actor_id
    ):
        raise ValidationError("Binary image evidence changed")
    validate_evidence(evidence.selection_read, selection, case, proof)


@sensitive_variables()
def required_reads(selection, case, proof, decisions, actor_id, *, ids=None):
    if not decisions:
        if ids:
            raise ValidationError("Unexpected binary image reads")
        return []
    reads = RightsPortabilityImageRead.objects.select_related(
        "action", "selection_read__action"
    ).filter(
        selection=selection,
        action__actor_id=actor_id,
        proof=proof,
        action__expected_version=case.version,
        selection_digest=selection.selection_digest,
    )
    if ids is not None:
        if ids == []:
            raise ValidationError("Independent binary image inspection required")
        if (
            not isinstance(ids, list)
            or len(ids) != len(decisions)
            or any(type(pk) is not int for pk in ids)
        ):
            raise ValidationError("Exact binary image reads required")
        reads = reads.filter(pk__in=ids)
    chosen = []
    for decision in decisions:
        row = (
            reads.filter(photo_id=decision["photo"], content_digest=decision["content_digest"])
            .order_by("-pk")
            .first()
        )
        if row is None:
            raise ValidationError("Independent binary image inspection required")
        validate_read(row, selection, case, proof, decision, actor_id)
        chosen.append(row.pk)
    if ids is not None and (len(set(ids)) != len(ids) or set(chosen) != set(ids)):
        raise ValidationError("Binary image approval reads changed")
    return chosen


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, version, selection_id, photo_id, key, purpose):
    if not isinstance(purpose, str) or not 20 <= len(purpose.strip()) <= 200:
        raise ValidationError("Binary image inspection purpose required")
    case, person, listing = reviewer_case(user, case_id)
    actor = authorize(user, case)
    # An independently audited draft read precedes decrypting its binary declarations.
    read, projected = record(
        user, case_id, version, selection_id, uuid5(key, "binary-selection-inspection"), purpose
    )
    selection = read.selection
    decisions = projected.get("images", [])
    decision = next((item for item in decisions if item["photo"] == str(photo_id)), None)
    if not decision:
        raise ValidationError("Selected binary image required")
    row = RightsPortabilityImageRead(
        selection=selection,
        selection_read=read,
        photo_id=photo_id,
        proof=selection.proof,
        source_digest=selection.source_digest,
        selection_digest=selection.selection_digest,
        content_digest=decision["content_digest"],
        original_session_version=user.session_version,
        original_mfa_version=user.mfa_version,
    )
    digest = signature(row, case, purpose)
    previous = RightsAction.objects.filter(key=key).first()
    if previous and (
        previous.request_id != case.pk
        or previous.actor_id != actor.pk
        or previous.operation != "port_image_inspect"
        or previous.expected_version != version
        or previous.payload_digest != digest
    ):
        raise ValidationError("Conflicting binary image inspection key")
    row.action = previous or RightsAction.objects.create(
        key=key,
        request=case,
        actor=actor,
        expected_version=version,
        operation="port_image_inspect",
        payload_digest=digest,
        encrypted_reason=seal({"reason": purpose}),
    )
    photo, content = image_content(person, photo_id)
    if hashlib.sha256(content).hexdigest() != decision["content_digest"]:
        raise ValidationError("Selected binary image content changed")
    if previous:
        stored = (
            RightsPortabilityImageRead.objects.select_related("action", "selection_read__action")
            .filter(action=previous)
            .first()
        )
        if stored is None:
            raise ValidationError("Binary image inspection unavailable")
        row = stored
    else:
        row.save()
    validate_read(row, selection, case, selection.proof, decision, actor.pk)
    authorize(user, case)
    if (
        authorized_proof(case, person, case.kind).pk != selection.proof_id
        or fingerprint(canonical(source_copy(person, listing, case))) != selection.source_digest
    ):
        raise ValidationError("Binary image authority or source changed")
    return row, content
