"""Materialize approved field decisions against one current subject inventory."""

from uuid import uuid5

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .models import RightsAccessScopeInventory
from .rights import fingerprint
from .rights_access_coverage_review import audit
from .rights_access_field_decision import consume
from .rights_access_response_draft import checked_body
from .rights_access_response_review import authorize_reviewer
from .rights_access_scope_store import inspect
from .rights_exports import canonical, reviewer_case


@transaction.atomic
@sensitive_variables()
def prepare(user, case_id, version, response_version, inventory_id, decision_ids, key, reason):
    if (
        not isinstance(decision_ids, list)
        or not decision_ids
        or any(type(item) is not int or item < 1 for item in decision_ids)
        or len(set(decision_ids)) != len(decision_ids)
    ):
        raise ValidationError("Distinct approved field decision IDs required")
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated supplemental copy preparation required")
    case, _, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or case.assigned_to_id != actor.pk
        or case.version != version
        or case.response_version != response_version
    ):
        raise ValidationError("Prepare assigned current access supplement only")
    inventory = (
        RightsAccessScopeInventory.objects.select_for_update()
        .select_related("action")
        .filter(pk=inventory_id, request=case, actor=actor)
        .first()
    )
    if inventory is None:
        raise PermissionDenied("Own exact subject inventory required")
    payload = {
        "case": str(case.pk),
        "version": version,
        "responses": response_version,
        "actor": actor.pk,
        "session": user.session_version,
        "mfa": user.mfa_version,
        "inventory": inventory.pk,
        "source": inventory.source_digest,
        "decisions": sorted(decision_ids),
        "reason": reason,
    }
    action = audit(
        case, actor, version, key, "access_supplement", fingerprint(canonical(payload)), reason
    )
    original_reason = checked_body(inventory.action.encrypted_reason)["reason"]
    _, manifest = inspect(
        user, case.pk, version, response_version, inventory.action.key, original_reason
    )
    required = {
        (entry["model"], record["reference"], name): facts["digest"]
        for entry in manifest["entries"]
        for record in entry["records"]
        for name, facts in record["fields"].items()
    }
    selected = {}
    evidence = []
    expires_at = inventory.expires_at
    for decision_id in sorted(decision_ids):
        row, body, consumption = consume(
            user,
            case.pk,
            version,
            response_version,
            decision_id,
            uuid5(key, f"access-supplement:{decision_id}"),
            "Materialize approved field into this access supplement",
        )
        data = body["preparation"]
        target = data["model"], data["reference"], data["field"]
        if (
            row.inventory_id != inventory.pk
            or data["source"] != manifest["digest"]
            or target not in required
            or body["source_field_digest"] != required[target]
        ):
            raise ValidationError("Supplement field belongs to another inventory or source")
        if target in selected:
            raise ValidationError("Conflicting decisions for the same access field")
        item = {
            "model": target[0],
            "reference": target[1],
            "field": target[2],
            "outcome": data["outcome"],
            "reason": data["reason"],
        }
        if data["outcome"] != "omitted":
            item["value"] = body["value"]
        selected[target] = item
        evidence.append(
            {
                "decision": row.pk,
                "preparation": row.action.payload_digest,
                "review": row.review_action_id,
                "consumption": consumption.pk,
                "source_field_digest": body["source_field_digest"],
            }
        )
        expires_at = min(expires_at, row.expires_at)
    remaining = sorted(set(required) - set(selected))
    result = {
        "schema": "access-supplement-v1",
        "inventory": inventory.pk,
        "source": manifest["digest"],
        "fields": [selected[target] for target in sorted(selected)],
        "evidence": evidence,
        "pending_fields": [
            {"model": model, "reference": reference, "field": field}
            for model, reference, field in remaining
        ],
        "pending_scopes": manifest["pending"],
        "partial": bool(remaining or manifest["pending"]),
        "expires_at": expires_at.isoformat(),
    }
    result["digest"] = fingerprint(canonical(result))
    authorize_reviewer(user, case)
    return result, action
