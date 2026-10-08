"""Private proposal interface. Independent decision and consumption remain separate."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .erasure_execution import SUPPORTED
from .models import ErasurePlan, PurposeExceptionProposal, RightsRequest
from .purpose_exceptions import propose, record
from .rights import allowed
from .rights_scope import permitted
from .views import private


class ProposalForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    purposes = forms.MultipleChoiceField(
        choices=SUPPORTED,
        widget=forms.CheckboxSelectMultiple,
        label="Ámbitos revisados de la operación / Reviewed operation scopes",
    )
    basis = forms.CharField(
        min_length=20,
        max_length=1000,
        widget=forms.Textarea,
        label="Fundamento concreto minimizado / Minimized specific grounds",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        english = language == "en"
        labels = {
            "purposes": ("Ámbitos revisados de la operación", "Reviewed operation scopes"),
            "basis": ("Fundamento concreto minimizado", "Minimized specific grounds"),
            "reason": ("Motivo minimizado", "Minimized reason"),
        }
        captions = {
            "account": ("Identidad y acceso de cuenta", "Account identity and access"),
            "contact": ("Desafíos de teléfono", "Phone challenges"),
            "representation": ("Autorización e invitaciones", "Authorization and invitations"),
            "shared_contact_review": ("Asociación al teléfono", "Phone association"),
            "media": ("Archivos y huellas propios", "Own files and fingerprints"),
            "profile": ("Alias público", "Public alias"),
            "publication": ("Contenido de anuncio", "Listing content"),
            "authentication": ("Tokens, códigos y sesiones", "Tokens, codes and sessions"),
            "account_preferences": ("Favoritos propios", "Own favorites"),
            "transient_copy": ("Contenido de copias transitorias", "Transient copy contents"),
        }
        for name, pair in labels.items():
            self.fields[name].label = pair[english]
        self.fields["purposes"].choices = [
            (value, captions[value][english]) for value, _ in self.fields["purposes"].choices
        ]


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, plan_id):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + p)
        for p in ["execute_rights_request", "review_purpose_exception"]
    ):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case or not ErasurePlan.objects.filter(pk=plan_id, action__request=case).exists():
        raise Http404
    if not permitted(request.user, case):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ProposalForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid4(), "version": case.version},
    )
    if case.account_subject_id:
        form.fields["purposes"].choices = [
            row
            for row in form.fields["purposes"].choices
            if row[0] in {"account", "authentication", "account_preferences", "transient_copy"}
        ]
    proposal = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            proposal = propose(request.user, case_id, plan_id, **form.cleaned_data)
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
            form = ProposalForm(
                language=request.LANGUAGE_CODE, initial={"key": uuid4(), "version": case.version}
            )
            if case.account_subject_id:
                form.fields["purposes"].choices = [
                    row
                    for row in form.fields["purposes"].choices
                    if row[0]
                    in {"account", "authentication", "account_preferences", "transient_copy"}
                ]
    return private(
        render(
            request,
            "safety/purpose_exception_prepare.html",
            {"case": case, "plan_id": plan_id, "form": form, "proposal": proposal},
            status=status,
        )
    )


class ReviewForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consulta auditada / Audited inspection"),
            ("review", "Revisión independiente / Independent review"),
        ],
        label="Operación / Operation",
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )
    outcome = forms.ChoiceField(
        required=False,
        choices=[
            ("", "Selecciona solo para revisión / Select only for review"),
            ("approved", "Aprobar / Approve"),
            ("rejected", "Rechazar / Reject"),
        ],
        label="Resultado / Outcome",
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        english = language == "en"
        for name, pair in {
            "operation": ("Operación", "Operation"),
            "reason": ("Motivo minimizado", "Minimized reason"),
            "outcome": ("Resultado", "Outcome"),
        }.items():
            self.fields[name].label = pair[english]
        self.fields["operation"].choices = [
            ("inspect", "Audited inspection" if english else "Consulta auditada"),
            ("review", "Independent review" if english else "Revisión independiente"),
        ]
        self.fields["outcome"].choices = [
            ("", "Select only for review" if english else "Selecciona solo para revisión"),
            ("approved", "Approve" if english else "Aprobar"),
            ("rejected", "Reject" if english else "Rechazar"),
        ]


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def review(request, case_id, proposal_id):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + p)
        for p in ["execute_rights_request", "review_purpose_exception"]
    ):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    proposal = PurposeExceptionProposal.objects.filter(pk=proposal_id, action__request=case).first()
    if not case or not proposal:
        raise Http404
    if not permitted(request.user, case):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ReviewForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"key": uuid4(), "version": case.version},
    )
    body = decision = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            result, body = record(request.user, case.pk, proposal.pk, **form.cleaned_data)
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
            decision = result.outcome if form.cleaned_data["operation"] == "review" else None
            form = ReviewForm(
                language=request.LANGUAGE_CODE, initial={"key": uuid4(), "version": case.version}
            )
    return private(
        render(
            request,
            "safety/purpose_exception_review.html",
            {"case": case, "proposal": proposal, "form": form, "body": body, "decision": decision},
            status=status,
        )
    )
