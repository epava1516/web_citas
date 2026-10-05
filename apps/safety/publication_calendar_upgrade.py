"""Recover existing calendar facts; never manufacture a reviewed decision."""

from datetime import date

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from .crypto import unseal
from .erasure_inventory import canonical
from .models import PrivacyPublicationHold, PublicationCalendarEvent, RightsAction
from .publication_purpose_release import decision
from .rights import fingerprint
from .rights_scope import locked_profile_case


@transaction.atomic
@sensitive_variables()
def restore_calendar(hold_id):
    """Maintenance-only operation, scoped atomically to one existing measure."""
    candidate = PrivacyPublicationHold.objects.get(pk=hold_id)
    case, person, _ = locked_profile_case(
        candidate.action.request_id, lock_listing=True, allow_version_change=True
    )
    hold = (
        PrivacyPublicationHold.objects.select_for_update(of=("self",))
        .select_related("action", "purpose_execution__review__plan__action")
        .get(pk=hold_id, person=person, action__request=case)
    )
    try:
        initial = date.fromisoformat(decision(hold)["review_on"])
        current_date = initial
        expected_version = 1
        records = []
        for action in (
            RightsAction.objects.select_for_update()
            .filter(request=case, operation="pub_cal_follow")
            .order_by("created_at", "pk")
        ):
            body = unseal(action.encrypted_reason)
            if body["hold"] != hold.pk:
                continue
            signature = fingerprint(
                canonical(
                    {
                        "hold": hold.pk,
                        "version": action.expected_version,
                        "hold_version": body["previous_version"],
                        "reason": body["reason"],
                        "next_review_on": body["next_review_on"],
                    }
                )
            )
            if (
                action.payload_digest != signature
                or body["previous_version"] != expected_version
                or date.fromisoformat(body["initial_review_on"]) != initial
                or date.fromisoformat(body["previous_review_on"]) != current_date
            ):
                raise ValueError
            current_date = date.fromisoformat(body["next_review_on"])
            records.append((action, expected_version))
            expected_version += 1
        if (
            hold.version != expected_version
            or hold.initial_purpose_review_on not in {None, initial}
            or hold.purpose_review_on not in {None, current_date}
        ):
            raise ValueError
        existing = list(hold.calendar_events.select_for_update())
        expected = {action.pk: version for action, version in records}
        if any(expected.get(event.action_id) != event.expected_version for event in existing):
            raise ValueError
        created = 0
        for action, version in records:
            event, new = PublicationCalendarEvent.objects.get_or_create(
                action=action, defaults={"hold": hold, "expected_version": version}
            )
            if event.hold_id != hold.pk or event.expected_version != version:
                raise ValueError
            if new:
                PublicationCalendarEvent.objects.filter(pk=event.pk).update(
                    created_at=action.created_at
                )
                created += 1
        changed = hold.initial_purpose_review_on is None or hold.purpose_review_on is None
        if changed:
            hold.initial_purpose_review_on = initial
            hold.purpose_review_on = current_date
            hold.save(update_fields=["initial_purpose_review_on", "purpose_review_on"])
        return {"dates_restored": changed, "events_restored": created}
    except (InvalidToken, ValueError, KeyError, TypeError, AttributeError) as error:
        raise ValidationError("Calendar recovery facts unavailable or inconsistent") from error
