"""Ordered selection of current profile photos; bytes and historical rows remain intact."""

import uuid

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import F, Q
from django.forms import formset_factory
from django.views.decorators.debug import sensitive_variables

from apps.mediafiles.models import Photo


class PhotoForm(forms.Form):
    photo_id = forms.UUIDField(widget=forms.HiddenInput)
    position = forms.IntegerField(min_value=0, max_value=7, label="Orden / Order")
    state = forms.CharField(required=False, disabled=True, label="Estado / State")


Editor = formset_factory(
    PhotoForm, extra=0, max_num=8, absolute_max=17, validate_max=True, can_delete=True
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
def validate(value, person=None, case=None):
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
        photos = available(person, case).filter(pk__in=normalized)
        if photos.count() != len(normalized):
            raise ValidationError(
                "Current available profile photos required / Fotografías vigentes y disponibles del perfil obligatorias"
            )
        if photos.values("blob_id").distinct().count() != len(normalized):
            raise ValidationError("Same image selected twice / Misma imagen seleccionada dos veces")
    return normalized


@sensitive_variables()
def available(person, case=None):
    originals = Q(revision__listing__approved_revision_id=F("revision_id"))
    staged = Q(pk__in=[])
    if case:
        from .rectification_uploads import baseline, eligible

        ids = eligible(case, person, baseline(case, person, person.listing)).values_list(
            "photo_id", flat=True
        )
        staged = Q(pk__in=ids, comparison_complete=True)
    return Photo.objects.filter(
        originals | staged,
        revision__listing__person=person,
        revision__manager_version=person.manager_version,
        removed_at__isnull=True,
        blob__status="ready",
    ).exclude(blob__derivative="")


@sensitive_variables()
def initial(value, uploads=()):
    states = dict(
        Photo.objects.filter(pk__in=list(value) + list(uploads)).values_list("pk", "blob__status")
    )
    labels = {
        "ready": "Ready / Preparada",
        "failed": "Failed / Fallida",
        "queued": "Processing / Procesando",
        "processing": "Processing / Procesando",
    }
    return [
        {
            "photo_id": identifier,
            "position": index % 8,
            "DELETE": identifier in uploads,
            "is_upload": identifier in uploads,
            "state": labels.get(states.get(uuid.UUID(identifier)), "Unavailable / No disponible"),
        }
        for index, identifier in enumerate(list(value) + list(uploads))
    ]


@sensitive_variables()
def changes(editor):
    rows = [row for row in editor.cleaned_data if row and not row.get("DELETE")]
    positions = [row["position"] for row in rows]
    if len(set(positions)) != len(positions):
        raise ValidationError(
            "Each photo needs a different order / Cada fotografía requiere un orden distinto"
        )
    return validate([str(row["photo_id"]) for row in sorted(rows, key=lambda row: row["position"])])
