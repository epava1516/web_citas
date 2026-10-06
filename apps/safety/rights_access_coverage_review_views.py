"""Private coverage review UI; GET never decrypts a coverage body."""

import json
from uuid import uuid4

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods

from .models import RightsAccessCoverage, RightsRequest
from .rights import allowed
from .rights_access_coverage_review import inspect, record
from .rights_access_response_review import authorize_reviewer
from .rights_access_response_views import DecisionForm, ReviewForm
from .views import private


@login_required
@sensitive_post_parameters()
@require_http_methods(["GET", "POST"])
def review(request, case_id, coverage_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        authorize_reviewer(request.user, case)
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    row = (
        RightsAccessCoverage.objects.filter(pk=coverage_id, request=case)
        .only("pk", "actor_id", "expires_at")
        .first()
    )
    if row is None:
        raise Http404
    if row.actor_id == request.user.pk:
        return private(HttpResponse("Independent reviewer required", status=403))
    if case.kind != "access" or case.status != "reviewing":
        return private(HttpResponse("Current access request required", status=409))
    form = ReviewForm(initial={"key": uuid4(), "version": case.version})
    decision_form = DecisionForm(initial={"key": uuid4(), "version": case.version})
    body = decision = None
    status = 200
    if request.method == "POST":
        deciding = request.POST.get("operation") == "review"
        active = DecisionForm(request.POST) if deciding else ReviewForm(request.POST)
        if deciding:
            decision_form = active
        else:
            form = active
        status = 400
        if active.is_valid():
            values = active.cleaned_data
            try:
                if deciding:
                    decision = record(
                        request.user,
                        case.pk,
                        values["version"],
                        row.pk,
                        values["read_id"],
                        values["key"],
                        values["reason"],
                        values["outcome"],
                    )
                else:
                    _, body, action = inspect(
                        request.user,
                        case.pk,
                        values["version"],
                        row.pk,
                        values["key"],
                        values["reason"],
                    )
                    decision_form = DecisionForm(
                        initial={"key": uuid4(), "version": case.version, "read_id": action.pk}
                    )
                status = 200
            except PermissionDenied:
                return private(HttpResponse("Forbidden", status=403))
            except ValidationError as error:
                active.add_error(None, error)
                status = 409
    return private(
        render(
            request,
            "safety/rights_access_coverage_review.html",
            {
                "case": case,
                "coverage": row,
                "form": form,
                "decision_form": decision_form,
                "body": body,
                "original_json": json.dumps(body["original"], ensure_ascii=False, indent=2)
                if body
                else None,
                "delivered_json": json.dumps(body["delivered"], ensure_ascii=False, indent=2)
                if body
                else None,
                "decision": decision,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )
