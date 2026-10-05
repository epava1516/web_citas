"""Private preparation interface; GET never discloses purpose snapshots."""

import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .erasure_inventory import canonical
from .models import RightsRequest
from .processing_plans import prepare, preview
from .rights import allowed, fingerprint
from .rights_scope import permitted
from .views import private


class PreparationForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("preview", "Consultar finalidades / Inspect purposes"),
            ("prepare", "Preparar decisiones / Prepare decisions"),
        ]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )
    source_digest = forms.CharField(required=False, max_length=64, widget=forms.HiddenInput)
    decisions = forms.JSONField(
        required=False, widget=forms.Textarea, label="Decisiones por finalidad / Purpose decisions"
    )

    def clean(self):
        values = super().clean()
        if values.get("operation") == "prepare" and (
            not values.get("source_digest") or not isinstance(values.get("decisions"), list)
        ):
            raise ValidationError(
                "Consulta finalidades y completa decisiones / Inspect purposes and complete decisions"
            )
        return values


@login_required
@sensitive_post_parameters("reason", "decisions")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def preparation(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    if case.kind not in {"restriction", "object"}:
        return private(HttpResponse("Unsupported request type", status=409))
    form = PreparationForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    manifest, plan, status = None, None, 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            if values["operation"] == "preview":
                manifest = preview(
                    request.user, case.pk, values["key"], values["version"], values["reason"]
                )
                draft = [
                    dict(
                        purpose=purpose,
                        operation="review",
                        basis="",
                        reason="",
                        scope="",
                        review_on="",
                    )
                    for purpose in sorted({item["purpose"] for item in manifest["entries"]})
                ]
                form = PreparationForm(
                    initial={
                        "key": uuid.uuid4(),
                        "version": case.version,
                        "operation": "prepare",
                        "reason": values["reason"],
                        "source_digest": fingerprint(canonical(manifest)),
                        "decisions": draft,
                    }
                )
            else:
                plan = prepare(
                    request.user,
                    case.pk,
                    values["key"],
                    values["version"],
                    values["reason"],
                    values["decisions"],
                    values["source_digest"],
                )
                form = PreparationForm(initial={"key": uuid.uuid4(), "version": case.version})
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/processing_prepare.html",
            {"case": case, "form": form, "manifest": manifest, "plan": plan},
            status=status,
        )
    )


class ReviewForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar plan / Inspect plan"),
            ("review", "Revisar plan / Review plan"),
        ]
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Selecciona / Select"),
            ("approved", "Aprobar / Approve"),
            ("rejected", "Rechazar / Reject"),
        ],
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review(request, case_id, plan_id):
    from .models import ProcessingPurposePlan
    from .processing_review import record

    if (
        not allowed(request)
        or not request.user.has_perm("safety.execute_rights_request")
        or not request.user.has_perm("safety.review_processing_plan")
    ):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if (
        not case
        or not ProcessingPurposePlan.objects.filter(pk=plan_id, action__request=case).exists()
    ):
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = ReviewForm(request.POST or None, initial={"key": uuid.uuid4(), "version": case.version})
    body, result, status = None, None, 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            result, body = record(request.user, case.pk, plan_id, **form.cleaned_data)
            form = ReviewForm(initial={"key": uuid.uuid4(), "version": case.version})
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/processing_review.html",
            {
                "case": case,
                "plan_id": plan_id,
                "form": form,
                "body": body,
                "reviewed": result if result and body is None else None,
            },
            status=status,
        )
    )


class ExecutionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    purposes = forms.MultipleChoiceField(
        choices=[("account_preferences", "Preferencias de cuenta / Account preferences")],
        widget=forms.CheckboxSelectMultiple,
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )
    confirmed = forms.BooleanField(
        label="Confirmo esta ejecución parcial / I confirm this partial execution"
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def execution(request, case_id, plan_id):
    from .models import ProcessingPurposePlan
    from .processing_execution import execute

    if not allowed(request) or not request.user.has_perm("safety.execute_rights_request"):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if (
        not case
        or not ProcessingPurposePlan.objects.filter(pk=plan_id, action__request=case).exists()
    ):
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = ExecutionForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": case.version}
    )
    result, status = None, 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            result = execute(request.user, case.pk, plan_id, **form.cleaned_data)
            case.refresh_from_db()
            form = ExecutionForm(initial={"key": uuid.uuid4(), "version": case.version})
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/processing_execute.html",
            {"case": case, "plan_id": plan_id, "form": form, "executed": result},
            status=status,
        )
    )
