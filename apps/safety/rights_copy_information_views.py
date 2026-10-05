"""Guided private information drafts; GET never decrypts previous content."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import User

from .models import RightsCopyInformation, RightsRequest
from .rights import allowed, fingerprint
from .rights_copy_information import FIELDS, inspect, record
from .rights_copy_page_review import fresh_authority
from .rights_exports import can_prepare, canonical, reviewer_case, source_copy
from .views import private


class InformationForm(forms.Form):
    source_digest = forms.CharField(min_length=64, max_length=64, widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    information_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    policy_version = forms.CharField(
        max_length=80, label="Referencia de política / Policy reference"
    )
    reason = forms.CharField(
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )


LABELS = {
    "processing": ("Confirmación de tratamiento", "Processing confirmation"),
    "purposes": ("Finalidades", "Purposes"),
    "categories": ("Categorías de datos", "Data categories"),
    "recipients": ("Destinatarios", "Recipients"),
    "retention": ("Conservación", "Retention"),
    "rights": ("Ejercicio de derechos", "Exercising rights"),
    "complaint": ("Reclamación", "Complaints"),
    "origins": ("Origen de los datos", "Data sources"),
    "automation": ("Decisiones automatizadas", "Automated decisions"),
    "transfers": ("Transferencias y garantías", "Transfers and safeguards"),
}


class FieldForm(forms.Form):
    field = forms.ChoiceField(choices=[(name, name) for name in FIELDS], widget=forms.HiddenInput)
    status = forms.ChoiceField(
        choices=[("pending", "Pendiente / Pending"), ("reviewed", "Revisado / Reviewed")],
        label="Estado / Status",
    )
    source = forms.ChoiceField(
        choices=[
            ("unknown", "Desconocida / Unknown"),
            ("configuration", "Configuración / Configuration"),
            ("inventory", "Inventario / Inventory"),
            ("reviewer", "Revisor / Reviewer"),
        ],
        label="Procedencia / Source",
    )
    text = forms.CharField(
        required=False, max_length=4000, widget=forms.Textarea, label="Información / Information"
    )

    @property
    def label_text(self):
        labels = LABELS.get(self["field"].value(), ("Apartado", "Section"))
        return labels[1 if (get_language() or "").startswith("en") else 0]


FieldSet = forms.formset_factory(
    FieldForm,
    extra=0,
    min_num=10,
    max_num=10,
    absolute_max=10,
    validate_min=True,
    validate_max=True,
)


class ReadForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    information_id = forms.IntegerField(
        min_value=1, label="Referencia de borrador / Draft reference"
    )
    purpose = forms.CharField(
        min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )


def initial_fields(information=None):
    return [
        {
            "field": name,
            **(
                information["access"][name]
                if information
                else {"status": "pending", "text": "", "source": "unknown"}
            ),
        }
        for name in FIELDS
    ]


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    if not RightsRequest.objects.filter(pk=case_id).exists():
        raise Http404
    try:
        with transaction.atomic():
            case, person, listing = reviewer_case(request.user, case_id)
            actor = User.objects.get(pk=request.user.pk)
            fresh_authority(actor, case, request.user.session_version, request.user.mfa_version)
            can_prepare(actor, case, person)
            source_digest = fingerprint(canonical(source_copy(person, listing, case)))
            latest = (
                RightsCopyInformation.objects.filter(request=case, actor=actor)
                .order_by("-version")
                .first()
            )
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    except ValidationError:
        return private(HttpResponse("Inspect assigned verified request first", status=409))
    initial = {
        "source_digest": source_digest,
        "key": uuid4(),
        "version": case.version,
        "information_version": latest.version if latest else 0,
    }
    reading = request.method == "POST" and request.POST.get("operation") == "inspect"
    form = InformationForm(
        request.POST if request.method == "POST" and not reading else None, initial=initial
    )
    fields = FieldSet(
        request.POST if request.method == "POST" and not reading else None,
        initial=initial_fields(),
        prefix="information",
    )
    read_form = ReadForm(
        request.POST if reading else None, initial={"key": uuid4(), "version": case.version}
    )
    saved = None
    status = 400 if request.method == "POST" else 200
    try:
        if reading and read_form.is_valid():
            values = read_form.cleaned_data
            row, information = inspect(
                request.user,
                case_id,
                values["version"],
                values["key"],
                values["information_id"],
                values["purpose"],
            )
            fields = FieldSet(initial=initial_fields(information), prefix="information")
            form = InformationForm(initial={**initial, "policy_version": row.policy_version})
            status = 200
        elif request.method == "POST" and not reading and form.is_valid() and fields.is_valid():
            names = [item.cleaned_data["field"] for item in fields]
            if len(set(names)) != len(FIELDS) or set(names) != set(FIELDS):
                raise ValidationError("Review every distinct information field")
            information = {
                "access": {
                    item.cleaned_data["field"]: {
                        key: item.cleaned_data[key] for key in ["status", "text", "source"]
                    }
                    for item in fields
                },
                "portability": {"status": "pending", "reason": ""}
                if case.kind == "portability"
                else None,
            }
            values = form.cleaned_data
            saved = record(
                request.user,
                case_id,
                values["version"],
                values["key"],
                values["information_version"],
                values["policy_version"],
                values["reason"],
                information,
                expected_source_digest=values["source_digest"],
            )
            form = InformationForm(initial={**initial, "information_version": saved.version})
            fields = FieldSet(initial=initial_fields(), prefix="information")
            status = 200
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    except ValidationError as error:
        (read_form if reading else form).add_error(None, error)
        status = 409
    return private(
        render(
            request,
            "safety/rights_copy_information.html",
            {"case": case, "form": form, "fields": fields, "read_form": read_form, "saved": saved},
            status=status,
        )
    )
