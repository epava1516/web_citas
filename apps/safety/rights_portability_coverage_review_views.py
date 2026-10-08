"""Private independent coverage review; source values appear only after audited POST."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsPortabilityCoverage, RightsRequest
from .rectification_presentation import caption
from .rights import allowed
from .rights_copy_information_views import LocalizedForm
from .rights_portability import DATASETS
from .rights_portability_coverage_inspection import inspect_page
from .rights_portability_coverage_review import record
from .rights_portability_prepare_selection_views import field_label
from .rights_portability_review import authorize
from .rights_portability_views import LABELS, translated
from .views import private


class PageForm(LocalizedForm):
    operation = forms.CharField(initial="inspect", widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    dataset = forms.ChoiceField(choices=[], label="Conjunto / Dataset")
    row_number = forms.IntegerField(min_value=1, initial=1, label="Registro / Record")
    field_page = forms.IntegerField(min_value=1, initial=1, label="Página / Page")
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado / Private purpose",
    )

    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        self.fields["dataset"].choices = [(name, translated(name)) for name in DATASETS] + [
            (
                "binary",
                caption("Imágenes / Images", language)
                if language is not None
                else "Imágenes / Images",
            )
        ]


class DecisionForm(LocalizedForm):
    operation = forms.CharField(initial="review", widget=forms.HiddenInput)
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=200,
        widget=forms.Textarea,
        label="Motivo privado de decisión / Private decision reason",
    )
    outcome = forms.ChoiceField(
        choices=[("approved", "Aprobar / Approve"), ("rejected", "Rechazar / Reject")],
        label="Decisión / Decision",
    )

    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs["id"] = "decision_" + name


def condition_captions(conditions, language):
    """Static enum/tri-state presentation; never translate supplied private text."""
    result = {}
    for name in ("basis", "origin"):
        value = conditions[name]
        result[name] = LABELS.get(value, (value, value))[language == "en"]
    for name in ("automated", "subject_related", "third_party_reviewed"):
        value = conditions[name]
        result[name] = (
            ("Yes" if language == "en" else "Sí")
            if value is True
            else "No"
            if value is False
            else ("Unknown" if language == "en" else "Desconocido")
            if value is None
            else value
        )
    return result


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review(request, case_id, coverage_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    try:
        authorize(request.user, case)
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    coverage = RightsPortabilityCoverage.objects.filter(pk=coverage_id, request=case).first()
    if coverage is None:
        raise Http404
    if coverage.actor_id == request.user.pk:
        return private(
            HttpResponse(
                "Independent reviewer required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere revisión independiente",
                status=403,
            )
        )
    initial = {
        "key": uuid4(),
        "version": case.version,
        "dataset": "subject_account" if case.account_subject_id else "profile",
    }
    form = PageForm(language=request.LANGUAGE_CODE, initial=initial)
    decision_form = DecisionForm(
        language=request.LANGUAGE_CODE, initial={"key": uuid4(), "version": case.version}
    )
    page = decision = None
    status = 200
    if request.method == "POST":
        status = 400
        try:
            if request.POST.get("operation") == "inspect":
                form = PageForm(request.POST, language=request.LANGUAGE_CODE)
                if form.is_valid():
                    values = form.cleaned_data
                    binary = values["dataset"] == "binary"
                    _, page = inspect_page(
                        request.user,
                        case.pk,
                        values["version"],
                        coverage.pk,
                        values["key"],
                        values["reason"],
                        "revisions" if binary else values["dataset"],
                        values["row_number"] - 1,
                        values["field_page"],
                        binary=binary,
                    )
                    for field in page["fields"]:
                        statuses = {
                            "included": ("Incluido", "Included"),
                            "excluded": ("Excluido", "Excluded"),
                            "pending": ("Pendiente", "Pending"),
                        }
                        value = field["status"]
                        field["status_caption"] = statuses.get(value, (value, value))[
                            request.LANGUAGE_CODE == "en"
                        ]
                        if field.get("conditions"):
                            field["condition_captions"] = condition_captions(
                                field["conditions"], request.LANGUAGE_CODE
                            )
                        field["label"] = (
                            field.get("photo") if binary else field_label(field["path"])
                        )
                        field["display_value"] = (
                            field.get("processing_status") if binary else field["value"]
                        )
                    form = PageForm(
                        language=request.LANGUAGE_CODE, initial={**values, "key": uuid4()}
                    )
                    status = 200
            elif request.POST.get("operation") == "review":
                decision_form = DecisionForm(request.POST, language=request.LANGUAGE_CODE)
                if decision_form.is_valid():
                    values = decision_form.cleaned_data
                    decision = record(
                        request.user,
                        case.pk,
                        values["version"],
                        coverage.pk,
                        values["key"],
                        values["reason"],
                        values["outcome"],
                    )
                    decision_form = DecisionForm(
                        language=request.LANGUAGE_CODE,
                        initial={"key": uuid4(), "version": case.version},
                    )
                    status = 200
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            (decision_form if request.POST.get("operation") == "review" else form).add_error(
                None, error
            )
            status = 409
    return private(
        render(
            request,
            "safety/rights_portability_coverage_review.html",
            {
                "case": case,
                "coverage": coverage,
                "form": form,
                "decision_form": decision_form,
                "page": page,
                "decision": decision,
                "decision_caption": dict(decision_form.fields["outcome"].choices).get(
                    decision.outcome, decision.outcome
                )
                if decision
                else None,
            },
            status=status,
        )
    )
