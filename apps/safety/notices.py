from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .crypto import seal, unseal
from .models import ReportNotice, SimulatedNoticeDelivery


@sensitive_variables()
def enqueue_ack(report, email):
    if email:
        ReportNotice.objects.get_or_create(
            event_key=f"report:{report.pk}:ack",
            defaults={
                "report": report,
                "kind": "ack",
                "encrypted_payload": seal(
                    {
                        "recipient": email,
                        "subject": "Denuncia recibida / Report received",
                        "body": "Hemos recibido tu comunicación. Conserva el enlace privado de seguimiento mostrado al enviarla. La recepción no acredita los hechos. / Your report was received. Keep the private receipt link shown on submission. Receipt does not verify the reported facts.",
                    }
                ),
            },
        )


@sensitive_variables()
def enqueue_outcome(report, action):
    messages = {
        "restrict": "Restricción preventiva aplicada / Preventive restriction applied",
        "dismiss": "Denuncia desestimada tras evaluación / Report dismissed after review",
        "uphold": "Restricción confirmada en revisión / Restriction upheld on review",
        "lift": "Restricción de este caso levantada; publicación sujeta a controles / This case restriction was lifted; publication remains subject to checks",
        "reopen": "Comunicación reabierta para nueva evaluación / Report reopened for further assessment",
    }
    if action.operation not in messages:
        return
    email = unseal(report.encrypted_payload).get("email")
    if email:
        ReportNotice.objects.get_or_create(
            event_key=f"action:{action.pk}:outcome",
            defaults={
                "report": report,
                "action": action,
                "kind": "outcome",
                "encrypted_payload": seal(
                    {
                        "recipient": email,
                        "subject": "Actualización de denuncia / Report update",
                        "body": messages[action.operation]
                        + ". Consulta tu enlace privado de seguimiento / Consult your private receipt link.",
                    }
                ),
            },
        )


@transaction.atomic
def simulate_delivery(notice_id):
    # This adapter never invokes mail, network or a console backend.
    if settings.PRODUCTION or settings.SAFETY_NOTICE_BACKEND != "simulator":
        return False
    notice = ReportNotice.objects.select_for_update().filter(pk=notice_id).first()
    if not notice or notice.status != "queued":
        return False
    SimulatedNoticeDelivery.objects.create(notice=notice)
    notice.status = "simulated"
    notice.simulated_at = timezone.now()
    notice.save(update_fields=["status", "simulated_at"])
    return True
