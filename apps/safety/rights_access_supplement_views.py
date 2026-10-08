"""Private staff preview of materialized supplemental access data."""

import json
from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsAccessFieldDecision, RightsAccessScopeInventory, RightsRequest
from .rights import allowed
from .rights_access_field_decision_views import localize_form
from .rights_access_response_review import authorize_reviewer
from .rights_access_response_views import ReviewForm
from .rights_access_supplement import prepare
from .views import private


class SupplementForm(ReviewForm):
    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.language = language
        localize_form(self, language)

    response_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    decisions = forms.CharField(
        widget=forms.Textarea,
        max_length=20000,
        label="IDs de decisiones aprobadas / Approved decision IDs",
    )

    def clean_decisions(self):
        try:
            values = [int(item.strip()) for item in self.cleaned_data["decisions"].split(",")]
        except ValueError:
            raise forms.ValidationError(
                "IDs separados por comas / Comma-separated IDs"
                if self.language is None
                else ("Comma-separated IDs" if self.language == "en" else "IDs separados por comas")
            )
        if any(item < 1 for item in values) or len(set(values)) != len(values):
            raise forms.ValidationError(
                "IDs únicos positivos / Unique positive IDs"
                if self.language is None
                else ("Unique positive IDs" if self.language == "en" else "IDs únicos positivos")
            )
        return values


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def preview(request, case_id, inventory_id):
    if not allowed(request):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        authorize_reviewer(request.user, case)
        if case.assigned_to_id != request.user.pk:
            raise PermissionDenied
    except PermissionDenied:
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    inventory = (
        RightsAccessScopeInventory.objects.filter(pk=inventory_id, request=case, actor=request.user)
        .only("pk")
        .first()
    )
    if inventory is None:
        raise Http404
    if case.kind != "access" or case.status != "reviewing":
        return private(
            HttpResponse(
                "Current access request required"
                if request.LANGUAGE_CODE == "en"
                else "Se requiere una solicitud de acceso vigente",
                status=409,
            )
        )
    candidates = Paginator(
        RightsAccessFieldDecision.objects.filter(
            inventory=inventory,
            outcome="approved",
            purged_at__isnull=True,
            expires_at__gt=timezone.now(),
        )
        .only("pk")
        .order_by("pk"),
        50,
    ).get_page(request.GET.get("page"))
    form = SupplementForm(
        language=request.LANGUAGE_CODE,
        initial={
            "key": uuid4(),
            "version": case.version,
            "response_version": case.response_version,
        },
    )
    body = None
    status = 200
    if request.method == "POST":
        form = SupplementForm(request.POST, language=request.LANGUAGE_CODE)
        status = 400
        if form.is_valid():
            value = form.cleaned_data
            try:
                body, _ = prepare(
                    request.user,
                    case.pk,
                    value["version"],
                    value["response_version"],
                    inventory.pk,
                    value["decisions"],
                    value["key"],
                    value["reason"],
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
                form.add_error(None, error)
                status = 409
    return private(
        render(
            request,
            "safety/rights_access_supplement.html",
            {
                "case": case,
                "inventory": inventory,
                "form": form,
                "candidates": candidates,
                "body": body,
                "copy_json": json.dumps(body["fields"], ensure_ascii=False, indent=2)
                if body
                else None,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )
