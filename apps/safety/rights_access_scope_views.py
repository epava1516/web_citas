"""Audited, paginated scope metadata. GET does not recover inventory bodies."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsRequest
from .rights import allowed
from .rights_access_response_review import authorize_reviewer
from .rights_access_response_views import ReviewForm
from .rights_access_scope_store import inspect
from .views import private


class ScopeForm(ReviewForm):
    response_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    page = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inventory(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        authorize_reviewer(request.user, case)
        if case.assigned_to_id != request.user.pk:
            raise PermissionDenied
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    if case.kind != "access" or case.status != "reviewing":
        return private(HttpResponse("Current access request required", status=409))
    form = ScopeForm(
        initial={"key": uuid4(), "version": case.version, "response_version": case.response_version}
    )
    row = manifest = page = None
    status = 200
    if request.method == "POST":
        form = ScopeForm(request.POST)
        status = 400
        if form.is_valid():
            values = form.cleaned_data
            try:
                row, manifest = inspect(
                    request.user,
                    case.pk,
                    values["version"],
                    values["response_version"],
                    values["key"],
                    values["reason"],
                )
                records = [
                    {
                        "model": entry["model"],
                        "purpose": entry["purpose"],
                        "count": entry["count"],
                        "record": record,
                    }
                    for entry in manifest["entries"]
                    for record in (entry["records"] or [None])
                ]
                page = Paginator(records, 25).get_page(values["page"] or 1)
                status = 200
            except PermissionDenied:
                return private(HttpResponse("Forbidden", status=403))
            except ValidationError as error:
                form.add_error(None, error)
                status = 409
    return private(
        render(
            request,
            "safety/rights_access_scope.html",
            {
                "case": case,
                "form": form,
                "inventory": row,
                "manifest": manifest,
                "entries": page,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )
