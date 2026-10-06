"""Shared exact-response review and atomic issuance; policies retain each right's semantics."""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .erasure_inventory import canonical
from .rights import fingerprint
from .rights_access_response_draft import checked_body


@dataclass(frozen=True)
class Policy:
    kinds: tuple
    prefix: str
    schema: str
    execution_model: object
    snapshot: object
    projection: object
    review_permission: str = ""


def _actor(policy, user, case, *, assigned):
    from django.core.exceptions import PermissionDenied

    from apps.core.models import User

    from .rights_copy_page_review import fresh_authority

    fresh_authority(user, case, user.session_version, user.mfa_version)
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or not fresh.has_perm("safety.respond_rights_request")
        or (
            policy.review_permission
            and case.assigned_to_id != fresh.pk
            and not fresh.has_perm(policy.review_permission)
        )
        or (assigned and case.assigned_to_id != fresh.pk)
    ):
        raise PermissionDenied


def _context(policy, user, case_id, version, responses, *, assigned):
    from .rights_responses import complete_response_read
    from .rights_scope import locked_case
    from .rights_verification import complete_read

    case, person, listing = locked_case(case_id, lock_listing=True, allow_erased_account=True)
    _actor(policy, user, case, assigned=assigned)
    if (
        case.kind not in policy.kinds
        or case.status != "reviewing"
        or case.version != version
        or case.response_version != responses
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError("Inspect current rights case and outgoing responses")
    return case, person, listing


def _digest(body):
    return fingerprint(canonical(body))


def _record(user, case, key, operation, body):
    from .crypto import seal
    from .models import RightsAction

    signature = _digest(body)
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id,
            previous.actor_id,
            previous.operation,
            previous.payload_digest,
        ) != (case.pk, user.pk, operation, signature):
            raise ValidationError("Conflicting final rights action key")
        if _digest(checked_body(previous.encrypted_reason)) != signature:
            raise ValidationError("Final rights action integrity changed")
        return previous
    return RightsAction.objects.create(
        key=key,
        request=case,
        actor=user,
        operation=operation,
        expected_version=case.version,
        payload_digest=signature,
        encrypted_reason=seal(body),
    )


@sensitive_variables()
def _material(policy, case, person, listing, execution_id):
    from .rights_communications import final_material

    material = policy.snapshot(case, person, listing, execution_id)
    material["communications"] = final_material(case, person, listing, execution_id)
    return material


@transaction.atomic
@sensitive_variables()
def prepare(policy, user, case_id, version, responses, execution_id, key, reason, text, confirmed):
    from .rights_response_text import checked_response_text

    checked_response_text(reason, text, confirmed)
    case, person, listing = _context(policy, user, case_id, version, responses, assigned=True)
    material = _material(policy, case, person, listing, execution_id)
    latest = (
        policy.execution_model.objects.filter(action__request=case).order_by("-action_id").first()
    )
    if not latest or str(latest.pk) != str(execution_id):
        raise ValidationError("Latest own-scope rights execution required")
    return _record(
        user,
        case,
        key,
        policy.prefix + "_final_draft",
        {
            "schema": policy.schema,
            "version": version,
            "responses": responses,
            "channel": case.receipt_digest,
            "session": user.session_version,
            "mfa": user.mfa_version,
            "material": material,
            "reason": reason,
            "text": text,
        },
    )


def _draft(policy, user, case_id, version, responses, draft_id, *, assigned):
    from datetime import timedelta

    from .models import RightsAction
    from .rights_copy_page_review import fresh_authority

    case, person, listing = _context(policy, user, case_id, version, responses, assigned=assigned)
    draft = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(
            pk=draft_id,
            request=case,
            operation=policy.prefix + "_final_draft",
            expected_version=version,
        )
        .first()
    )
    latest = (
        RightsAction.objects.filter(
            request=case, operation=policy.prefix + "_final_draft", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if not draft or not latest or latest.pk != draft.pk:
        raise ValidationError("Latest final rights draft required")
    body = checked_body(draft.encrypted_reason)
    _actor(policy, draft.actor, case, assigned=True)
    fresh_authority(draft.actor, case, body["session"], body["mfa"])
    latest_execution = (
        policy.execution_model.objects.filter(action__request=case).order_by("-action_id").first()
    )
    if (
        _digest(body) != draft.payload_digest
        or body["version"] != version
        or body["responses"] != responses
        or body["channel"] != case.receipt_digest
        or timezone.now() >= draft.created_at + timedelta(hours=24)
        or not latest_execution
        or str(latest_execution.pk) != str(body["material"]["execution"])
        or canonical(_material(policy, case, person, listing, body["material"]["execution"]))
        != canonical(body["material"])
    ):
        raise ValidationError("Final rights draft or execution changed or expired")
    return case, draft, body


@transaction.atomic
@sensitive_variables()
def inspect(policy, user, case_id, version, responses, draft_id, purpose):
    import uuid

    from django.core.exceptions import PermissionDenied

    from .models import RightsAction

    case, _, _ = _context(policy, user, case_id, version, responses, assigned=False)
    draft = RightsAction.objects.filter(
        pk=draft_id,
        request=case,
        operation=policy.prefix + "_final_draft",
        expected_version=version,
    ).first()
    if not draft:
        raise ValidationError("Current final rights draft required")
    if draft.actor_id == user.pk:
        raise PermissionDenied("Independent reviewer required")
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited access purpose required")
    read = _record(
        user,
        case,
        uuid.uuid4(),
        policy.prefix + "_final_read",
        {
            "draft": draft.pk,
            "digest": draft.payload_digest,
            "responses": responses,
            "channel": case.receipt_digest,
            "purpose": purpose,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    _, _, body = _draft(policy, user, case_id, version, responses, draft_id, assigned=False)
    return read, body


@transaction.atomic
@sensitive_variables()
def review(policy, user, case_id, version, responses, draft_id, read_id, key, outcome, reason):
    from django.core.exceptions import PermissionDenied

    from .models import RightsAction
    from .rights_copy_page_review import fresh_authority

    case, draft, _ = _draft(policy, user, case_id, version, responses, draft_id, assigned=False)
    if user.pk == draft.actor_id:
        raise PermissionDenied("Independent reviewer required")
    read = RightsAction.objects.filter(
        pk=read_id,
        request=case,
        actor=user,
        operation=policy.prefix + "_final_read",
        expected_version=version,
    ).first()
    if (
        not read
        or outcome not in {"approved", "rejected"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Independent audited motivated review required")
    inspected = checked_body(read.encrypted_reason)
    if (
        _digest(inspected) != read.payload_digest
        or inspected["draft"] != draft.pk
        or inspected["digest"] != draft.payload_digest
        or inspected["responses"] != responses
        or inspected["channel"] != case.receipt_digest
    ):
        raise ValidationError("Exact current final rights read required")
    fresh_authority(user, case, inspected["session"], inspected["mfa"])
    return _record(
        user,
        case,
        key,
        policy.prefix + "_final_review",
        {
            "draft": draft.pk,
            "digest": draft.payload_digest,
            "read": read.pk,
            "outcome": outcome,
            "reason": reason,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )


@transaction.atomic
@sensitive_variables()
def issue(policy, user, case_id, version, responses, review_id, key):
    from .crypto import seal, unseal
    from .models import RightsAction, RightsNotice, RightsResponse
    from .rights_copy_page_review import fresh_authority
    from .rights_scope import locked_case

    case, _, _ = locked_case(case_id, lock_listing=True, allow_erased_account=True)
    _actor(policy, user, case, assigned=True)
    previous = RightsResponse.objects.filter(key=key).first()
    if previous:
        issuance = RightsAction.objects.filter(
            key=key, request=case, actor=user, operation=policy.prefix + "_final_issue"
        ).first()
        if not issuance or previous.request_id != case.pk or previous.actor_id != user.pk:
            raise ValidationError("Conflicting final rights response key")
        issued = checked_body(issuance.encrypted_reason)
        if (
            _digest(issued) != issuance.payload_digest
            or issued.get("review") != review_id
            or issued.get("version") != version
            or issued.get("responses") != responses
            or issued.get("channel") != case.receipt_digest
            or _digest(checked_body(previous.encrypted_response)) != issued.get("response_digest")
            or previous.payload_digest != issued.get("draft_digest")
            or previous.case_version != version
            or previous.response_version != responses + 1
            or previous.kind != issued.get("kind")
        ):
            raise ValidationError("Final rights replay binding changed")
        draft = (
            RightsAction.objects.select_related("actor")
            .filter(
                pk=issued.get("draft"),
                request=case,
                actor=user,
                operation=policy.prefix + "_final_draft",
            )
            .first()
        )
        approval = (
            RightsAction.objects.select_related("actor")
            .filter(pk=review_id, request=case, operation=policy.prefix + "_final_review")
            .first()
        )
        if not draft or not approval or approval.actor_id == user.pk:
            raise ValidationError("Final rights replay evidence unavailable")
        body, decision = (
            checked_body(draft.encrypted_reason),
            checked_body(approval.encrypted_reason),
        )
        if (
            _digest(body) != draft.payload_digest
            or draft.payload_digest != issued.get("draft_digest")
            or _digest(decision) != approval.payload_digest
            or approval.payload_digest != issued.get("review_digest")
            or decision.get("outcome") != "approved"
            or decision.get("draft") != draft.pk
            or decision.get("digest") != draft.payload_digest
        ):
            raise ValidationError("Final rights replay approval changed")
        fresh_authority(user, case, body["session"], body["mfa"])
        fresh_authority(approval.actor, case, decision["session"], decision["mfa"])
        _actor(policy, approval.actor, case, assigned=False)
        return previous
    approval = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(
            pk=review_id,
            request=case,
            operation=policy.prefix + "_final_review",
            expected_version=version,
        )
        .first()
    )
    latest = (
        RightsAction.objects.filter(
            request=case, operation=policy.prefix + "_final_review", expected_version=version
        )
        .order_by("-pk")
        .first()
    )
    if not approval or not latest or latest.pk != approval.pk:
        raise ValidationError("Latest independent final rights review required")
    decision = checked_body(approval.encrypted_reason)
    if _digest(decision) != approval.payload_digest or decision.get("outcome") != "approved":
        raise ValidationError("Intact approved final rights response required")
    case, draft, body = _draft(
        policy, user, case_id, version, responses, decision["draft"], assigned=True
    )
    if (
        draft.actor_id != user.pk
        or approval.actor_id == user.pk
        or decision["digest"] != draft.payload_digest
    ):
        raise ValidationError("Independent exact final rights approval required")
    read = RightsAction.objects.filter(
        pk=decision["read"],
        request=case,
        actor=approval.actor,
        operation=policy.prefix + "_final_read",
        expected_version=version,
    ).first()
    if not read:
        raise ValidationError("Final rights audit unavailable")
    inspected = checked_body(read.encrypted_reason)
    if (
        _digest(inspected) != read.payload_digest
        or inspected["draft"] != draft.pk
        or inspected["digest"] != draft.payload_digest
        or inspected["responses"] != responses
        or inspected["channel"] != case.receipt_digest
    ):
        raise ValidationError("Final rights audit changed")
    fresh_authority(approval.actor, case, inspected["session"], inspected["mfa"])
    fresh_authority(approval.actor, case, decision["session"], decision["mfa"])
    _actor(policy, approval.actor, case, assigned=False)
    material = body["material"]
    pending, response_body = policy.projection(material, body["text"])
    kind = case.kind + ("_partial" if pending else "_complete")
    _record(
        user,
        case,
        key,
        policy.prefix + "_final_issue",
        {
            "review": review_id,
            "version": version,
            "responses": responses,
            "draft": draft.pk,
            "draft_digest": draft.payload_digest,
            "review_digest": approval.payload_digest,
            "response_digest": _digest(response_body),
            "channel": case.receipt_digest,
            "kind": kind,
        },
    )
    response = RightsResponse.objects.create(
        key=key,
        request=case,
        actor=user,
        case_version=version,
        response_version=responses + 1,
        kind=kind,
        payload_digest=draft.payload_digest,
        encrypted_reason=seal({"reason": body["reason"]}),
        encrypted_response=seal(response_body),
    )
    draft.final_response = response
    draft.save(update_fields=["final_response"])
    contact = unseal(case.encrypted_payload).get("email")
    if contact:
        RightsNotice.objects.create(
            response=response,
            encrypted_payload=seal(
                {
                    "recipient": contact,
                    "subject": "Respuesta privada / Private response",
                    "body": "Hay una respuesta disponible en tu acuse privado. A response is available in your private receipt.",
                }
            ),
        )
    case.version += 1
    case.response_version += 1
    case.scope_status = "unverified"
    if not pending:
        case.status = "resolved"
    case.save(update_fields=["version", "response_version", "scope_status", "status"])
    return response


def purge_unissued_drafts():
    """Clear expired unused bodies, retaining metadata and issued-response evidence."""
    from datetime import timedelta

    from .models import RightsAction, RightsRequest, RightsResponse

    now = timezone.now()
    cutoff = now - timedelta(hours=24)
    candidates = list(
        RightsAction.objects.filter(
            operation__in=["erase_final_draft", "process_final_draft", "rectify_final_draft"],
            created_at__lte=cutoff,
            purged_at__isnull=True,
            final_response__isnull=True,
        )
        .exclude(encrypted_reason="")
        .order_by("pk")
        .values_list("pk", "request_id")[:100]
    )
    erased = 0
    for action_id, case_id in candidates:
        with transaction.atomic():
            # Same lock order as issuance: case first, then action. Recheck after waits.
            case = (
                RightsRequest.objects.select_for_update(skip_locked=True).filter(pk=case_id).first()
            )
            if not case:
                continue
            draft = (
                RightsAction.objects.select_for_update()
                .filter(
                    pk=action_id,
                    created_at__lte=cutoff,
                    purged_at__isnull=True,
                    final_response__isnull=True,
                )
                .exclude(encrypted_reason="")
                .first()
            )
            if not draft:
                continue
            prefix = draft.operation.split("_", 1)[0]
            issued = list(
                RightsAction.objects.filter(
                    request=case,
                    expected_version=draft.expected_version,
                    operation=prefix + ("_final_close" if prefix == "rectify" else "_final_issue"),
                )
            )
            protected, intact = None, True
            for record in issued:
                try:
                    body = checked_body(record.encrypted_reason)
                    if _digest(body) != record.payload_digest:
                        raise ValidationError("Issuance integrity changed")
                    if body.get("draft") == draft.pk:
                        protected = RightsResponse.objects.filter(
                            key=record.key, request=case
                        ).first()
                        if not protected or body.get("draft_digest") != draft.payload_digest:
                            raise ValidationError("Issued draft binding unavailable")
                except ValidationError:
                    intact = False
                    break
            if not intact:
                continue  # Never erase potential issued evidence on an uncertain binding.
            if protected:
                draft.final_response = protected
                draft.save(update_fields=["final_response"])
                continue
            draft.encrypted_reason = ""
            draft.purged_at = now
            draft.save(update_fields=["encrypted_reason", "purged_at"])
            erased += 1
    return erased
