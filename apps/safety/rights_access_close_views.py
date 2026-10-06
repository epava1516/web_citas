"""Private access closure; complete delivery evidence is mandatory."""

from uuid import uuid4

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from .models import RightsAccessResponseReview, RightsRequest
from .rights import allowed
from .rights_access_close import close
from .rights_access_response_views import ReviewForm
from .rights_copy_page_review import fresh_authority
from .views import private


class CloseForm(ReviewForm):
    response_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def close_response(request, case_id, review_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if case is None:
        raise Http404
    try:
        fresh_authority(request.user, case, request.user.session_version, request.user.mfa_version)
        if (
            not request.user.has_perm("safety.respond_rights_request")
            or case.assigned_to_id != request.user.pk
        ):
            raise PermissionDenied
    except PermissionDenied:
        return private(HttpResponse("Forbidden", status=403))
    decision = (
        RightsAccessResponseReview.objects.select_related("draft")
        .filter(
            pk=review_id,
            draft__request=case,
            draft__actor=request.user,
            outcome="approved",
        )
        .only("pk", "draft__case_version", "draft__response_version", "draft__export_id")
        .first()
    )
    if decision is None:
        raise Http404
    form = CloseForm(
        request.POST if request.method == "POST" else None,
        initial={
            "key": uuid4(),
            "version": decision.draft.case_version,
            "response_version": decision.draft.response_version,
        },
    )
    response = None
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            response = close(
                request.user,
                case.pk,
                values["version"],
                values["response_version"],
                decision.pk,
                values["key"],
                values["reason"],
            )
            case.refresh_from_db()
            status = 200
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/rights_access_close.html",
            {
                "case": case,
                "form": form,
                "decision": decision,
                "response": response,
                "english": request.LANGUAGE_CODE == "en",
            },
            status=status,
        )
    )
