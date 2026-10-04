"""Ordered selection of current profile photos; bytes and historical rows remain intact."""

import uuid

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import F
from django.forms import formset_factory
from django.views.decorators.debug import sensitive_variables

from apps.mediafiles.models import Photo


class PhotoForm(forms.Form):
    photo_id = forms.UUIDField(widget=forms.HiddenInput)
    position = forms.IntegerField(min_value=0, max_value=7, label="Orden / Order")


Editor = formset_factory(
    PhotoForm, extra=0, max_num=8, absolute_max=9, validate_max=True, can_delete=True
)


@sensitive_variables()
def source(revision):
    return [
        str(value)
        for value in revision.photos.filter(removed_at__isnull=True)
        .order_by("position", "created_at", "pk")
        .values_list("pk", flat=True)
    ]


@sensitive_variables()
def validate(value, person=None):
    if not isinstance(value, list) or len(value) > 8:
        raise ValidationError("At most eight photos / Máximo ocho fotografías")
    try:
        if any(not isinstance(item, str) for item in value):
            raise ValueError
        normalized = [str(uuid.UUID(item)) for item in value]
    except (ValueError, AttributeError) as error:
        raise ValidationError(
            "Invalid photo selection / Selección de fotografías no válida"
        ) from error
    if len(set(normalized)) != len(normalized):
        raise ValidationError("Repeated photos / Fotografías repetidas")
    if person and normalized:
        photos = Photo.objects.filter(
            pk__in=normalized,
            revision__listing__person=person,
            revision__listing__approved_revision_id=F("revision_id"),
            revision__manager_version=person.manager_version,
            removed_at__isnull=True,
            blob__status="ready",
        ).exclude(blob__derivative="")
        if photos.count() != len(normalized):
            raise ValidationError(
                "Current available profile photos required / Fotografías vigentes y disponibles del perfil obligatorias"
            )
    return normalized


@sensitive_variables()
def initial(value):
    return [{"photo_id": identifier, "position": index} for index, identifier in enumerate(value)]


@sensitive_variables()
def changes(editor):
    rows = [row for row in editor.cleaned_data if row and not row.get("DELETE")]
    positions = [row["position"] for row in rows]
    if len(set(positions)) != len(positions):
        raise ValidationError(
            "Each photo needs a different order / Cada fotografía requiere un orden distinto"
        )
    return validate([str(row["photo_id"]) for row in sorted(rows, key=lambda row: row["position"])])
