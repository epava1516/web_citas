"""Scoped encrypted correction proposals; execution requires a separate reviewed step."""

import json
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.catalog.models import Category, Municipality, PostalCode, Service, Zone
from apps.listings.forms import DetailsForm, validate_listing_text
from apps.listings.models import Revision

from . import (
    rectification_catalog,
    rectification_contacts,
    rectification_details,
    rectification_location,
    rectification_rates,
)
from .crypto import seal
from .models import (
    RightsAction,
    RightsRectificationProposal,
    RightsRectificationSourceRead,
    RightsRequest,
)
from .rights import allowed, fingerprint
from .rights_responses import complete_response_read
from .rights_scope import locked_case, permitted
from .rights_verification import authorized_proof, complete_read
from .views import private

FIELDS = {
    "alias": 80,
    **{
        field: DetailsForm.base_fields[field].max_length
        for field in ["title", "description", "description_alternative"]
    },
}


@sensitive_variables()
def validated_changes(value, person=None):
    if (
        not isinstance(value, dict)
        or not value
        or set(value) - (set(FIELDS) | {"location", "catalog", "rates", "contacts", "details"})
    ):
        raise ValidationError("Unsupported correction fields / Campos de corrección no admitidos")
    value = value.copy()
    for field in sorted(value):
        text = value[field]
        if field == "details":
            value[field] = rectification_details.validate(text)
            continue
        if field == "contacts":
            value[field] = rectification_contacts.validate(text, person)
            continue
        if field == "rates":
            value[field] = rectification_rates.validate(text)
            continue
        if field == "catalog":
            value[field] = rectification_catalog.validate(text)
            continue
        if field == "location":
            rectification_location.validate(text)
            continue
        if (
            not isinstance(text, str)
            or len(text) > FIELDS[field]
            or (field != "description_alternative" and not text.strip())
        ):
            raise ValidationError("Invalid correction / Corrección no válida")
        if field != "alias":
            DetailsForm.base_fields[field].clean(text)
        validate_listing_text(text)
    return value


@transaction.atomic
@sensitive_variables()
def propose(user, case_id, key, version, changes, reason):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
    ):
        raise PermissionDenied
    case, person, listing = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    changes = validated_changes(changes, person)
    signature = fingerprint(
        json.dumps({"version": version, "changes": changes, "reason": reason}, sort_keys=True)
    )
    previous = RightsAction.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.operation == "rectify_plan"
            and previous.payload_digest == signature
        ):
            return RightsRectificationProposal.objects.get(action=previous)
        raise ValidationError("Conflicting proposal key / Clave incompatible")
    if (
        case.kind != "rectify"
        or case.version != version
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or not 20 <= len(reason.strip()) <= 2000
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect current assigned correction request / Consulta la solicitud asignada vigente"
        )
    proof = authorized_proof(case, person, "rectify")
    revision, source = source_snapshot(case, person, listing)
    if set(changes) - {"alias"} and (
        not revision or revision.manager_version != person.manager_version
    ):
        raise ValidationError("Current revision required / Revisión vigente obligatoria")
    source_digest = fingerprint(json.dumps(source, sort_keys=True))
    if not RightsRectificationSourceRead.objects.filter(
        request=case,
        actor=user,
        proof=proof,
        case_version=case.version,
        source_digest=source_digest,
    ).exists():
        raise ValidationError(
            "Read current correction source first / Consulta primero la fuente de rectificación vigente"
        )
    try:
        with transaction.atomic():
            action = RightsAction.objects.create(
                key=key,
                request=case,
                actor=user,
                expected_version=version,
                operation="rectify_plan",
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
            )
            proposal = RightsRectificationProposal.objects.create(
                action=action,
                proof=proof,
                person=person,
                source_revision=revision,
                source_digest=source_digest,
                encrypted_changes=seal(changes),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting proposal key / Clave incompatible") from error
    case.version += 1
    case.scope_status = "unverified"
    case.save(update_fields=["version", "scope_status"])
    return proposal


@sensitive_variables()
def source_snapshot(case, person, listing):
    revision = None
    if listing and listing.approved_revision_id:
        revision = Revision.objects.select_for_update().get(pk=listing.approved_revision_id)
    copied_source = None
    if revision:
        # Bind every copied value and relation, not only corrected text fields.
        copied_source = {
            "values": {
                field.attname: getattr(revision, field.attname)
                for field in Revision._meta.concrete_fields
            },
            "relations": {
                field.name: list(
                    getattr(revision, field.name).order_by("pk").values_list("pk", flat=True)
                )
                for field in Revision._meta.many_to_many
            },
            "rates": list(revision.rates.select_for_update().order_by("pk").values()),
            "photos": list(revision.photos.select_for_update().order_by("pk").values()),
        }
        copied_source = json.loads(json.dumps(copied_source, sort_keys=True, default=str))
    source = {
        "copied_source": copied_source,
        "person": str(person.pk),
        "subject": str(person.subject_id),
        "manager_version": person.manager_version,
        "rights_version": person.rights_version,
        "channel": case.receipt_digest,
        "alias": person.alias,
        "phone_binding": rectification_contacts.binding(person),
        "publication_erased_at": person.publication_erased_at.isoformat()
        if person.publication_erased_at
        else None,
        "listing_status": listing.status if listing else None,
        "listing_lifecycle_version": listing.lifecycle_version if listing else None,
        "revision": str(revision.pk) if revision else None,
        "revision_version": revision.edit_version if revision else None,
        "revision_status": revision.status if revision else None,
        "fields": {field: getattr(revision, field) for field in FIELDS if field != "alias"}
        if revision
        else {},
    }
    if revision:
        source["fields"]["location"] = rectification_location.source(revision)
        source["fields"]["catalog"] = rectification_catalog.source(revision)
        source["fields"]["rates"] = rectification_rates.source(revision)
        source["fields"]["contacts"] = rectification_contacts.source(revision)
        source["fields"]["details"] = rectification_details.source(revision)
    return revision, source


@transaction.atomic
@sensitive_variables()
def preview(user, case_id, version, purpose):
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.execute_rights_request")
    ):
        raise PermissionDenied
    case, person, listing = locked_case(case_id, lock_listing=True)
    if not permitted(user, case):
        raise PermissionDenied
    if (
        case.kind != "rectify"
        or case.version != version
        or case.status != "reviewing"
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
        or not complete_response_read(user, case)
        or not 10 <= len(purpose.strip()) <= 200
    ):
        raise ValidationError(
            "Inspect current assigned correction source / Consulta la fuente asignada vigente"
        )
    proof = authorized_proof(case, person, "rectify")
    _, source = source_snapshot(case, person, listing)
    RightsRectificationSourceRead.objects.create(
        request=case,
        actor=user,
        proof=proof,
        case_version=case.version,
        source_digest=fingerprint(json.dumps(source, sort_keys=True)),
        purpose=purpose,
    )
    return {"alias": source["alias"], **source["fields"]}


class ProposalForm(rectification_details.Editor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in rectification_details.FIELDS:
            self.fields[field].required = False

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("preview", "Consultar fuente (auditoría) / Inspect source (audited)"),
            ("propose", "Registrar propuesta / Record proposal"),
        ]
    )
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )
    fields = forms.MultipleChoiceField(
        required=False,
        choices=[
            ("alias", "Nombre del perfil / Profile name"),
            ("title", "Título / Title"),
            ("description", "Descripción / Description"),
            ("description_alternative", "Descripción alternativa / Alternative description"),
            ("location", "Ubicación completa / Complete location"),
            ("catalog", "Categorías y servicios / Categories and services"),
            ("rates", "Tabla de tarifas / Tariff table"),
            ("contacts", "Teléfono y canales / Phone and channels"),
            ("details", "Características y desplazamientos / Attributes and travel"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Campos que se propone corregir / Fields proposed for correction",
    )
    alias = forms.CharField(required=False, max_length=80, label="Nombre del perfil / Profile name")
    title = forms.CharField(required=False, max_length=FIELDS["title"], label="Título / Title")
    description = forms.CharField(
        required=False,
        max_length=FIELDS["description"],
        strip=False,
        widget=forms.Textarea,
        label="Descripción / Description",
    )
    description_alternative = forms.CharField(
        required=False,
        max_length=FIELDS["description_alternative"],
        strip=False,
        widget=forms.Textarea,
        label="Descripción alternativa / Alternative description",
    )
    municipality = forms.ModelChoiceField(
        queryset=Municipality.objects.filter(active=True), required=False, label="Ciudad / City"
    )
    postal_code = forms.ModelChoiceField(
        queryset=PostalCode.objects.filter(public_safe=True),
        required=False,
        label="Código postal / Postal code",
        help_text="Recomendado; sin domicilio / Recommended; no street address",
    )
    zone = forms.ModelChoiceField(
        queryset=Zone.objects.filter(active=True), required=False, label="Zona / Area"
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Categorías / Categories",
    )
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(active=True),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Servicios / Services",
    )
    phone = forms.CharField(
        required=False, max_length=30, label="Teléfono ya verificado / Already verified phone"
    )
    whatsapp = forms.BooleanField(required=False, label="WhatsApp")
    telegram = forms.CharField(required=False, max_length=32, label="Telegram")
    reason = forms.CharField(
        required=False,
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )

    def clean(self):
        data = super().clean()
        if data.get("operation") == "propose":
            selected = data.get("fields", [])
            if not selected:
                raise forms.ValidationError(
                    "Selecciona los campos que se propone corregir / Select fields proposed for correction"
                )
            data["changes"] = {
                field: data.get(field, "")
                for field in selected
                if field not in {"location", "catalog", "rates", "contacts", "details"}
            }
            if "details" in selected:
                data["changes"]["details"] = rectification_details.validate(
                    {
                        **{field: data.get(field) for field in rectification_details.SCALARS},
                        "travel_areas": [row.pk for row in data.get("travel_areas", [])],
                    }
                )
            if "contacts" in selected:
                data["changes"]["contacts"] = rectification_contacts.validate(
                    {
                        "phone": data.get("phone", ""),
                        "whatsapp": data.get("whatsapp", False),
                        "telegram": data.get("telegram", ""),
                    }
                )
            if "location" in selected:
                data["changes"]["location"] = {
                    field: data[field].pk if data.get(field) else None
                    for field in ["municipality", "postal_code", "zone"]
                }
                rectification_location.validate(data["changes"]["location"])
            if "catalog" in selected:
                data["changes"]["catalog"] = rectification_catalog.validate(
                    {
                        field: [row.pk for row in data.get(field, [])]
                        for field in ["categories", "services"]
                    }
                )
        return data


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    if case.kind != "rectify":
        return private(HttpResponse("Unsupported request type", status=409))
    form = ProposalForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    rate_editor = rectification_rates.Editor(
        request.POST if request.method == "POST" else None, prefix="rates"
    )
    source_fields = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            data = form.cleaned_data
            if data["operation"] == "preview":
                source_fields = preview(request.user, case.pk, data["version"], data["purpose"])
            else:
                if "rates" in data["fields"]:
                    if not rate_editor.is_valid():
                        raise ValidationError(
                            "Review rate table errors / Revisa los errores de tarifas"
                        )
                    data["changes"]["rates"] = rectification_rates.changes(rate_editor)
                propose(
                    request.user,
                    case.pk,
                    data["key"],
                    data["version"],
                    data["changes"],
                    data["reason"],
                )
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            if source_fields is None:
                return private(redirect("rights_inspect", case_id=case.pk))
            status = 200
            rate_editor = rectification_rates.Editor(
                initial=source_fields.get("rates", []), prefix="rates"
            )
            form = ProposalForm(
                initial={
                    "key": uuid.uuid4(),
                    "version": case.version,
                    "operation": "propose",
                    **{
                        field: value
                        for field, value in source_fields.items()
                        if field not in {"location", "catalog", "rates", "contacts", "details"}
                    },
                    **source_fields.get("location", {}),
                    **source_fields.get("catalog", {}),
                    **source_fields.get("contacts", {}),
                    **source_fields.get("details", {}),
                }
            )
    return private(
        render(
            request,
            "safety/rights_rectification.html",
            {
                "case": case,
                "form": form,
                "source_fields": source_fields,
                "rate_editor": rate_editor,
                "proposals": Paginator(
                    RightsRectificationProposal.objects.filter(action__request=case)
                    .select_related("action")
                    .defer("encrypted_changes", "action__encrypted_reason")
                    .order_by("-created_at", "-pk"),
                    50,
                ).get_page(request.GET.get("proposals_page")),
            },
            status=status,
        )
    )
