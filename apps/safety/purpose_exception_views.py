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
from .models import ErasurePlan, RightsRequest
from .purpose_exceptions import propose
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


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def prepare(request, case_id, plan_id):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + p)
        for p in ["execute_rights_request", "review_purpose_exception"]
    ):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case or not ErasurePlan.objects.filter(pk=plan_id, action__request=case).exists():
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = ProposalForm(request.POST or None, initial={"key": uuid4(), "version": case.version})
    if case.account_subject_id:
        form.fields["purposes"].choices = [
            row
            for row in SUPPORTED
            if row[0] in {"account", "authentication", "account_preferences", "transient_copy"}
        ]
    proposal = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            proposal = propose(request.user, case_id, plan_id, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            status = 200
            form = ProposalForm(initial={"key": uuid4(), "version": case.version})
            if case.account_subject_id:
                form.fields["purposes"].choices = [
                    row
                    for row in SUPPORTED
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
