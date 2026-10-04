"""Private structured assessment forms; GET never decrypts recipient inventory."""

import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.forms import formset_factory
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import Agency, User

from .models import RightsRectificationRecipientInventory, RightsRequest
from .recipient_assessments import inspect, propose, targets
from .rectification_review import permission
from .rights import allowed
from .rights_scope import permitted
from .views import private


def target_title(token, candidate, english):
    if candidate:
        kind = candidate["kind"]
        label = (
            ("Agency representation" if english else "Representación por agencia")
            if kind == "agency"
            else ("Publishing or management account" if english else "Cuenta publicadora o gestora")
        )
        try:
            name = (
                Agency.objects.filter(pk=candidate["reference"])
                .values_list("name", flat=True)
                .first()
                if kind == "agency"
                else User.objects.filter(
                    pk=int(candidate["reference"]), account_erased_at__isnull=True
                )
                .values_list("username", flat=True)
                .first()
            )
        except (ValueError, ValidationError):
            name = None
        return (
            label
            + ": "
            + (
                name
                or ("Identity requires review" if english else "Identidad pendiente de revisar")
            )
        )
    labels = {
        "actual_disclosures_and_recipient_scope_review": (
            "Actual disclosures and recipient scope",
            "Comunicaciones reales y ámbito de destinatarios",
        ),
        "historical_editor_access_without_assignment_history": (
            "Historical editor access",
            "Acceso histórico de editores",
        ),
        "public_audience_and_reuse_without_identified_recipients": (
            "Public audience and reuse",
            "Público y reutilización",
        ),
        "processors_and_external_destinations_register": (
            "Processors and external destinations",
            "Encargados y destinos externos",
        ),
        "historical_recipient_contact_authorization_and_delivery": (
            "Historical recipient contact and delivery",
            "Contacto y entrega a destinatarios históricos",
        ),
    }
    return labels.get(token.removeprefix("gap:"), ("Unresolved gap", "Laguna pendiente"))[
        0 if english else 1
    ]


class AccessForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar campos / Inspect fields"),
            ("propose", "Proponer evaluación / Propose assessment"),
        ]
    )
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )


class DecisionForm(forms.Form):
    target = forms.CharField(widget=forms.HiddenInput, max_length=200)
    outcome = forms.ChoiceField(
        label="Decisión propuesta / Proposed decision",
        choices=[
            ("pending", "Pendiente / Pending"),
            ("not_disclosed", "Sin divulgación acreditada / No disclosure assessed"),
            ("communicated", "Comunicación con acuse / Communication with receipt"),
            ("impossible", "Proponer imposibilidad / Propose impossibility"),
            (
                "disproportionate",
                "Proponer esfuerzo desproporcionado / Propose disproportionate effort",
            ),
        ],
    )
    reason = forms.CharField(
        min_length=20, max_length=2000, widget=forms.Textarea, label="Motivos / Grounds"
    )
    evidence = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Evidencia examinada / Examined evidence",
    )


Decisions = formset_factory(
    DecisionForm, extra=0, max_num=1000, absolute_max=1000, validate_max=True
)


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, inventory_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    try:
        permission(request.user)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    inventory = (
        RightsRectificationRecipientInventory.objects.filter(pk=inventory_id, action__request=case)
        .only("pk")
        .first()
    )
    if not case or not inventory:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    access = AccessForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    decisions = None
    status = 200 if request.method == "GET" else 400
    if request.method == "POST" and access.is_valid():
        values = access.cleaned_data
        try:
            if values["operation"] == "inspect":
                data = inspect(
                    request.user, case_id, inventory_id, values["version"], values["purpose"]
                )
                decisions = Decisions(
                    initial=[{"target": token, "outcome": "pending"} for token in targets(data)],
                    prefix="decisions",
                )
                for decision, (token, candidate) in zip(
                    decisions.forms, targets(data).items(), strict=True
                ):
                    decision.target_title = target_title(
                        token, candidate, request.LANGUAGE_CODE == "en"
                    )
                access = AccessForm(
                    initial={"key": uuid.uuid4(), "version": case.version, "operation": "propose"}
                )
                status = 200
            else:
                decisions = Decisions(request.POST, prefix="decisions")
                if decisions.is_valid():
                    rows = {
                        row["target"]: {key: row[key] for key in ["outcome", "reason", "evidence"]}
                        for row in decisions.cleaned_data
                    }
                    if len(rows) != len(decisions.cleaned_data):
                        raise ValidationError(
                            "Duplicate assessment target / Destinatario duplicado"
                        )
                    propose(
                        request.user, case_id, inventory_id, values["key"], values["version"], rows
                    )
                    return private(redirect("rights_inspect", case_id=case.pk))
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            access.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/recipient_assessment.html",
            {"form": access, "decisions": decisions},
            status=status,
        )
    )
