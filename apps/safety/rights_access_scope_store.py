"""Audited encrypted access field census; no data release, decisions or closure."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .models import RightsAccessScopeInventory
from .rights import fingerprint
from .rights_access_coverage_review import audit
from .rights_access_response_draft import checked_body
from .rights_access_response_review import authorize_reviewer
from .rights_access_scope_inventory import source
from .rights_exports import can_prepare, canonical, reviewer_case
from .rights_responses import complete_response_read


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, version, response_version, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated access scope inspection required")
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
                "reason": reason,
            }
        )
    )
    action = audit(case, actor, version, key, "access_scope_read", digest, reason)
    manifest = source(case, person)
    row = RightsAccessScopeInventory.objects.filter(action=action).first()
    if row:
        expected = (
            case.pk,
            actor.pk,
            proof.pk,
            version,
            response_version,
            user.session_version,
            user.mfa_version,
            manifest["digest"],
        )
        actual = (
            row.request_id,
            row.actor_id,
            row.proof_id,
            row.case_version,
            row.response_version,
            row.original_session_version,
            row.original_mfa_version,
            row.source_digest,
        )
        if (
            actual != expected
            or row.purged_at
            or row.expires_at <= timezone.now()
            or checked_body(row.encrypted_inventory) != manifest
        ):
            raise ValidationError("Access scope inventory changed or expired")
    else:
        row = RightsAccessScopeInventory.objects.create(
            action=action,
            request=case,
            actor=actor,
            proof=proof,
            case_version=version,
            response_version=response_version,
            original_session_version=user.session_version,
            original_mfa_version=user.mfa_version,
            source_digest=manifest["digest"],
            encrypted_inventory=seal_inventory(manifest),
            expires_at=min(proof.expires_at, timezone.now() + timedelta(hours=24)),
        )
    authorize_reviewer(user, case)
    if can_prepare(actor, case, person).pk != proof.pk:
        raise ValidationError("Access scope authorization changed")
    return row, manifest


def seal_inventory(manifest):
    from .crypto import seal

    return seal(manifest)
