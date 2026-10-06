"""Typed proposed field release and independent decision. No complete-access approval."""

import re

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .models import RightsAccessFieldDecision, RightsAccessScopeInventory, RightsAction
from .rights import fingerprint
from .rights_access_coverage_review import audit
from .rights_access_field_read import read
from .rights_access_response_draft import checked_body
from .rights_access_response_review import authorize_reviewer
from .rights_exports import canonical, reviewer_case
from .rights_responses import complete_response_read
from .rights_verification import complete_read


def released(value, outcome, redacted):
    if outcome == "included" and redacted is None:
        return value
    if outcome == "omitted" and redacted is None:
        return None
    if outcome != "redacted" or not isinstance(value, str) or not isinstance(redacted, str):
        raise ValidationError("Exact inclusion, omission or textual redaction required")
    if not redacted or redacted == value or "[redacted]" not in redacted:
        raise ValidationError("Motivated redaction must remove content")
    cursor = 0
    retained = 0
    for part in re.split(r"\[redacted\]", redacted):
        if part:
            position = value.find(part, cursor)
            if position < 0:
                raise ValidationError("Redaction cannot introduce foreign content")
            cursor = position + len(part)
            retained += len(part)
    if retained >= len(value):
        raise ValidationError("Redaction must remove original content")
    return redacted


@transaction.atomic
@sensitive_variables()
def propose(
    user,
    case_id,
    version,
    response_version,
    inventory_id,
    read_id,
    model,
    reference,
    field,
    key,
    reason,
    outcome,
    redacted=None,
):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated field decision required")
    case, _, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    inventory = (
        RightsAccessScopeInventory.objects.select_for_update()
        .filter(pk=inventory_id, request=case, actor=actor)
        .first()
    )
    reading = RightsAction.objects.filter(
        pk=read_id, request=case, actor=actor, operation="access_field_read"
    ).first()
    if inventory is None or reading is None:
        raise PermissionDenied("Own exact field inspection required")
    payload = {
        "inventory": inventory.pk,
        "read": reading.pk,
        "read_digest": reading.payload_digest,
        "source": inventory.source_digest,
        "model": model,
        "reference": reference,
        "field": field,
        "outcome": outcome,
        "redacted": redacted,
        "reason": reason,
        "version": version,
        "responses": response_version,
        "actor": actor.pk,
        "session": user.session_version,
        "mfa": user.mfa_version,
    }
    action = audit(
        case, actor, version, key, "access_field_decide", fingerprint(canonical(payload)), reason
    )
    read_reason = checked_body(reading.encrypted_reason)["reason"]
    inspected, _ = read(
        user,
        case.pk,
        version,
        response_version,
        inventory.pk,
        model,
        reference,
        field,
        reading.key,
        read_reason,
    )
    value = released(inspected["value"], outcome, redacted)
    body = {"preparation": payload, "source_field_digest": inspected["digest"], "value": value}
    row = RightsAccessFieldDecision.objects.select_for_update().filter(action=action).first()
    if row:
        if (
            row.inventory_id != inventory.pk
            or row.read_action_id != reading.pk
            or row.purged_at
            or row.expires_at <= timezone.now()
            or checked_body(row.encrypted_body) != body
        ):
            raise ValidationError("Access field decision changed or expired")
    else:
        row = RightsAccessFieldDecision.objects.create(
            action=action,
            inventory=inventory,
            read_action=reading,
            encrypted_body=seal(body),
            expires_at=inventory.expires_at,
        )
    return row, body


def context(user, case_id, version, decision_id):
    case, _, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or case.version != version
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect current access case and responses first")
    row = (
        RightsAccessFieldDecision.objects.select_for_update(of=("self",))
        .select_related("action", "inventory", "read_action")
        .filter(pk=decision_id, inventory__request=case)
        .first()
    )
    if row is None or row.action.actor_id == actor.pk:
        raise PermissionDenied("Independent field decision reviewer required")
    if row.purged_at or row.expires_at <= timezone.now():
        raise ValidationError("Field decision expired")
    return case, actor, row


def review_digest(case, user, row, reason):
    return fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "responses": case.response_version,
                "actor": user.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "decision": row.pk,
                "preparation": row.action.payload_digest,
                "ciphertext": fingerprint(row.encrypted_body),
                "reason": reason,
            }
        )
    )


@transaction.atomic
@sensitive_variables()
def inspect_decision(user, case_id, version, decision_id, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated independent field inspection required")
    case, actor, row = context(user, case_id, version, decision_id)
    action = audit(
        case,
        actor,
        version,
        key,
        "access_decision_read",
        review_digest(case, user, row, reason),
        reason,
    )
    body = checked_body(row.encrypted_body)
    data = body["preparation"]
    author = User.objects.get(pk=row.action.actor_id)
    # Reproduce original preparation with its original authority epochs; current authority
    # validation rejects revocations rather than silently adopting newer epochs.
    author.session_version = data["session"]
    author.mfa_version = data["mfa"]
    replay, expected = propose(
        author,
        case.pk,
        data["version"],
        data["responses"],
        row.inventory_id,
        row.read_action_id,
        data["model"],
        data["reference"],
        data["field"],
        row.action.key,
        data["reason"],
        data["outcome"],
        data["redacted"],
    )
    if replay.pk != row.pk or expected != body:
        raise ValidationError("Field decision evidence changed")
    original, _ = read(
        author,
        case.pk,
        data["version"],
        data["responses"],
        row.inventory_id,
        data["model"],
        data["reference"],
        data["field"],
        row.read_action.key,
        checked_body(row.read_action.encrypted_reason)["reason"],
    )
    authorize_reviewer(user, case)
    return row, body | {"original": original["value"]}, action


@transaction.atomic
@sensitive_variables()
def review(user, case_id, version, decision_id, read_id, key, reason, outcome):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated independent field review required")
    if outcome not in {"approved", "rejected"}:
        raise ValidationError("Independent decision required")
    case, actor, row = context(user, case_id, version, decision_id)
    reading = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=actor,
        expected_version=version,
        operation="access_decision_read",
    ).first()
    if reading is None:
        raise ValidationError("Inspect exact field decision before review")
    payload = {
        "inspection": reading.pk,
        "read_digest": reading.payload_digest,
        "current": review_digest(case, user, row, reason),
        "outcome": outcome,
    }
    action = audit(
        case, actor, version, key, "access_field_review", fingerprint(canonical(payload)), reason
    )
    read_reason = checked_body(reading.encrypted_reason)["reason"]
    inspect_decision(user, case.pk, version, row.pk, reading.key, read_reason)
    if row.review_action_id:
        if (
            row.review_action_id != action.pk
            or row.outcome != outcome
            or row.review_read_action_id != reading.pk
            or row.reviewer_session_version != user.session_version
            or row.reviewer_mfa_version != user.mfa_version
        ):
            raise ValidationError("Field decision already reviewed")
    else:
        row.review_action = action
        row.outcome = outcome
        row.review_read_action = reading
        row.reviewer_session_version = user.session_version
        row.reviewer_mfa_version = user.mfa_version
        row.save(
            update_fields=[
                "review_action",
                "outcome",
                "review_read_action",
                "reviewer_session_version",
                "reviewer_mfa_version",
            ]
        )
    return row


@transaction.atomic
@sensitive_variables()
def consume(user, case_id, version, response_version, decision_id, key, reason):
    """Materialize one currently approved field decision; caller must build full coverage."""
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated approved field consumption required")
    case, _, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.assigned_to_id != actor.pk
        or case.kind != "access"
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != response_version
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Consume own current access decision only")
    row = (
        RightsAccessFieldDecision.objects.select_for_update(of=("self",))
        .select_related("action", "review_action", "inventory")
        .filter(pk=decision_id, inventory__request=case, action__actor=actor, outcome="approved")
        .first()
    )
    if row is None or not row.review_action_id or not row.review_read_action_id:
        raise ValidationError("Independent approved field decision required")
    payload = {
        "decision": row.pk,
        "preparation": row.action.payload_digest,
        "review": row.review_action.payload_digest,
        "source": row.inventory.source_digest,
        "ciphertext": fingerprint(row.encrypted_body),
        "case": str(case.pk),
        "version": version,
        "responses": response_version,
        "actor": actor.pk,
        "session": user.session_version,
        "mfa": user.mfa_version,
        "reason": reason,
    }
    action = audit(
        case, actor, version, key, "access_field_use", fingerprint(canonical(payload)), reason
    )
    reviewer = User.objects.get(pk=row.review_action.actor_id)
    reviewer.session_version = row.reviewer_session_version
    reviewer.mfa_version = row.reviewer_mfa_version
    review_reason = checked_body(row.review_action.encrypted_reason)["reason"]
    review(
        reviewer,
        case.pk,
        version,
        row.pk,
        row.review_read_action_id,
        row.review_action.key,
        review_reason,
        "approved",
    )
    body = checked_body(row.encrypted_body)
    authorize_reviewer(user, case)
    return row, body, action
