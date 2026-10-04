"""Bounded local outbox processing; simulator never invokes a channel provider."""

from datetime import timedelta

from django.conf import settings
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .crypto import unseal
from .models import (
    ComplaintNotice,
    ReportNotice,
    RightsNotice,
    SimulatedComplaintNoticeDelivery,
    SimulatedRightsNoticeDelivery,
)
from .notices import simulate_delivery


@sensitive_variables()
def simulated_adapter(notice):
    payload = unseal(notice.encrypted_payload)
    validate_email(payload["recipient"])
    if not all(isinstance(payload.get(key), str) and payload[key] for key in ["subject", "body"]):
        raise ValueError("Invalid notice payload")
    if isinstance(notice, ReportNotice):
        if not simulate_delivery(notice.pk):
            raise ValueError("Simulator unavailable")
    else:
        delivery_model = (
            SimulatedRightsNoticeDelivery
            if isinstance(notice, RightsNotice)
            else SimulatedComplaintNoticeDelivery
        )
        delivery_model.objects.create(notice=notice)
        notice.status = "simulated"
        notice.simulated_at = timezone.now()
        notice.save(update_fields=["status", "simulated_at"])


@sensitive_variables()
def process_outbox(limit=100):
    if settings.PRODUCTION or settings.SAFETY_NOTICE_BACKEND != "simulator":
        return {"processed": 0, "simulated": 0, "retry": 0, "failed": 0, "disabled": True}
    limit = min(max(int(limit), 1), 100)
    result = {"processed": 0, "simulated": 0, "retry": 0, "failed": 0, "disabled": False}
    # Interleave both kinds, avoiding starvation by an always-busy report queue.
    while result["processed"] < limit:
        found = False
        for model in [ReportNotice, ComplaintNotice, RightsNotice]:
            if result["processed"] >= limit:
                break
            with transaction.atomic():
                now = timezone.now()
                notice = (
                    model.objects.select_for_update(skip_locked=True)
                    .filter(status__in=["queued", "retry"], attempts__lt=5)
                    .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
                    .order_by("created_at", "pk")
                    .first()
                )
                if not notice:
                    continue
                found = True
                notice.attempts += 1
                try:
                    with transaction.atomic():
                        notice.status = "queued"
                        notice.save(update_fields=["status"])
                        simulated_adapter(notice)
                except Exception:
                    # No exception text, recipient, message, or decrypted payload is persisted/logged.
                    notice.status = "failed" if notice.attempts >= 5 else "retry"
                    notice.error_code = "adapter_failure"
                    notice.next_attempt_at = (
                        None
                        if notice.status == "failed"
                        else now + timedelta(seconds=60 * 2 ** (notice.attempts - 1))
                    )
                    result[notice.status] += 1
                else:
                    notice.status = "simulated"
                    notice.error_code = ""
                    notice.next_attempt_at = None
                    result["simulated"] += 1
                notice.save(update_fields=["status", "attempts", "error_code", "next_attempt_at"])
                result["processed"] += 1
        if not found:
            break
    return result
