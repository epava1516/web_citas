"""One private screen for preparation, independent reading/review and issuance."""

import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from . import rectification_final
from .models import RightsAction, RightsRectificationRecipientReview, RightsRequest
from .rights import allowed
from .rights_scope import permitted
from .views import private


class FinalForm(forms.Form):
    def __init__(self, *args, language="es", **kwargs):
        self.language = language
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.label and " / " in field.label:
                spanish, english = field.label.split(" / ", 1)
                field.label = english if language == "en" else spanish
        self.fields["operation"].label = "Operation" if language == "en" else "Operación"
        self.fields["outcome"].label = "Outcome" if language == "en" else "Decisión"
        for name in ("operation", "outcome"):
            self.fields[name].choices = [
                (value, caption.split(" / ", 1)[language == "en"])
                for value, caption in self.fields[name].choices
            ]

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    responses = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("prepare", "Preparar respuesta / Prepare response"),
            ("inspect", "Consultar borrador independiente / Inspect independent draft"),
            ("review", "Revisar respuesta / Review response"),
            ("close", "Emitir y cerrar / Issue and close"),
        ]
    )
    recipient_review = forms.IntegerField(
        required=False, min_value=1, label="Revisión de destinatarios / Recipient review"
    )
    draft = forms.IntegerField(required=False, min_value=1, label="Borrador / Draft")
    read = forms.IntegerField(required=False, min_value=1, label="Consulta auditada / Audited read")
    review = forms.IntegerField(required=False, min_value=1, label="Revisión final / Final review")
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )
    reason = forms.CharField(
        required=False,
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivos / Grounds",
    )
    text = forms.CharField(
        required=False,
        min_length=50,
        max_length=4000,
        widget=forms.Textarea,
        label="Respuesta privada / Private response",
    )
    confirmed = forms.BooleanField(
        required=False,
        label="Respuesta revisada sin datos de terceros / Reviewed response without third-party data",
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[("approved", "Aprobar / Approve"), ("rejected", "Rechazar / Reject")],
    )

    def clean(self):
        values = super().clean()
        required = {
            "prepare": ["recipient_review", "reason", "text", "confirmed"],
            "inspect": ["draft", "purpose"],
            "review": ["draft", "read", "reason", "outcome"],
            "close": ["review"],
        }
        for field in required.get(values.get("operation"), []):
            if not values.get(field):
                self.add_error(
                    field,
                    "Required for this action"
                    if self.language == "en"
                    else "Obligatorio para esta acción",
                )
        return values


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def final(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id, kind="rectify").first()
    if case is None:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    try:
        rectification_final.actor(request.user, case, assigned=False)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    form = FinalForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={
            "key": uuid.uuid4(),
            "version": case.version,
            "responses": case.response_version,
        },
    )
    material = None
    status = 200 if request.method == "GET" else 400
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        common = (request.user, case.pk, values["version"], values["responses"])
        try:
            if values["operation"] == "prepare":
                rectification_final.prepare(
                    *common,
                    values["recipient_review"],
                    values["key"],
                    values["reason"],
                    values["text"],
                    values["confirmed"],
                )
            elif values["operation"] == "inspect":
                audited, material = rectification_final.inspect(
                    *common, values["draft"], values["purpose"]
                )
                form = FinalForm(
                    language=request.LANGUAGE_CODE,
                    initial={
                        **values,
                        "key": uuid.uuid4(),
                        "operation": "review",
                        "read": audited.pk,
                    },
                )
                status = 200
            elif values["operation"] == "review":
                rectification_final.review(
                    *common,
                    values["draft"],
                    values["read"],
                    values["key"],
                    values["outcome"],
                    values["reason"],
                )
            else:
                rectification_final.close(*common, values["review"], values["key"])
            if values["operation"] != "inspect":
                return private(redirect("rectification_final", case_id=case.pk))
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except (ValidationError, IntegrityError) as error:
            form.add_error(
                None,
                error
                if isinstance(error, ValidationError)
                else "Clave incompatible / Conflicting key",
            )
            status = 409
    # Metadata only: encrypted response/evidence is never opened on GET.
    return private(
        render(
            request,
            "safety/rectification_final.html",
            {
                "case": case,
                "form": form,
                "material": material,
                "actions": RightsAction.objects.filter(
                    request=case,
                    operation__in=[
                        "rectify_final_draft",
                        "rectify_final_read",
                        "rectify_final_review",
                        "rectify_final_close",
                    ],
                )
                .order_by("-pk")
                .values("pk", "operation", "actor_id", "created_at")[:50],
                "recipient_reviews": RightsRectificationRecipientReview.objects.filter(
                    action__request=case, outcome="accepted"
                ).values_list("pk", flat=True),
            },
            status=status,
        )
    )
