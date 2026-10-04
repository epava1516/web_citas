"""Coherent active categories/services for a corrected draft revision."""

from django.core.exceptions import ValidationError
from django.db import connection

from apps.catalog.models import Category, Service


def validate(value):
    if not isinstance(value, dict) or set(value) != {"categories", "services"}:
        raise ValidationError(
            "Complete catalog selection required / Selección completa obligatoria"
        )
    rows = {}
    normalized = {}
    for field, model, limit in [("categories", Category, 100), ("services", Service, 500)]:
        identifiers = value[field]
        if (
            not isinstance(identifiers, list)
            or not 1 <= len(identifiers) <= limit
            or any(type(pk) is not int or not 0 < pk <= 9223372036854775807 for pk in identifiers)
            or len(set(identifiers)) != len(identifiers)
        ):
            raise ValidationError("Invalid catalog selection / Selección de catálogo no válida")
        normalized[field] = sorted(identifiers)
        query = model.objects.filter(pk__in=identifiers, active=True).order_by("pk")
        if connection.in_atomic_block:
            query = query.select_for_update()
        rows[field] = list(query)
        if len(rows[field]) != len(identifiers):
            raise ValidationError("Catalog selection unavailable / Selección no disponible")
    if any(service.category_id not in normalized["categories"] for service in rows["services"]):
        raise ValidationError("Service outside selected categories / Servicio fuera de categorías")
    return normalized


def source(revision):
    return {
        field: list(getattr(revision, field).order_by("pk").values_list("pk", flat=True))
        for field in ["categories", "services"]
    }


def display(value, english=False):
    field = "name_en" if english else "name_es"
    return " · ".join(
        [
            getattr(row, field)
            for row in Category.objects.filter(pk__in=value["categories"]).order_by("pk")
        ]
        + [
            getattr(row, field)
            for row in Service.objects.filter(pk__in=value["services"]).order_by("pk")
        ]
    )
