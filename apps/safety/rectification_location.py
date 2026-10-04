"""Coherent city/postal/area correction, without exact street addresses."""

from django.core.exceptions import ValidationError
from django.db import connection

from apps.catalog.models import Municipality, PostalCode, Zone


def validate(value):
    if not isinstance(value, dict) or set(value) != {"municipality", "postal_code", "zone"}:
        raise ValidationError("Complete location required / Ubicación completa obligatoria")
    rows = {}
    for field, model in [
        ("municipality", Municipality),
        ("postal_code", PostalCode),
        ("zone", Zone),
    ]:
        identifier = value[field]
        if identifier is None and field != "municipality":
            rows[field] = None
            continue
        if type(identifier) is not int or not 0 < identifier <= 9223372036854775807:
            raise ValidationError("Invalid location reference / Referencia geográfica no válida")
        query = model.objects.all()
        if connection.in_atomic_block:
            query = query.select_for_update()
        row = query.filter(pk=identifier).first()
        if not row or (field != "postal_code" and not row.active):
            raise ValidationError("Location unavailable / Ubicación no disponible")
        rows[field] = row
    city, postal, zone = rows["municipality"], rows["postal_code"], rows["zone"]
    if postal and (not postal.public_safe or not postal.municipalities.filter(pk=city.pk).exists()):
        raise ValidationError(
            "Postal code incompatible or restricted / CP incompatible o restringido"
        )
    if zone and zone.municipality_id != city.pk:
        raise ValidationError("Area does not match city / Zona incompatible con ciudad")
    return value


def source(revision):
    return {
        field: getattr(revision, field + "_id") for field in ["municipality", "postal_code", "zone"]
    }


def display(value):
    parts = []
    for field, model in [
        ("municipality", Municipality),
        ("postal_code", PostalCode),
        ("zone", Zone),
    ]:
        if value[field] is not None:
            row = model.objects.get(pk=value[field])
            parts.append(str(row))
    return " · ".join(parts)
