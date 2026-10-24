"""Correct self-described listing attributes using existing editor choices."""

from copy import deepcopy

from django import forms
from django.core.exceptions import ValidationError
from django.db import connection
from django.views.decorators.debug import sensitive_variables

from apps.catalog.models import Municipality
from apps.listings.forms import DetailsForm

SCALARS = [
    "content_language",
    "profile_type",
    "show_trans_label",
    "spoken_languages",
    "days",
    "time_slot",
    "reception",
    "travel",
]
FIELDS = SCALARS + ["travel_areas"]
LEGACY_FIELDS = set(FIELDS) - {"show_trans_label"}


def field(name, label):
    result = deepcopy(DetailsForm.base_fields[name])
    result.label = label
    return result


class Editor(forms.Form):
    content_language = field("content_language", "Idioma del contenido / Content language")
    profile_type = field("profile_type", "Tipo de perfil / Profile type")
    show_trans_label = field("show_trans_label", "Mostrar etiqueta trans / Show trans label")
    spoken_languages = field("spoken_languages", "Idiomas hablados / Spoken languages")
    days = field("days", "Días / Days")
    time_slot = field("time_slot", "Horario / Time slot")
    reception = forms.BooleanField(required=False, label="Recepción / Reception")
    travel = forms.BooleanField(required=False, label="Desplazamiento / Travel")
    travel_areas = forms.ModelMultipleChoiceField(
        queryset=Municipality.objects.filter(active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Ciudades de desplazamiento / Travel cities",
    )


@sensitive_variables()
def validate(value):
    if not isinstance(value, dict) or (set(value) != set(FIELDS) and set(value) != LEGACY_FIELDS):
        raise ValidationError("Complete profile details required / Detalles completos obligatorios")
    flags = ["reception", "travel"] + (["show_trans_label"] if "show_trans_label" in value else [])
    if any(type(value[field]) is not bool for field in flags):
        raise ValidationError("Invalid detail flags / Opciones no válidas")
    for field, limit in [("spoken_languages", 6), ("days", 7), ("travel_areas", 1000)]:
        items = value[field]
        if not isinstance(items, list) or len(items) > limit:
            raise ValidationError("Invalid detail list / Lista de detalles no válida")
        if field == "travel_areas":
            if any(type(pk) is not int or not 0 < pk <= 9223372036854775807 for pk in items):
                raise ValidationError("Invalid travel city / Ciudad de desplazamiento no válida")
        elif any(not isinstance(item, str) for item in items):
            raise ValidationError("Invalid detail choice / Opción de detalles no válida")
        if len(set(items)) != len(items):
            raise ValidationError("Duplicate detail choices / Opciones duplicadas")
    if any(
        not isinstance(value[field], str)
        for field in ["content_language", "profile_type", "time_slot"]
    ):
        raise ValidationError("Invalid detail choice / Opción de detalles no válida")
    editor = Editor(value)
    if not editor.is_valid():
        raise ValidationError("Invalid profile details / Detalles de perfil no válidos")
    cities = Municipality.objects.filter(pk__in=value["travel_areas"], active=True).order_by("pk")
    if connection.in_atomic_block:
        cities = cities.select_for_update()
    if len(list(cities)) != len(value["travel_areas"]):
        raise ValidationError("Travel city unavailable / Ciudad de desplazamiento no disponible")
    return {
        **{field: editor.cleaned_data[field] for field in SCALARS if field in value},
        "spoken_languages": sorted(value["spoken_languages"]),
        "days": sorted(value["days"]),
        "travel_areas": sorted(value["travel_areas"]),
    }


@sensitive_variables()
def source(revision):
    return {
        **{field: getattr(revision, field) for field in SCALARS},
        "travel_areas": list(revision.travel_areas.order_by("pk").values_list("pk", flat=True)),
    }


@sensitive_variables()
def display(value, language=None):
    from .rectification_presentation import caption

    def label(value):
        return caption(value, language) if language in {"es", "en"} else value

    parts = []
    for field in SCALARS:
        if field not in value:  # Historical proposals do not implicitly change a later field.
            continue
        form_field = Editor.base_fields[field]
        item = value[field]
        if hasattr(form_field, "choices"):
            choices = dict(form_field.choices)

            def choice(value):
                # Only schema-owned captions are translated; unknown/raw values are preserved.
                return str(label(choices[value])) if value in choices else str(value)

            item = ", ".join(choice(x) for x in item) if isinstance(item, list) else choice(item)
        elif isinstance(item, bool):
            item = label("Sí / Yes") if item else "No"
        parts.append(str(label(form_field.label or field)) + ": " + str(item))
    parts.append(
        str(label("Ciudades / Cities"))
        + ": "
        + ", ".join(
            str(row)
            for row in Municipality.objects.filter(pk__in=value["travel_areas"]).order_by("pk")
        )
    )
    return "\n".join(parts)
