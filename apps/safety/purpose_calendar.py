"""Versioned operational follow-up; never releases processing restrictions."""

from datetime import date, timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .erasure_inventory import canonical
from .models import PurposeCalendarEvent, PurposeRestriction, RightsAction
from .processing_review import authorize
from .rights import fingerprint
from .rights_scope import locked_case


def permission(user, case, restriction):
    fresh = authorize(user, case, review_permission=False)
    if (
        not fresh.has_perm("safety.review_purpose_calendar")
        or fresh.pk == restriction.execution.action.actor_id
    ):
        raise PermissionDenied
    return fresh


@transaction.atomic
@sensitive_variables()
def record(
    user,
    restriction_id,
    key,
    version,
    case_version,
    operation,
    reason,
    next_review_on=None,
    history_before=None,
):
    reference = (
        PurposeRestriction.objects.filter(pk=restriction_id)
        .values_list("execution__action__request_id", flat=True)
        .first()
    )
    if not reference:
        raise PermissionDenied
    case, person, _ = locked_case(reference, lock_listing=True, allow_version_change=True)
    restriction = (
        PurposeRestriction.objects.select_for_update(of=("self",))
        .select_related("execution__action")
        .get(pk=restriction_id)
    )
    fresh = permission(user, case, restriction)
    subject_id = case.account_subject_id or (person.subject_id if person else None)
    if (
        restriction.execution.action.request_id != case.pk
        or restriction.subject_id != subject_id
        or restriction.execution.account_subject_id != case.account_subject_id
        or restriction.execution.person_id != case.person_id
    ):
        raise PermissionDenied
    if (
        operation not in {"inspect", "follow_up"}
        or not isinstance(reason, str)
        or not 20 <= len(reason.strip()) <= 2000
    ):
        raise ValidationError("Invalid follow-up / Seguimiento inválido")
    operation_name = "purpose_cal_inspect" if operation == "inspect" else "purpose_cal_follow"
    signature = fingerprint(
        canonical(
            {
                "restriction": restriction.pk,
                "version": version,
                "case_version": case_version,
                "operation": operation,
                "reason": reason,
                "next_review_on": next_review_on,
                "history_before": history_before,
            }
        )
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == fresh.pk
            and previous.operation == operation_name
            and previous.payload_digest == signature
        ):
            event = PurposeCalendarEvent.objects.get(action=previous)
            permission(user, case, restriction)
            try:
                snapshot = unseal(event.encrypted_snapshot)
            except (InvalidToken, ValueError, KeyError, TypeError) as error:
                raise ValidationError(
                    "Calendar record unavailable / Registro de calendario no disponible"
                ) from error
            return event, snapshot
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if (
        case.version != case_version
        or restriction.version != version
        or not restriction.active
        or case.status != "reviewing"
    ):
        raise ValidationError("Measure or request changed / Medida o solicitud cambiada")
    if operation == "follow_up":
        if (
            not isinstance(next_review_on, date)
            or not timezone.localdate()
            < next_review_on
            <= timezone.localdate() + timedelta(days=90)
            or history_before is not None
        ):
            raise ValidationError(
                "Future operational review within 90 days required / Revisión operativa futura dentro de 90 días obligatoria"
            )
    elif next_review_on is not None:
        raise ValidationError("Inspection cannot change dates / Consulta no cambia fechas")
    if (
        history_before is not None
        and not restriction.calendar_events.filter(pk=history_before).exists()
    ):
        raise ValidationError("Invalid history cursor / Cursor de historia inválido")
    rows = (
        restriction.calendar_events.select_related("action")
        .filter(action__operation="purpose_cal_follow")
        .order_by("-pk")
    )
    if history_before is not None:
        rows = rows.filter(pk__lt=history_before)
    history = list(rows[:51])
    snapshot = {
        "restriction": restriction.pk,
        "version": restriction.version,
        "initial_review_on": str(restriction.initial_review_on or restriction.review_on),
        "review_on": str(restriction.review_on),
        "history": [],
        "next_cursor": history[49].pk if len(history) > 50 else None,
    }
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=fresh,
                expected_version=case_version,
                operation=operation_name,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            event = PurposeCalendarEvent.objects.create(
                action=action,
                restriction=restriction,
                expected_version=version,
                encrypted_snapshot=seal(snapshot),
            )
            # Audit exists before any historical reason is decrypted.
            for row in history[:50]:
                snapshot["history"].append(
                    {
                        "id": row.pk,
                        "created_at": str(row.created_at),
                        "reason": unseal(row.action.encrypted_reason)["reason"],
                    }
                )
            if operation == "follow_up":
                restriction.initial_review_on = (
                    restriction.initial_review_on or restriction.review_on
                )
                restriction.review_on = next_review_on
                restriction.version += 1
                restriction.save(update_fields=["initial_review_on", "review_on", "version"])
                snapshot["next_review_on"] = str(next_review_on)
            event.encrypted_snapshot = seal(snapshot)
            event.save(update_fields=["encrypted_snapshot"])
            permission(user, case, restriction)
            return event, snapshot
    except (IntegrityError, InvalidToken, ValueError, KeyError, TypeError) as error:
        raise ValidationError(
            "Calendar record unavailable / Registro de calendario no disponible"
        ) from error
