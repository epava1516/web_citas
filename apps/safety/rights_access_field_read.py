"""Audited inspection of explicitly supported subject fields; never a release approval."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .models import RightsAccessScopeInventory
from .rights import fingerprint
from .rights_access_coverage_review import audit
from .rights_access_response_draft import checked_body
from .rights_access_response_review import authorize_reviewer
from .rights_access_scope_inventory import normalized, source
from .rights_access_scope_store import inspect
from .rights_exports import can_prepare, canonical, reviewer_case
from .rights_responses import complete_response_read

# Explicitly reviewed scalar fields. No credentials, arbitrary JSON/ciphertext, foreign IDs
# or generic model traversal; unsupported fields need a typed adapter before inspection.
FIELDS = {
    "core.User": frozenset(
        {
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "last_login",
            "date_joined",
            "is_active",
            "email_verified_at",
            "account_erased_at",
        }
    ),
    "listings.Revision": frozenset(
        {
            "title",
            "description",
            "content_language",
            "description_alternative",
            "profile_type",
            "spoken_languages",
            "days",
            "time_slot",
            "reception",
            "travel",
            "phone",
            "whatsapp",
            "telegram",
            "contact_exposure_accepted",
            "created_at",
            "updated_at",
        }
    ),
    "listings.Rate": frozenset({"concept", "mode", "amount", "currency"}),
}


@transaction.atomic
@sensitive_variables()
def read(
    user, case_id, version, response_version, inventory_id, model, reference, field, key, reason
):
    if field not in FIELDS.get(model, ()):
        raise ValidationError("Unsupported access field inspection")
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated field inspection required")
    case, person, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or case.assigned_to_id != actor.pk
        or case.version != version
        or case.response_version != response_version
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect assigned current access request and responses first")
    row = (
        RightsAccessScopeInventory.objects.select_for_update()
        .select_related("action")
        .filter(pk=inventory_id, request=case, actor=actor)
        .first()
    )
    if row is None:
        raise PermissionDenied("Own scoped access inventory required")
    proof = can_prepare(actor, case, person)
    digest = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "responses": response_version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "proof": str(proof.pk),
                "inventory": row.pk,
                "source": row.source_digest,
                "model": model,
                "reference": reference,
                "field": field,
                "reason": reason,
            }
        )
    )
    action = audit(case, actor, version, key, "access_field_read", digest, reason)
    original_reason = checked_body(row.action.encrypted_reason)["reason"]
    _, manifest = inspect(user, case.pk, version, response_version, row.action.key, original_reason)
    candidates = [
        record
        for entry in manifest["entries"]
        if entry["model"] == model
        for record in entry["records"]
        if record["reference"] == reference
    ]
    if len(candidates) != 1 or field not in candidates[0]["fields"]:
        raise ValidationError("Exact inventoried subject field required")
    values = []

    @sensitive_variables()
    def capture(label, row_reference, body):
        if label == model and row_reference == reference:
            values.append(normalized(body[field]))

    current = source(case, person, value_sink=capture)
    if (
        current != manifest
        or len(values) != 1
        or fingerprint(canonical(values[0])) != candidates[0]["fields"][field]["digest"]
    ):
        raise ValidationError("Access field source changed")
    authorize_reviewer(user, case)
    if can_prepare(actor, case, person).pk != proof.pk:
        raise ValidationError("Access field authority changed")
    return {
        "inventory": row.pk,
        "source": row.source_digest,
        "model": model,
        "reference": reference,
        "field": field,
        "value": values[0],
        "digest": candidates[0]["fields"][field]["digest"],
    }, action
