"""Private independent information review; GET never restores draft contents."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsCopyInformation, RightsRequest
from .rights import allowed
from .rights_copy_information_views import LABELS, FieldForm, LocalizedForm
from .rights_information_review import authorize, record
from .views import private


class ReviewForm(LocalizedForm):
    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, language=language, **kwargs)
        if language is not None:
            self.fields["operation"].label = "Operation" if language == "en" else "Operación"
            self.fields["outcome"].label = "Outcome" if language == "en" else "Resultado"

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[("inspect", "Consultar / Inspect"), ("review", "Decidir / Decide")]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[("", "—"), ("approved", "Aprobar / Approve"), ("rejected", "Rechazar / Reject")],
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review(request, case_id, information_id):
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
    information = RightsCopyInformation.objects.filter(pk=information_id, request=case).first()
    if not information:
        raise Http404
    if information.actor_id == request.user.pk:
        return private(
            HttpResponse(
                "Independent reviewer required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere revisión independiente",
                status=403,
            )
        )
    form = ReviewForm(
        request.POST if request.method == "POST" else None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid4(), "version": case.version},
    )
    body, decision = None, None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            result, body = record(request.user, case.pk, information.pk, **form.cleaned_data)
            decision = result if body is None else None
            form = ReviewForm(
                language=request.LANGUAGE_CODE, initial={"key": uuid4(), "version": case.version}
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
    reviewed_fields = []
    if body:
        english = (get_language() or "").startswith("en")
        display_form = FieldForm(language=request.LANGUAGE_CODE)
        statuses = dict(display_form.fields["status"].choices)
        sources = dict(display_form.fields["source"].choices)
        reviewed_fields = [
            {
                "label": LABELS[field][1 if english else 0],
                **item,
                "status_caption": statuses.get(item["status"], item["status"]),
                "source_caption": sources.get(item["source"], item["source"]),
            }
            for field, item in body["access"].items()
        ]
    return private(
        render(
            request,
            "safety/rights_information_review.html",
            {
                "case": case,
                "information_id": information.pk,
                "form": form,
                "body": body,
                "reviewed_fields": reviewed_fields,
                "decision": decision,
            },
            status=status,
        )
    )
