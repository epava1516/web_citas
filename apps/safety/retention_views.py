"""Private retention follow-up calendar, independent of execution authorization."""

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

from .erasure_plans import LABELS
from .models import RetentionReview
from .retention_reviews import record
from .rights import allowed
from .rights_scope import permitted
from .views import private


def permitted_request(request):
    return allowed(request) and request.user.has_perm("safety.review_retention")


@login_required
@require_GET
def queue(request):
    if not permitted_request(request):
        return private(HttpResponse("Forbidden", status=403))
    attention = request.GET.get("attention", "due")
    if attention not in {"due", "soon", "all"}:
        return private(HttpResponse("Invalid attention", status=400))
    rows = RetentionReview.objects.select_related(
        "responsible",
        "plan__action__request__person",
        "plan__action__request__referenced_revision__publisher_acceptance",
    ).order_by("next_review_on", "pk")
    today = timezone.localdate()
    if attention == "due":
        rows = rows.filter(next_review_on__lte=today)
    elif attention == "soon":
        from datetime import timedelta

        rows = rows.filter(next_review_on__lte=today + timedelta(days=7))
    visible = []
    for row in rows:
        if permitted(request.user, row.plan.action.request):
            row.purpose_label = LABELS.get(row.purpose, row.purpose)
            visible.append(row)
    page = Paginator(visible, 50).get_page(request.GET.get("page"))
    return private(
        render(request, "safety/retention_queue.html", {"page": page, "attention": attention})
    )


class ReviewForm(forms.Form):
    history_before = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, widget=forms.HiddenInput
    )
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    case_version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("inspect", "Consultar finalidad / Inspect purpose"),
            ("follow_up", "Registrar revisión y seguimiento / Record review and follow-up"),
        ]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo minimizado / Minimized reason",
    )
    next_review_on = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
        label="Próxima revisión operativa, no ampliación de conservación / Next operational review, not retention extension",
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inspect(request, review_id):
    if not permitted_request(request):
        return private(HttpResponse("Forbidden", status=403))
    review = (
        RetentionReview.objects.select_related("plan__action__request").filter(pk=review_id).first()
    )
    if not review:
        raise Http404
    case = review.plan.action.request
    if not permitted(request.user, case):
        return private(HttpResponse("Forbidden", status=403))
    form = ReviewForm(
        request.POST or None,
        initial={"key": uuid.uuid4(), "version": review.version, "case_version": case.version},
    )
    decision = None
    recorded = False
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            _, decision = record(request.user, review.pk, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            recorded = form.cleaned_data["operation"] == "follow_up"
            status = 200
            review.refresh_from_db()
            # Fresh key/version allow following inspection with an independent review.
            form = ReviewForm(
                initial={
                    "key": uuid.uuid4(),
                    "version": review.version,
                    "case_version": case.version,
                    "operation": "follow_up" if decision else "inspect",
                }
            )
    return private(
        render(
            request,
            "safety/retention_review.html",
            {
                "form": form,
                "review": review,
                "case": case,
                "decision": decision,
                "recorded": recorded,
                "purpose_label": LABELS.get(review.purpose, review.purpose),
                "history_key": uuid.uuid4(),
            },
            status=status,
        )
    )
