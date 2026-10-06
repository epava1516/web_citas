"""Motivated proposals per recipient/gap; exceptions require later independent review."""

import json

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import (
    RightsAction,
    RightsRectificationRecipientAssessment,
    RightsRectificationRecipientInventory,
)
from .rectification_recipients import execution_scope_matches, snapshot
from .rectification_review import permission
from .rights import fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read


def targets(data):
    rows = {}
    for candidate in data["candidates"]:
        token = fingerprint(json.dumps([candidate["kind"], candidate["reference"]]))
        rows[token] = candidate
    rows.update({"gap:" + value: None for value in data["pending"]})
    return rows


@sensitive_variables()
def validate_decisions(data, decisions):
    required = targets(data)
    if not isinstance(decisions, dict) or set(decisions) != set(required):
        raise ValidationError("Assess every recipient and gap / Evalúa cada destinatario y laguna")
    for token, decision in decisions.items():
        if not isinstance(decision, dict) or set(decision) != {"outcome", "reason", "evidence"}:
            raise ValidationError("Motivated evidence required / Evidencia motivada obligatoria")
        if decision["outcome"] not in {
            "pending",
            "not_disclosed",
            "impossible",
            "disproportionate",
            "communicated",
        }:
            raise ValidationError("Unsupported assessment / Evaluación no admitida")
        for field in ["reason", "evidence"]:
            value = decision[field]
            if not isinstance(value, str) or not 20 <= len(value.strip()) <= 2000:
                raise ValidationError("Explain grounds and evidence / Explica motivos y evidencia")
        if decision["outcome"] == "communicated":
            candidate = required[token]
            if (
                not candidate
                or candidate["kind"] not in {"account", "individual"}
                or not any(
                    str(notice["recipient_id"]) == candidate["reference"]
                    and notice["acknowledged_at"]
                    for notice in data["manager_notices"]
                )
            ):
                raise ValidationError(
                    "Recorded recipient receipt required / Recepción registrada del destinatario obligatoria"
                )
    return decisions


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, inventory_id, key, version, decisions):
    permission(user)
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    inventory = (
        RightsRectificationRecipientInventory.objects.select_for_update()
        .select_related("action", "execution")
        .filter(
            pk=inventory_id,
            action__request=case,
            execution__notification__review__proposal__person=person,
            execution__notification__review__proposal__account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if not inventory:
        raise ValidationError("Recipient inventory unavailable / Inventario no disponible")
    signature = fingerprint(
        json.dumps(
            {"inventory": inventory_id, "version": version, "decisions": decisions}, sort_keys=True
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "recipients_plan"
            and previous.payload_digest == signature
        ):
            return RightsRectificationRecipientAssessment.objects.get(action=previous)
        raise ValidationError("Conflicting assessment key / Clave incompatible")
    if (
        case.kind != "rectify"
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or case.version != version
        or not complete_read(user, case)
        or not complete_response_read(user, case)
        or inventory.action.actor_id != user.pk
        or inventory.action.expected_version != version
        or not execution_scope_matches(case, person, inventory.execution)
    ):
        raise ValidationError(
            "Inspect current assigned recipient inventory / Consulta el inventario asignado vigente"
        )
    proof = authorized_proof(case, person, "rectify")
    data = snapshot(person, inventory.execution, case)
    if (
        inventory.proof_id != proof.pk
        or fingerprint(json.dumps(data, sort_keys=True)) != inventory.source_digest
    ):
        raise ValidationError(
            "Recipient history changed; inspect again / Historial cambiado; consulta de nuevo"
        )
    stored = unseal(inventory.encrypted_inventory)
    if fingerprint(json.dumps(stored, sort_keys=True)) != inventory.source_digest:
        raise ValidationError("Inventory integrity mismatch / Inventario incompatible")
    if not RightsAction.objects.filter(
        request=case,
        actor=user,
        expected_version=version,
        operation="recipients_read",
        payload_digest=read_stamp(inventory, proof),
    ).exists():
        raise ValidationError(
            "Read recipient assessment fields first / Consulta primero los campos de evaluación"
        )
    validate_decisions(stored, decisions)
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="recipients_plan",
                payload_digest=signature,
                encrypted_reason=seal({"stage": "recipient_assessment_proposal"}),
            )
            result = RightsRectificationRecipientAssessment.objects.create(
                inventory=inventory,
                action=action,
                proof=proof,
                source_digest=inventory.source_digest,
                encrypted_decisions=seal(decisions),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting assessment / Evaluación incompatible") from error
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return result


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, inventory_id, version, purpose):
    import uuid

    permission(user)
    case, person, _ = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    inventory = (
        RightsRectificationRecipientInventory.objects.select_for_update()
        .select_related("action", "execution")
        .filter(
            pk=inventory_id,
            action__request=case,
            execution__notification__review__proposal__person=person,
            execution__notification__review__proposal__account_subject_id=case.account_subject_id,
        )
        .first()
    )
    if (
        not inventory
        or case.kind != "rectify"
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or case.version != version
        or not complete_read(user, case)
        or not complete_response_read(user, case)
        or inventory.action.actor_id != user.pk
        or inventory.action.expected_version != version
        or not execution_scope_matches(case, person, inventory.execution)
        or not 10 <= len(purpose.strip()) <= 200
    ):
        raise ValidationError(
            "Inspect current assigned recipient inventory / Consulta el inventario asignado vigente"
        )
    proof = authorized_proof(case, person, "rectify")
    data = snapshot(person, inventory.execution, case)
    if (
        inventory.proof_id != proof.pk
        or fingerprint(json.dumps(data, sort_keys=True)) != inventory.source_digest
    ):
        raise ValidationError(
            "Recipient history changed; inspect again / Historial cambiado; consulta de nuevo"
        )
    stored = unseal(inventory.encrypted_inventory)
    if fingerprint(json.dumps(stored, sort_keys=True)) != inventory.source_digest:
        raise ValidationError("Inventory integrity mismatch / Inventario incompatible")
    RightsAction.objects.create(
        key=uuid.uuid4(),
        request=case,
        actor=user,
        expected_version=version,
        operation="recipients_read",
        payload_digest=read_stamp(inventory, proof),
        encrypted_reason=seal({"purpose": purpose}),
    )
    return stored


def read_stamp(inventory, proof):
    return fingerprint(
        json.dumps(
            {"inventory": inventory.pk, "proof": str(proof.pk), "source": inventory.source_digest},
            sort_keys=True,
        )
    )
