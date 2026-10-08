"""Private, audited inspection and notification proposal; restriction stays active."""

import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from .models import PurposeRestriction, RightsRequest
from .purpose_release import execute, inspect, propose
from .rights import allowed
from .rights_scope import permitted
from .views import private


class ReleaseForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar medida / Inspect restriction"),
            ("propose", "Proponer y comunicar / Propose and notify"),
            ("execute", "Ejecutar propuesta recibida / Execute received proposal"),
        ]
    )
    ground = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Selecciona / Select"),
            (
                "restriction_resolved",
                "Fundamento de limitación resuelto / Restriction ground resolved",
            ),
            ("resume_requested", "Nueva solicitud revisada / Reviewed new request"),
        ],
    )
    resume_message_id = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=9223372036854775807,
        label="Mensaje del sujeto para reanudar / Subject message requesting resumption",
    )
    proposal_id = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=9223372036854775807,
        label="Propuesta recibida / Received proposal",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo interno minimizado / Minimized internal reason",
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.language = language
        english = language == "en"
        labels = {
            "operation": ("Operación", "Operation"),
            "ground": ("Fundamento", "Ground"),
            "resume_message_id": (
                "Mensaje del sujeto para reanudar",
                "Subject message requesting resumption",
            ),
            "proposal_id": ("Propuesta recibida", "Received proposal"),
            "reason": ("Motivo interno minimizado", "Minimized internal reason"),
        }
        captions = {
            "operation": {
                "inspect": ("Consultar medida", "Inspect restriction"),
                "propose": ("Proponer y comunicar", "Propose and notify"),
                "execute": ("Ejecutar propuesta recibida", "Execute received proposal"),
                "follow_up": ("Registrar seguimiento", "Record follow-up"),
                "history": ("Consultar historial", "Inspect history"),
            },
            "ground": {
                "": ("Selecciona", "Select"),
                "restriction_resolved": (
                    "Fundamento de limitación resuelto",
                    "Restriction ground resolved",
                ),
                "resume_requested": ("Nueva solicitud revisada", "Reviewed new request"),
            },
        }
        for name, pair in labels.items():
            self.fields[name].label = pair[english]
        for name, translated in captions.items():
            self.fields[name].choices = [
                (value, translated[value][english]) for value, _ in self.fields[name].choices
            ]


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def release(request, case_id, restriction_id):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + p)
        for p in ["execute_rights_request", "release_purpose_restriction", "respond_rights_request"]
    ):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    restriction = PurposeRestriction.objects.filter(
        pk=restriction_id, execution__action__request=case
    ).first()
    if not case or not restriction:
        raise Http404
    if (
        not permitted(request.user, case)
        or request.user.pk == restriction.execution.action.actor_id
    ):
        return private(HttpResponse("Forbidden", status=403))
    proposal = restriction.release_proposals.order_by("-pk").first()
    form = ReleaseForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={
            "key": uuid.uuid4(),
            "version": case.version,
            "proposal_id": proposal.pk if proposal else None,
        },
    )
    body, status = None, 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            args = (
                request.user,
                case.pk,
                restriction.pk,
                values["key"],
                values["version"],
                values["reason"],
            )
            if values["operation"] == "inspect":
                _, body = inspect(*args)
            elif values["operation"] == "propose":
                proposal = propose(*args, values["ground"], values["resume_message_id"])
            else:
                proposal = execute(
                    request.user,
                    case.pk,
                    restriction.pk,
                    values["key"],
                    values["version"],
                    values["proposal_id"],
                    values["reason"],
                )
            case.refresh_from_db()
            form = ReleaseForm(
                language=request.LANGUAGE_CODE,
                initial={
                    "key": uuid.uuid4(),
                    "version": case.version,
                    "proposal_id": proposal.pk if proposal else None,
                },
            )
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/purpose_release.html",
            {
                "case": case,
                "restriction": restriction,
                "form": form,
                "body": body,
                "proposal": proposal,
            },
            status=status,
        )
    )


class QueueForm(forms.Form):
    state = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Activas / Active"),
            ("active", "Activas / Active"),
            ("released", "Levantadas / Released"),
        ],
    )
    due = forms.ChoiceField(
        required=False,
        choices=[("", "Todas las fechas / All dates"), ("due", "Revisión vencida / Review due")],
    )
    purpose = forms.ChoiceField(
        required=False,
        choices=[("", "Todas / All"), ("account_preferences", "Preferencias / Preferences")],
    )


@login_required
@require_GET
def queue(request, case_id):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + name)
        for name in [
            "execute_rights_request",
            "release_purpose_restriction",
            "respond_rights_request",
        ]
    ):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = QueueForm(request.GET)
    measures = PurposeRestriction.objects.none()
    status = 200
    if form.is_valid():
        measures = (
            PurposeRestriction.objects.filter(execution__action__request=case)
            .exclude(execution__action__actor=request.user)
            .filter(active=form.cleaned_data["state"] != "released")
        )
        if form.cleaned_data["due"]:
            measures = measures.filter(review_on__lte=timezone.localdate())
        if form.cleaned_data["purpose"]:
            measures = measures.filter(purpose=form.cleaned_data["purpose"])
        measures = measures.order_by("review_on", "pk")
    else:
        status = 400
    query = request.GET.copy()
    query.pop("page", None)
    return private(
        render(
            request,
            "safety/purpose_restriction_queue.html",
            {
                "case": case,
                "form": form,
                "measures": Paginator(measures, 25).get_page(request.GET.get("page")),
                "filters": query.urlencode(),
            },
            status=status,
        )
    )
