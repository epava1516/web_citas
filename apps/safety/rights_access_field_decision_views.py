"""Private typed field decision forms; GET never recovers decision bodies."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .models import RightsAccessFieldDecision, RightsRequest
from .rectification_presentation import caption
from .rights import allowed
from .rights_access_field_decision import inspect_decision, propose, review
from .rights_access_response_review import authorize_reviewer
from .rights_access_response_views import DecisionForm, ReviewForm
from .views import private


def localize_form(form, language):
    if language is None:
        return form
    for field in form.fields.values():
        field.label = caption(field.label, language)
        if hasattr(field, "choices") and not hasattr(field, "queryset"):
            field.choices = [(value, caption(label, language)) for value, label in field.choices]
    labels = {
        "field_target": ("Campo exacto", "Exact field"),
        "field_key": ("Clave de consulta de campo", "Field inspection key"),
        "outcome": ("Decisión", "Decision"),
    }
    for name, pair in labels.items():
        if name in form.fields:
            form.fields[name].label = pair[language == "en"]
    return form


class ProposalForm(ReviewForm):
    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, **kwargs)
        localize_form(self, language)

    response_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    read_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    model = forms.CharField(max_length=80, widget=forms.HiddenInput)
    reference = forms.CharField(min_length=64, max_length=64, widget=forms.HiddenInput)
    field = forms.CharField(max_length=80, widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("included", "Incluir / Include"),
            ("redacted", "Redactar / Redact"),
            ("omitted", "Omitir / Omit"),
        ]
    )
    redacted = forms.CharField(
        required=False,
        max_length=20000,
        widget=forms.Textarea,
        label="Texto redactado con [redacted] / Redacted text",
    )


def current(request, case_id):
    if not allowed(request):
        raise PermissionDenied
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    authorize_reviewer(request.user, case)
    return case


@login_required
@sensitive_post_parameters()
@require_http_methods(["POST"])
def prepare(request, case_id, inventory_id):
    try:
        case = current(request, case_id)
        if case.assigned_to_id != request.user.pk:
            raise PermissionDenied
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ProposalForm(request.POST, language=request.LANGUAGE_CODE)
    row = body = None
    status = 400
    if form.is_valid():
        value = form.cleaned_data
        try:
            row, body = propose(
                request.user,
                case.pk,
                value["version"],
                value["response_version"],
                inventory_id,
                value["read_id"],
                value["model"],
                value["reference"],
                value["field"],
                value["key"],
                value["reason"],
                value["outcome"],
                value["redacted"] or None,
            )
            status = 200
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    localize_form(form, request.LANGUAGE_CODE)
    return private(
        render(
            request,
            "safety/rights_access_field_decision.html",
            {
                "case": case,
                "form": form,
                "decision": row,
                "body": body,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )


@login_required
@sensitive_post_parameters()
@require_http_methods(["GET", "POST"])
def independent(request, case_id, decision_id):
    try:
        case = current(request, case_id)
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    row = (
        RightsAccessFieldDecision.objects.filter(pk=decision_id, inventory__request=case)
        .select_related("action")
        .first()
    )
    if row is None:
        raise Http404
    if row.action.actor_id == request.user.pk:
        return private(
            HttpResponse(
                "Independent reviewer required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere revisión independiente",
                status=403,
            )
        )
    if case.kind != "access" or case.status != "reviewing":
        return private(
            HttpResponse(
                "Current access request required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere una solicitud de acceso vigente",
                status=409,
            )
        )
    form = ReviewForm(initial={"key": uuid4(), "version": case.version})
    decision_form = DecisionForm(initial={"key": uuid4(), "version": case.version})
    body = decision = None
    status = 200
    if request.method == "POST":
        deciding = request.POST.get("operation") == "review"
        active = DecisionForm(request.POST) if deciding else ReviewForm(request.POST)
        if deciding:
            decision_form = active
        else:
            form = active
        status = 400
        if active.is_valid():
            value = active.cleaned_data
            try:
                if deciding:
                    decision = review(
                        request.user,
                        case.pk,
                        value["version"],
                        row.pk,
                        value["read_id"],
                        value["key"],
                        value["reason"],
                        value["outcome"],
                    )
                else:
                    _, body, action = inspect_decision(
                        request.user,
                        case.pk,
                        value["version"],
                        row.pk,
                        value["key"],
                        value["reason"],
                    )
                    decision_form = DecisionForm(
                        initial={"key": uuid4(), "version": case.version, "read_id": action.pk}
                    )
                status = 200
            except PermissionDenied:
                return private(
                    HttpResponse(
                        "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado",
                        status=403,
                    )
                )
            except ValidationError as error:
                active.add_error(None, error)
                status = 409
    localize_form(form, request.LANGUAGE_CODE)
    localize_form(decision_form, request.LANGUAGE_CODE)
    return private(
        render(
            request,
            "safety/rights_access_field_review.html",
            {
                "case": case,
                "proposal": row,
                "form": form,
                "decision_form": decision_form,
                "body": body,
                "decision": decision,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )
