"""Independent access accounting inspection/review; does not close access scope."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import User

from .crypto import seal
from .models import RightsAccessCoverage, RightsAccessCoverageReview, RightsAction
from .rights import fingerprint
from .rights_access_coverage_store import save
from .rights_access_response_draft import checked_body
from .rights_access_response_review import authorize_reviewer
from .rights_exports import canonical, reviewer_case, source_copy
from .rights_responses import complete_response_read
from .rights_verification import authorized_proof, complete_read


def context(user, case_id, version, coverage_id):
    case, person, _ = reviewer_case(user, case_id)
    actor = authorize_reviewer(user, case)
    if (
        case.kind != "access"
        or case.status != "reviewing"
        or case.version != version
        or not complete_read(actor, case)
        or not complete_response_read(actor, case)
    ):
        raise ValidationError("Inspect current access request and responses first")
    row = (
        RightsAccessCoverage.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=coverage_id, request=case)
        .first()
    )
    if row is None or row.actor_id == actor.pk:
        raise PermissionDenied("Independent access coverage reviewer required")
    if (
        row.case_version != version
        or row.response_version != case.response_version
        or row.purged_at
        or row.expires_at <= timezone.now()
        or authorized_proof(case, person, "access").pk != row.proof_id
    ):
        raise ValidationError("Current access coverage unavailable")
    return case, actor, row


def signature(case, actor, row, user, reason):
    return fingerprint(
        canonical(
            {
                "case": str(case.pk),
                "version": case.version,
                "responses": case.response_version,
                "actor": actor.pk,
                "session": user.session_version,
                "mfa": user.mfa_version,
                "coverage": row.pk,
                "preparation": row.action.payload_digest,
                "accounting": row.accounting_digest,
                "ciphertext": fingerprint(row.encrypted_coverage),
                "reason": reason,
            }
        )
    )


def audit(case, actor, version, key, operation, digest, reason):
    action, _ = RightsAction.objects.get_or_create(
        key=key,
        defaults={
            "request": case,
            "actor": actor,
            "expected_version": version,
            "operation": operation,
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
    ) != (case.pk, actor.pk, version, operation, digest) or checked_body(
        action.encrypted_reason
    ) != {"reason": reason}:
        raise ValidationError("Conflicting access coverage review key")
    return action


@transaction.atomic
@sensitive_variables()
def inspect(user, case_id, version, coverage_id, key, reason):
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 200:
        raise ValidationError("Motivated coverage inspection required")
    case, actor, row = context(user, case_id, version, coverage_id)
    action = audit(
        case,
        actor,
        version,
        key,
        "access_cover_read",
        signature(case, actor, row, user, reason),
        reason,
    )
    body = checked_body(row.encrypted_coverage)
    if not isinstance(body, dict) or set(body) != {
        "delivered",
        "declarations",
        "references",
        "source",
        "delivery",
        "accounting",
        "bound_references",
    }:
        raise ValidationError("Access coverage encrypted body changed")
    author = User.objects.get(pk=row.actor_id)
    author.session_version, author.mfa_version = (
        row.original_session_version,
        row.original_mfa_version,
    )
    author_reason = checked_body(row.action.encrypted_reason)
    if not isinstance(author_reason, dict) or set(author_reason) != {"reason"}:
        raise ValidationError("Access coverage preparation reason changed")
    replay = save(
        author,
        case.pk,
        version,
        case.response_version,
        row.export_id,
        row.action.key,
        author_reason["reason"],
        body["delivered"],
        body["declarations"],
        body["references"],
        body["source"],
        body["delivery"],
    )
    if replay.pk != row.pk:
        raise ValidationError("Access coverage preparation changed")
    authorize_reviewer(user, case)
    _, person, listing = reviewer_case(user, case_id)
    from .rights_access_reference_bodies import validated_bodies

    original = source_copy(person, listing, case)
    evidence = validated_bodies(case, row, author, original, body["bound_references"])
    authorize_reviewer(user, case)
    return row, body | {"original": original, "evidence_bodies": evidence}, action


@transaction.atomic
@sensitive_variables()
def record(user, case_id, version, coverage_id, read_id, key, reason, outcome):
    if (
        outcome not in {"approved", "rejected"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 200
    ):
        raise ValidationError("Motivated access accounting decision required")
    case, actor, row = context(user, case_id, version, coverage_id)
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=actor,
        expected_version=version,
        operation="access_cover_read",
    ).first()
    if not read:
        raise ValidationError("Inspect exact access coverage first")
    read_reason = checked_body(read.encrypted_reason)
    if not isinstance(read_reason, dict) or set(read_reason) != {"reason"}:
        raise ValidationError("Coverage inspection reason changed")
    inspect(user, case.pk, version, row.pk, read.key, read_reason["reason"])
    digest = fingerprint(
        canonical(
            {
                "read": read.pk,
                "read_digest": read.payload_digest,
                "inspection": signature(case, actor, row, user, reason),
                "outcome": outcome,
            }
        )
    )
    existing = RightsAccessCoverageReview.objects.filter(coverage=row).first()
    if existing and existing.action.key != key:
        raise ValidationError("Access coverage already reviewed")
    action = audit(case, actor, version, key, "access_cover_review", digest, reason)
    decision, _ = RightsAccessCoverageReview.objects.get_or_create(
        action=action,
        defaults={
            "coverage": row,
            "read_action": read,
            "accounting_digest": row.accounting_digest,
            "ciphertext_digest": fingerprint(row.encrypted_coverage),
            "original_session_version": user.session_version,
            "original_mfa_version": user.mfa_version,
            "outcome": outcome,
        },
    )
    actual = (
        decision.coverage_id,
        decision.read_action_id,
        decision.accounting_digest,
        decision.ciphertext_digest,
        decision.original_session_version,
        decision.original_mfa_version,
        decision.outcome,
    )
    expected = (
        row.pk,
        read.pk,
        row.accounting_digest,
        fingerprint(row.encrypted_coverage),
        user.session_version,
        user.mfa_version,
        outcome,
    )
    if actual != expected:
        raise ValidationError("Coverage decision evidence changed")
    authorize_reviewer(user, case)
    return decision
