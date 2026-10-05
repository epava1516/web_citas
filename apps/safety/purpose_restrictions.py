"""Durable selected-purpose blocks; review dates never release them automatically."""

from django.core.exceptions import ValidationError
from django.db import connection
from django.http import HttpResponse

from .models import PurposeRestriction


def restricted(subject, purpose):
    if not connection.in_atomic_block:
        raise RuntimeError("Restriction checks require scope locks and a transaction")
    return PurposeRestriction.objects.filter(subject=subject, purpose=purpose, active=True).exists()


def require_unrestricted(subject, purpose):
    if restricted(subject, purpose):
        raise ValidationError(
            "Purpose restricted; reviewed exception required / Finalidad limitada; excepción revisada obligatoria"
        )


def blocked_response():
    response = HttpResponse(
        "This processing purpose is restricted / Esta finalidad de tratamiento está limitada",
        status=409,
    )
    response["Cache-Control"] = "private, no-store"
    return response
