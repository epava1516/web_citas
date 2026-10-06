"""Reviewed in-app delivery only; no external transport or inferred historical authority."""

from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.core.models import AgencyMember, User

from .crypto import seal
from .models import RightsAction, RightsRecipientNotice
from .rights_access_response_draft import checked_body
from .rights_copy_page_review import fresh_authority
from .rights_final_response import _context, _digest, _record
from .rights_scope import locked_case


def authorized_targets(case, person):
    if person:
        recipients = {person.individual_id} if person.individual_id else {person.agency.owner_id}
        if (
            person.agency_id
            and person.assigned_editor_id
            and AgencyMember.objects.filter(
                agency_id=person.agency_id, user_id=person.assigned_editor_id, active=True
            ).exists()
        ):
            recipients.add(person.assigned_editor_id)
        authority = str(person.manager_version)
    else:
        recipients = {case.account_subject_id}
        authority = "account"
    return [
        {"recipient": str(user.pk), "authorization_version": authority}
        for user in User.objects.filter(
            pk__in=recipients, is_active=True, account_erased_at__isnull=True
        ).order_by("pk")
    ]


def notice_payload(case, effects):
    if case.kind == "erase":
        purposes = [
            {"purpose": purpose, "state": "erased"} for purpose in effects["completed_purposes"]
        ]
    else:
        purposes = [
            {"purpose": row["purpose"], "state": row["state"]}
            for row in effects["decisions"]
            if row["state"] in {"restricted", "ceased"}
        ]
    return {
        "schema": "rights-recipient-notice-v1",
        "kind": case.kind,
        "execution": str(effects["execution"]),
        "purposes": purposes,
        "simulation": True,
        "complete": False,
    }


def delivery_evidence(case, execution_key):
    result = []
    for row in (
        RightsRecipientNotice.objects.filter(request=case, execution_key=str(execution_key))
        .select_related("action", "acknowledged_read", "acknowledged_action")
        .order_by("pk")
    ):
        checked_delivery(row, case)
        if _digest(checked_body(row.encrypted_payload)) != row.payload_digest:
            raise ValidationError("Recipient evidence content changed")
        if row.acknowledged_at:
            checked_ack(row)
        result.append(
            {
                "pk": row.pk,
                "recipient_id": row.recipient_id,
                "authorization_version": row.authorization_version,
                "payload_digest": row.payload_digest,
                "acknowledged_at": row.acknowledged_at.isoformat() if row.acknowledged_at else None,
            }
        )
    return result


@sensitive_variables()
def approved(user, case, version, responses, review_id, *, current_source):
    from . import rights_communications as communications

    reviewed = (
        RightsAction.objects.select_for_update()
        .select_related("actor")
        .filter(
            pk=review_id, request=case, operation="rights_comms_review", expected_version=version
        )
        .first()
    )
    if not reviewed:
        raise ValidationError("Own reviewed recipient assessment required")
    body = checked_body(reviewed.encrypted_reason)
    if _digest(body) != reviewed.payload_digest or body.get("outcome") != "approved":
        raise ValidationError("Approved recipient assessment required")
    if reviewed.actor_id == user.pk:
        raise PermissionDenied("Independent recipient approval required")
    fresh_authority(reviewed.actor, case, body["session"], body["mfa"])
    fresh = User.objects.get(pk=reviewed.actor_id)
    if not fresh.is_active or not fresh.has_perm("safety.review_recipient_assessment"):
        raise PermissionDenied
    latest = (
        RightsAction.objects.filter(
            request=case,
            operation="rights_comms_review",
            expected_version=version,
        )
        .order_by("-pk")
        .first()
    )
    if not latest or latest.pk != reviewed.pk:
        raise ValidationError("Latest recipient assessment review required")
    plan = (
        RightsAction.objects.select_related("actor")
        .filter(
            pk=body.get("plan"),
            request=case,
            operation="rights_comms_plan",
            expected_version=version,
        )
        .first()
    )
    if not plan or plan.payload_digest != body.get("digest"):
        raise ValidationError("Exact reviewed recipient plan required")
    data = checked_body(plan.encrypted_reason)
    if (
        _digest(data) != plan.payload_digest
        or data.get("version") != version
        or data.get("responses") != responses
        or data.get("channel") != case.receipt_digest
    ):
        raise ValidationError("Recipient review binding changed")
    communications.backend(case.pk)._actor(plan.actor, case, assigned=True)
    fresh_authority(plan.actor, case, data["session"], data["mfa"])
    read = RightsAction.objects.filter(
        pk=body.get("read"),
        request=case,
        actor=reviewed.actor,
        operation="rights_comms_read",
        expected_version=version,
    ).first()
    if not read:
        raise ValidationError("Exact reviewed recipient read required")
    access = checked_body(read.encrypted_reason)
    if (
        _digest(access) != read.payload_digest
        or access.get("plan") != plan.pk
        or access.get("digest") != plan.payload_digest
        or access.get("responses") != responses
        or access.get("channel") != case.receipt_digest
    ):
        raise ValidationError("Recipient review read binding changed")
    fresh_authority(reviewed.actor, case, access["session"], access["mfa"])
    # Replays may observe acknowledgements added by this delivery, but no other drift.
    _, person, listing = locked_case(case.pk, lock_listing=True, allow_erased_account=True)
    source = communications.snapshot(case, person, listing, data["source"]["execution"])
    old = data["source"]
    if current_source:
        matches = _digest(source) == _digest(old)
    else:
        matches = _digest({k: v for k, v in source.items() if k != "manager_notices"}) == _digest(
            {k: v for k, v in old.items() if k != "manager_notices"}
        )
    if not matches:
        raise ValidationError("Reviewed recipient source changed")
    latest_plan = (
        RightsAction.objects.filter(
            request=case,
            operation="rights_comms_plan",
            expected_version=version,
        )
        .order_by("-pk")
        .first()
    )
    if not latest_plan or latest_plan.pk != plan.pk:
        raise ValidationError("Latest reviewed recipient plan required")
    return reviewed, data


@transaction.atomic
@sensitive_variables()
def deliver(user, case_id, version, responses, review_id, key):
    from . import rights_communications as communications

    case, _, _ = _context(
        communications.backend(case_id)._POLICY, user, case_id, version, responses, assigned=True
    )
    previous = RightsAction.objects.filter(key=key).first()
    reviewed, data = approved(
        user, case, version, responses, review_id, current_source=previous is None
    )
    payload = data["source"]["notice_payload"]
    targets = data["source"]["notice_targets"]
    if not targets:
        raise ValidationError("No authorized current recipient; keep delivery pending")
    action = _record(
        user,
        case,
        key,
        "rights_comms_deliver",
        {
            "review": reviewed.pk,
            "digest": reviewed.payload_digest,
            "version": version,
            "responses": responses,
            "channel": case.receipt_digest,
            "payload": payload,
            "targets": targets,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    for target in targets:
        notice, created = RightsRecipientNotice.objects.get_or_create(
            request=case,
            execution_key=payload["execution"],
            recipient_id=int(target["recipient"]),
            authorization_version=target["authorization_version"],
            defaults={
                "action": action,
                "encrypted_payload": seal(payload),
                "payload_digest": _digest(payload),
            },
        )
        if not created and (
            notice.payload_digest != _digest(payload)
            or _digest(checked_body(notice.encrypted_payload)) != notice.payload_digest
        ):
            raise ValidationError("Existing recipient delivery conflicts with reviewed content")
    return action


def recipient_authority(user, case, person, notice):
    fresh = User.objects.get(pk=user.pk)
    if (
        not fresh.is_active
        or fresh.account_erased_at
        or not fresh.mfa_enabled
        or fresh.session_version != user.session_version
        or fresh.mfa_version != user.mfa_version
        or notice.recipient_id != fresh.pk
        or {"recipient": str(fresh.pk), "authorization_version": notice.authorization_version}
        not in authorized_targets(case, person)
    ):
        raise PermissionDenied


@transaction.atomic
@sensitive_variables()
def inspect_notice(user, notice_id, purpose):
    if not isinstance(purpose, str) or not 10 <= len(purpose.strip()) <= 200:
        raise ValidationError("Audited recipient access purpose required")
    metadata = RightsRecipientNotice.objects.filter(pk=notice_id).first()
    if not metadata:
        raise ValidationError("Recipient notice unavailable")
    case, person, _ = locked_case(metadata.request_id, lock_listing=True, allow_erased_account=True)
    notice = RightsRecipientNotice.objects.select_for_update().get(pk=notice_id)
    recipient_authority(user, case, person, notice)
    checked_delivery(notice, case)
    read = _record(
        user,
        case,
        uuid4(),
        "rights_notice_read",
        {
            "notice": notice.pk,
            "digest": notice.payload_digest,
            "purpose": purpose,
            "authority": notice.authorization_version,
            "session": user.session_version,
            "mfa": user.mfa_version,
        },
    )
    payload = checked_body(notice.encrypted_payload)
    if (
        _digest(payload) != notice.payload_digest
        or payload.get("execution") != notice.execution_key
        or payload.get("kind") != case.kind
        or notice.action.request_id != case.pk
    ):
        raise ValidationError("Recipient notice integrity changed")
    return read, payload


@transaction.atomic
@sensitive_variables()
def acknowledge(user, notice_id, read_id):
    metadata = RightsRecipientNotice.objects.filter(pk=notice_id).first()
    if not metadata:
        raise ValidationError("Recipient notice unavailable")
    case, person, _ = locked_case(metadata.request_id, lock_listing=True, allow_erased_account=True)
    notice = RightsRecipientNotice.objects.select_for_update().get(pk=notice_id)
    recipient_authority(user, case, person, notice)
    checked_delivery(notice, case)
    read = RightsAction.objects.filter(
        pk=read_id, request=case, actor=user, operation="rights_notice_read"
    ).first()
    if not read:
        raise ValidationError("Read the exact recipient notice before acknowledgement")
    body = checked_body(read.encrypted_reason)
    if (
        _digest(body) != read.payload_digest
        or body.get("notice") != notice.pk
        or body.get("digest") != notice.payload_digest
        or body.get("authority") != notice.authorization_version
        or body.get("session") != user.session_version
        or body.get("mfa") != user.mfa_version
        or _digest(checked_body(notice.encrypted_payload)) != notice.payload_digest
    ):
        raise ValidationError("Recipient acknowledgement binding changed")
    if not notice.acknowledged_at:
        now = timezone.now()
        ack = _record(
            user,
            case,
            uuid4(),
            "rights_notice_ack",
            {
                "notice": notice.pk,
                "read": read.pk,
                "digest": notice.payload_digest,
                "authority": notice.authorization_version,
                "acknowledged_at": now.isoformat(),
                "session": user.session_version,
                "mfa": user.mfa_version,
            },
        )
        notice.acknowledged_at = now
        notice.acknowledged_read = read
        notice.acknowledged_action = ack
        notice.save(update_fields=["acknowledged_at", "acknowledged_read", "acknowledged_action"])
    checked_ack(notice)

    return notice


def checked_delivery(notice, case):
    action = notice.action
    body = checked_body(action.encrypted_reason)
    if (
        action.request_id != case.pk
        or action.operation != "rights_comms_deliver"
        or _digest(body) != action.payload_digest
        or _digest(body.get("payload")) != notice.payload_digest
        or {
            "recipient": str(notice.recipient_id),
            "authorization_version": notice.authorization_version,
        }
        not in body.get("targets", [])
    ):
        raise ValidationError("Reviewed recipient delivery integrity changed")


@sensitive_variables()
def checked_ack(notice):
    read, ack = notice.acknowledged_read, notice.acknowledged_action
    if not read or not ack or not notice.acknowledged_at:
        raise ValidationError("Recipient receipt audit unavailable")
    access, body = checked_body(read.encrypted_reason), checked_body(ack.encrypted_reason)
    if (
        read.request_id != notice.request_id
        or ack.request_id != notice.request_id
        or read.actor_id != notice.recipient_id
        or ack.actor_id != notice.recipient_id
        or read.operation != "rights_notice_read"
        or ack.operation != "rights_notice_ack"
        or _digest(access) != read.payload_digest
        or _digest(body) != ack.payload_digest
        or access.get("notice") != notice.pk
        or body.get("notice") != notice.pk
        or access.get("digest") != notice.payload_digest
        or body.get("digest") != notice.payload_digest
        or access.get("authority") != notice.authorization_version
        or body.get("authority") != notice.authorization_version
        or body.get("read") != read.pk
        or body.get("acknowledged_at") != notice.acknowledged_at.isoformat()
        or body.get("session") != access.get("session")
        or body.get("mfa") != access.get("mfa")
    ):
        raise ValidationError("Recipient receipt audit changed")
