"""Versioned operational review dates; never expire publication restrictions."""

from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .crypto import seal
from .erasure_inventory import canonical
from .models import PrivacyPublicationHold, PublicationCalendarEvent, RightsAction
from .privacy_release import current
from .processing_review import authorize
from .rights import fingerprint
from .rights_scope import locked_profile_case


@transaction.atomic
@sensitive_variables()
def follow_up(user, case_id, hold_id, key, version, hold_version, reason, next_review_on):
    case, person, _ = locked_profile_case(case_id, lock_listing=True, allow_version_change=True)
    hold = (
        PrivacyPublicationHold.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=hold_id, person=person, action__request=case, purpose_execution__isnull=False)
        .first()
    )
    fresh = authorize(user, case, review_permission=False)
    if not fresh.has_perm("safety.review_purpose_calendar"):
        raise PermissionDenied
    if not hold:
        raise PermissionDenied
    if (
        not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
        or not isinstance(next_review_on, date)
        or not timezone.localdate() < next_review_on <= timezone.localdate() + timedelta(days=90)
    ):
        raise ValidationError("Future operational review within 90 days required")
    signature = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "version": version,
                "hold_version": hold_version,
                "reason": reason,
                "next_review_on": next_review_on.isoformat(),
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == "pub_cal_follow"
            and previous.payload_digest == signature
        ):
            return previous
        raise ValidationError("Conflicting replay")
    proof = current(fresh, case, person, hold, version)
    if hold.version != hold_version or not hold.initial_purpose_review_on:
        raise ValidationError("Measure calendar changed or initial date unavailable")
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="pub_cal_follow",
                payload_digest=signature,
                encrypted_reason=seal(
                    {
                        "reason": reason,
                        "hold": hold.pk,
                        "proof": str(proof.pk),
                        "previous_version": hold.version,
                        "previous_review_on": hold.purpose_review_on.isoformat(),
                        "initial_review_on": hold.initial_purpose_review_on.isoformat(),
                        "next_review_on": next_review_on.isoformat(),
                    }
                ),
            )
            PublicationCalendarEvent.objects.create(
                action=action,
                hold=hold,
                expected_version=hold.version,
            )
            hold.version += 1
            hold.purpose_review_on = next_review_on
            hold.save(update_fields=["version", "purpose_review_on"])
            fresh = authorize(user, case, review_permission=False)
            if not fresh.has_perm("safety.review_purpose_calendar"):
                raise PermissionDenied
            return action
    except IntegrityError as error:
        raise ValidationError("Conflicting calendar action") from error


@transaction.atomic
@sensitive_variables()
def history(user, case_id, hold_id, key, version, reason, before=None):
    from cryptography.fernet import InvalidToken

    from .crypto import unseal

    case, person, _ = locked_profile_case(case_id, lock_listing=True, allow_version_change=True)
    hold = (
        PrivacyPublicationHold.objects.select_for_update(of=("self",))
        .select_related("action")
        .filter(pk=hold_id, person=person, action__request=case)
        .first()
    )
    fresh = authorize(user, case, review_permission=False)
    if not hold or not fresh.has_perm("safety.review_purpose_calendar"):
        raise PermissionDenied
    proof = current(fresh, case, person, hold, version)
    if not isinstance(reason, str) or not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("History inspection reason required")
    events = hold.calendar_events.select_related("action").order_by("-pk")
    if before is not None:
        if (
            not isinstance(before, int)
            or isinstance(before, bool)
            or not events.filter(pk=before).exists()
        ):
            raise ValidationError("Invalid history cursor")
        events = events.filter(pk__lt=before)
    rows = list(events[:51])
    signature = fingerprint(
        canonical(
            {
                "hold": hold.pk,
                "version": version,
                "hold_version": hold.version,
                "proof": str(proof.pk),
                "reason": reason,
                "before": before,
                "rows": [[row.pk, fingerprint(row.action.encrypted_reason)] for row in rows],
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id != case.pk
            or previous.actor_id != fresh.pk
            or previous.operation != "pub_cal_history"
            or previous.payload_digest != signature
        ):
            raise ValidationError("Conflicting history replay")
        try:
            return previous, unseal(previous.encrypted_reason)["result"]
        except (InvalidToken, ValueError, KeyError, TypeError) as error:
            raise ValidationError("History record unavailable") from error
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=version,
                operation="pub_cal_history",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            result = {"rows": [], "next_cursor": rows[49].pk if len(rows) > 50 else None}
            for row in rows[:50]:
                body = unseal(row.action.encrypted_reason)
                expected = fingerprint(
                    canonical(
                        {
                            "hold": hold.pk,
                            "version": row.action.expected_version,
                            "hold_version": row.expected_version,
                            "reason": body["reason"],
                            "next_review_on": body["next_review_on"],
                        }
                    )
                )
                if (
                    row.action.operation != "pub_cal_follow"
                    or row.action.request_id != case.pk
                    or row.action.payload_digest != expected
                ):
                    raise ValidationError("Calendar event signature changed")
                if body["hold"] != hold.pk or body["previous_version"] != row.expected_version:
                    raise ValidationError("Calendar event scope changed")
                result["rows"].append(
                    {
                        "id": row.pk,
                        "created_at": row.created_at.isoformat(),
                        "version": row.expected_version,
                        "reason": body["reason"],
                        "previous_review_on": body["previous_review_on"],
                        "next_review_on": body["next_review_on"],
                    }
                )
            action.encrypted_reason = seal({"reason": reason, "result": result})
            action.save(update_fields=["encrypted_reason"])
            fresh = authorize(user, case, review_permission=False)
            if not fresh.has_perm("safety.review_purpose_calendar"):
                raise PermissionDenied
            return action, result
    except (InvalidToken, ValueError, KeyError, TypeError, IntegrityError) as error:
        raise ValidationError("Calendar history unavailable") from error
