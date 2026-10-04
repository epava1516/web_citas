"""Correct one profile's contact channels without rewriting a shared phone claim."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection
from django.views.decorators.debug import sensitive_variables

from apps.core.models import PhoneClaim
from apps.core.verification_services import normalize_phone
from apps.listings.forms import normalize_telegram


@sensitive_variables()
def validate(value, person=None):
    if (
        not isinstance(value, dict)
        or set(value) != {"phone", "whatsapp", "telegram"}
        or not isinstance(value["phone"], str)
        or len(value["phone"]) > 30
        or type(value["whatsapp"]) is not bool
        or not isinstance(value["telegram"], str)
        or len(value["telegram"]) > 32
    ):
        raise ValidationError("Invalid contact fields / Campos de contacto no válidos")
    normalized = {
        "phone": normalize_phone(value["phone"]) if value["phone"] else "",
        "whatsapp": value["whatsapp"],
        "telegram": normalize_telegram(value["telegram"]),
    }
    if normalized["whatsapp"] and not normalized["phone"]:
        raise ValidationError("WhatsApp requires a phone / WhatsApp requiere teléfono")
    if person is not None:
        claim(normalized, person)
    return normalized


@sensitive_variables()
def claim(value, person):
    if not value["phone"]:
        return None
    query = PhoneClaim.objects.filter(phone=value["phone"])
    if connection.in_atomic_block:
        query = query.select_for_update()
    row = query.first()
    if (
        not row
        or not row.verified_at
        or row.individual_id != person.individual_id
        or row.agency_id != person.agency_id
        or (settings.PRODUCTION and row.verification_procedure != "sms-v1")
        or (
            not settings.PRODUCTION and row.verification_procedure not in {"sms-v1", "simulator-v1"}
        )
    ):
        raise ValidationError(
            "Verified contact for current manager required / Contacto verificado del gestor actual obligatorio"
        )
    return row


@sensitive_variables()
def source(revision):
    return {"phone": revision.phone, "whatsapp": revision.whatsapp, "telegram": revision.telegram}


@sensitive_variables()
def binding(person):
    query = PhoneClaim.objects.filter(pk=person.phone_claim_id)
    if connection.in_atomic_block:
        query = query.select_for_update()
    row = query.first()
    if not row:
        return None
    return {
        "id": row.pk,
        "phone": row.phone,
        "individual": str(row.individual_id or ""),
        "agency": str(row.agency_id or ""),
        "verified_at": row.verified_at.isoformat() if row.verified_at else None,
        "procedure": row.verification_procedure,
    }


@sensitive_variables()
def display(value, english=False):
    return " · ".join(
        ([value["phone"]] if value["phone"] else [])
        + (["WhatsApp"] if value["whatsapp"] else [])
        + (["Telegram: " + value["telegram"]] if value["telegram"] else [])
    ) or ("No contacts specified" if english else "Sin contactos indicados")
