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

from . import erasure_final
from .models import ErasureExecution, RightsAction, RightsRequest
from .rights import allowed
from .rights_scope import permitted
from .views import private


class FinalForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    responses = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("prepare", "Preparar respuesta / Prepare response"),
            ("inspect", "Consultar borrador independiente / Inspect independent draft"),
            ("review", "Revisar respuesta / Review response"),
            ("issue", "Emitir respuesta / Issue response"),
        ]
    )
    execution = forms.UUIDField(required=False, label="Ejecución de supresión / Erasure execution")
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
            "prepare": ["execution", "reason", "text", "confirmed"],
            "inspect": ["draft", "purpose"],
            "review": ["draft", "read", "reason", "outcome"],
            "issue": ["review"],
        }
        for field in required.get(values.get("operation"), []):
            if not values.get(field):
                self.add_error(field, "Obligatorio para esta acción / Required for this action")
        return values


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def final(
    request,
    case_id,
    *,
    backend=erasure_final,
    kinds=("erase",),
    execution_model=ErasureExecution,
    form_class=FinalForm,
    template="safety/erasure_final.html",
    prefix="erase",
):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id, kind__in=kinds).first()
    if case is None:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    try:
        backend._actor(request.user, case, assigned=False)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    form = form_class(
        request.POST or None,
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
                backend.prepare(
                    *common,
                    values["execution"],
                    values["key"],
                    values["reason"],
                    values["text"],
                    values["confirmed"],
                )
            elif values["operation"] == "inspect":
                audited, material = backend.inspect(*common, values["draft"], values["purpose"])
                form = form_class(
                    initial={
                        **values,
                        "key": uuid.uuid4(),
                        "operation": "review",
                        "read": audited.pk,
                    }
                )
                status = 200
            elif values["operation"] == "review":
                backend.review(
                    *common,
                    values["draft"],
                    values["read"],
                    values["key"],
                    values["outcome"],
                    values["reason"],
                )
            else:
                backend.issue(*common, values["review"], values["key"])
            if values["operation"] != "inspect":
                return private(
                    redirect(
                        "erasure_final" if prefix == "erase" else "processing_final",
                        case_id=case.pk,
                    )
                )
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
            template,
            {
                "case": case,
                "form": form,
                "material": material,
                "actions": RightsAction.objects.filter(
                    request=case,
                    operation__in=[
                        prefix + "_final_draft",
                        prefix + "_final_read",
                        prefix + "_final_review",
                        prefix + "_final_issue",
                    ],
                )
                .order_by("-pk")
                .values("pk", "operation", "actor_id", "created_at")[:50],
                "executions": execution_model.objects.filter(action__request=case).values_list(
                    "pk", flat=True
                ),
            },
            status=status,
        )
    )
