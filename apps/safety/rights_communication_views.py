"""Private structured recipient assessment: GET opens metadata only."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from . import rights_communications as service
from .models import RightsAction, RightsRequest
from .recipient_assessment_views import Decisions, target_title
from .recipient_assessments import targets
from .rights import allowed
from .rights_scope import permitted
from .views import private


class CommunicationForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    responses = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("source", "Consultar destinatarios / Inspect recipients"),
            ("propose", "Proponer evaluación / Propose assessment"),
            ("inspect", "Consulta independiente / Independent inspection"),
            ("review", "Revisión independiente / Independent review"),
            ("deliver", "Crear notificaciones revisadas / Create reviewed notices"),
        ]
    )
    execution = forms.CharField(required=False, max_length=36, label="Ejecución / Execution")
    plan = forms.IntegerField(required=False, min_value=1, label="Evaluación / Assessment")
    review = forms.IntegerField(required=False, min_value=1, label="Revisión / Review")
    read = forms.IntegerField(required=False, min_value=1, label="Consulta / Audited read")
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
    outcome = forms.ChoiceField(
        required=False,
        choices=[
            ("approved", "Aprobar / Approve"),
            ("rejected", "Rechazar / Reject"),
        ],
    )

    def clean(self):
        values = super().clean()
        fields = {
            "source": ["execution", "purpose"],
            "propose": ["execution", "purpose"],
            "inspect": ["plan", "purpose"],
            "review": ["plan", "read", "reason", "outcome"],
            "deliver": ["review"],
        }
        for field in fields.get(values.get("operation"), []):
            if not values.get(field):
                self.add_error(field, "Obligatorio / Required")
        return values


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def communications(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(
        pk=case_id, kind__in=["erase", "restriction", "object"]
    ).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    backend = service.backend(case.pk)
    try:
        backend._actor(request.user, case, assigned=False)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    form = CommunicationForm(
        request.POST or None,
        initial={
            "key": uuid4(),
            "version": case.version,
            "responses": case.response_version,
        },
    )
    decisions = None
    inspected = None
    notice_preview = None
    status = 200 if request.method == "GET" else 400
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        common = (request.user, case.pk, values["version"], values["responses"])
        try:
            if values["operation"] == "source":
                _, source = service.inspect_source(*common, values["execution"], values["purpose"])
                notice_preview = source["notice_payload"]
                decisions = Decisions(
                    prefix="decisions",
                    initial=[{"target": token, "outcome": "pending"} for token in targets(source)],
                )
                for decision, (token, candidate) in zip(
                    decisions, targets(source).items(), strict=True
                ):
                    decision.target_title = target_title(
                        token, candidate, request.LANGUAGE_CODE == "en"
                    )
                form = CommunicationForm(initial={**values, "key": uuid4(), "operation": "propose"})
                status = 200
            elif values["operation"] == "propose":
                decisions = Decisions(request.POST, prefix="decisions")
                if decisions.is_valid():
                    rows = decisions.cleaned_data
                    mapped = {
                        row["target"]: {key: row[key] for key in ["outcome", "reason", "evidence"]}
                        for row in rows
                    }
                    if len(mapped) != len(rows):
                        raise ValidationError("Repeated recipient target / Destinatario repetido")
                    service.propose(
                        *common, values["execution"], values["key"], values["purpose"], mapped
                    )
                    return private(redirect("rights_communications", case_id=case.pk))
            elif values["operation"] == "inspect":
                audited, inspected = service.inspect(*common, values["plan"], values["purpose"])
                form = CommunicationForm(
                    initial={**values, "key": uuid4(), "operation": "review", "read": audited.pk}
                )
                status = 200
            elif values["operation"] == "review":
                service.review(
                    *common,
                    values["plan"],
                    values["read"],
                    values["key"],
                    values["outcome"],
                    values["reason"],
                )
                return private(redirect("rights_communications", case_id=case.pk))
            else:
                from .communication_notices import deliver

                deliver(*common, values["review"], values["key"])
                return private(redirect("rights_communications", case_id=case.pk))
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except (ValidationError, IntegrityError, ValueError) as error:
            form.add_error(
                None,
                error
                if isinstance(error, ValidationError)
                else "Acción incompatible / Conflicting action",
            )
            status = 409
    return private(
        render(
            request,
            "safety/rights_communications.html",
            {
                "case": case,
                "form": form,
                "decisions": decisions,
                "inspected": inspected,
                "notice_preview": notice_preview,
                "executions": backend._POLICY.execution_model.objects.filter(
                    action__request=case
                ).values_list("pk", flat=True),
                "actions": RightsAction.objects.filter(
                    request=case,
                    operation__in=[
                        "rights_comms_source",
                        "rights_comms_plan",
                        "rights_comms_read",
                        "rights_comms_review",
                    ],
                )
                .order_by("-pk")
                .values("pk", "operation", "created_at")[:50],
            },
            status=status,
        )
    )
