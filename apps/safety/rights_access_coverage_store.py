"""Audited encrypted access accounting drafts; no independent approval or closure."""

from copy import copy

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .models import RightsAccessCoverage, RightsAction, RightsExport, RightsExportInformationBinding
from .rights import fingerprint
from .rights_access_coverage import compile_coverage
from .rights_access_evidence_refs import bind_references
from .rights_access_response_draft import checked_body
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .rights_information_export import validate_export_binding
from .rights_portability_export import validate_transport
from .rights_responses import complete_response_read


def required_references(declarations):
    labels = {"boundary:" + name for name in declarations["boundaries"]}
    for section, rows in declarations["sections"].items():
        for row in rows:
            for path in row["decisions"]:
                labels.add(
                    fingerprint(canonical({"section": section, "row": row["row"], "path": path}))
                )
    return labels


@transaction.atomic
@sensitive_variables()
def save(
    user,
    case_id,
    version,
    response_version,
    export_id,
    key,
    reason,
    delivered,
    declarations,
    references,
    expected_source,
    expected_delivery,
):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Motivated access coverage preparation required")
    session, mfa = user.session_version, user.mfa_version
    case, person, listing = reviewer_case(user, case_id)
    actor = User.objects.get(pk=user.pk)
    fresh_authority(actor, case, session, mfa)
    if case.assigned_to_id != actor.pk or not actor.has_perm("safety.respond_rights_request"):
        raise PermissionDenied
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != response_version
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect current access request and responses first")
    proof = can_prepare(actor, case, person)
    export = (
        RightsExport.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=export_id, action__request=case, action__actor=actor)
        .first()
    )
    binding = (
        RightsExportInformationBinding.objects.select_for_update().filter(export=export).first()
        if export
        else None
    )
    if (
        not binding
        or export.expires_at <= timezone.now()
        or export.purged_at
        or export.channel_digest != case.receipt_digest
        or proof.pk == export.proof_id
        or proof.created_at <= export.created_at
    ):
        raise ValidationError("Approved information export and new authorization required")
    payload = {
        "delivered": delivered,
        "declarations": declarations,
        "references": references,
        "source": expected_source,
        "delivery": expected_delivery,
    }
    binding_digest = fingerprint(
        canonical(
            {
                field: getattr(binding, field)
                for field in [
                    "source_digest",
                    "information_digest",
                    "policy_digest",
                    "inspection_digest",
                    "decision_digest",
                ]
            }
        )
    )
    digest = fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": version,
                "responses": response_version,
                "actor": actor.pk,
                "session": session,
                "mfa": mfa,
                "export": str(export.pk),
                "export_digest": export.action.payload_digest,
                "information": binding.review_id,
                "binding": binding_digest,
                "proof": str(proof.pk),
                "payload": payload,
                "reason": reason,
            }
        )
    )
    action, created = RightsAction.objects.get_or_create(
        key=key,
        defaults={
            "request": case,
            "actor": actor,
            "expected_version": version,
            "operation": "access_coverage",
            "payload_digest": digest,
            "encrypted_reason": seal({"reason": reason}),
        },
    )
    if (
        action.request_id,
        action.actor_id,
        action.expected_version,
        action.operation,
        action.payload_digest,
    ) != (case.pk, actor.pk, version, "access_coverage", digest) or checked_body(
        action.encrypted_reason
    ) != {"reason": reason}:
        raise ValidationError("Conflicting access coverage key")
    historical = copy(case)
    historical.version = export.case_version
    validate_export_binding(historical, person, export)
    validate_transport(export, delivered)
    source = source_copy(person, listing, case)
    accounting = compile_coverage(
        source, delivered, declarations, expected_source, expected_delivery
    )
    if (
        expected_source != binding.source_digest
        or not isinstance(references, dict)
        or set(references) != required_references(declarations)
    ):
        raise ValidationError("Every access decision needs exact source evidence")
    facts = bind_references(case, export, references)
    body = payload | {"accounting": accounting, "bound_references": facts}
    row = RightsAccessCoverage.objects.filter(action=action).first()
    if row:
        expected = (
            case.pk,
            actor.pk,
            export.pk,
            binding.review_id,
            proof.pk,
            version,
            response_version,
            session,
            mfa,
            export.action.payload_digest,
            binding_digest,
        )
        actual = (
            row.request_id,
            row.actor_id,
            row.export_id,
            row.information_review_id,
            row.proof_id,
            row.case_version,
            row.response_version,
            row.original_session_version,
            row.original_mfa_version,
            row.export_digest,
            row.binding_digest,
        )
        if actual != expected:
            raise ValidationError("Access coverage references changed")
        if (
            row.purged_at
            or row.expires_at <= timezone.now()
            or row.accounting_digest != accounting["accounting_digest"]
            or checked_body(row.encrypted_coverage) != body
        ):
            raise ValidationError("Access coverage changed or expired")
    else:
        if not created:
            raise ValidationError("Access coverage audit has no stored draft")
        row = RightsAccessCoverage.objects.create(
            action=action,
            request=case,
            actor=actor,
            export=export,
            information_review_id=binding.review_id,
            proof=proof,
            case_version=version,
            response_version=response_version,
            original_session_version=session,
            original_mfa_version=mfa,
            export_digest=export.action.payload_digest,
            binding_digest=binding_digest,
            accounting_digest=accounting["accounting_digest"],
            encrypted_coverage=seal(body),
            expires_at=min(export.expires_at, proof.expires_at),
        )
    fresh_authority(actor, case, session, mfa)
    if (
        not User.objects.get(pk=actor.pk).has_perm("safety.respond_rights_request")
        or can_prepare(actor, case, person).pk != proof.pk
    ):
        raise PermissionDenied
    return row
