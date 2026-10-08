"""Private independent assessment review; contents are available only after audited POST."""

import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsRectificationRecipientAssessment, RightsRequest
from .recipient_assessment_views import target_title
from .recipient_assessments import targets
from .recipient_review import inspect, permission, review
from .rectification_presentation import caption
from .rights import allowed
from .rights_scope import permitted
from .views import private


class ReviewForm(forms.Form):
    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.label = caption(field.label, language)
            if hasattr(field, "choices"):
                field.choices = [
                    (value, caption(label, language)) for value, label in field.choices
                ]
        self.fields["operation"].label = "Operation" if language == "en" else "Operación"
        self.fields["outcome"].label = "Outcome" if language == "en" else "Resultado"

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(widget=forms.HiddenInput, min_value=1)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar decisiones / Inspect decisions"),
            ("review", "Registrar revisión / Record review"),
        ]
    )
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[
            ("accepted", "Aceptar evaluación / Accept assessment"),
            ("rejected", "Rechazar evaluación / Reject assessment"),
        ],
    )
    reason = forms.CharField(
        required=False,
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivos de revisión / Review grounds",
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, assessment_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    try:
        permission(request.user)
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    assessment = (
        RightsRectificationRecipientAssessment.objects.filter(
            pk=assessment_id, action__request=case
        )
        .select_related("action")
        .first()
    )
    if not case or not assessment:
        raise Http404
    if not permitted(request.user, case) or assessment.action.actor_id == request.user.pk:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ReviewForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid.uuid4(), "version": case.version},
    )
    rows = None
    status = 200 if request.method == "GET" else 400
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            if values["operation"] == "inspect":
                data, decisions = inspect(
                    request.user, case_id, assessment_id, values["version"], values["purpose"]
                )
                rows = [
                    {
                        "title": target_title(token, candidate, request.LANGUAGE_CODE == "en"),
                        **decisions[token],
                    }
                    for token, candidate in targets(data).items()
                ]
                status = 200
            else:
                review(
                    request.user,
                    case_id,
                    assessment_id,
                    values["key"],
                    values["version"],
                    values["outcome"],
                    values["reason"],
                )
                return private(redirect("rights_inspect", case_id=case.pk))
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(request, "safety/recipient_review.html", {"form": form, "rows": rows}, status=status)
    )
