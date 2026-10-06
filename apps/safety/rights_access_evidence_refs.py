"""Scoped metadata bindings for access accounting; no content access or approval."""

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import RightsAction
from .rights import fingerprint
from .rights_exports import canonical

ALLOWED = {"copy_page_save", "copy_info_review"}


def bind_references(case, export, references):
    """Caller holds canonical authorization locks; references are not approval proof.

    Historical page/info validators must additionally validate each exact stored
    body, actor epochs, proof, scope and decision before independent approval.
    """
    if not transaction.get_connection().in_atomic_block:
        raise RuntimeError("Evidence bindings require enclosing transaction")
    if export.action.request_id != case.pk or case.kind != "access":
        raise ValidationError("Access export in the same request required")
    if not isinstance(references, dict) or not references:
        raise ValidationError("Explicit access evidence references required")
    result = {}
    for label, reference in references.items():
        if (
            not isinstance(label, str)
            or not 1 <= len(label) <= 500
            or not isinstance(reference, dict)
            or set(reference) != {"action", "digest"}
            or type(reference["action"]) is not int
            or reference["action"] < 1
        ):
            raise ValidationError("Invalid access evidence reference")
        action = (
            RightsAction.objects.select_for_update()
            .filter(
                pk=reference["action"],
                request=case,
                expected_version=export.action.expected_version,
                operation__in=ALLOWED,
            )
            .first()
        )
        if action is None:
            raise ValidationError("Evidence must belong to the exact export preparation")
        snapshot = {
            "action": action.pk,
            "request": str(action.request_id),
            "actor": action.actor_id,
            "version": action.expected_version,
            "operation": action.operation,
            "payload": action.payload_digest,
            "reason_ciphertext": fingerprint(action.encrypted_reason),
        }
        digest = fingerprint(canonical(snapshot))
        if reference["digest"] != digest:
            raise ValidationError("Access evidence reference changed")
        result[label] = snapshot | {"digest": digest}
    return result
