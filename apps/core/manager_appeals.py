from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.listings.appeals import AppealForm
from apps.listings.moderation import reviewer_allowed

from .agencies import person_queryset
from .manager_review import transfer_conflict
from .models import Agency, ManagerAppeal, ManagerReview, Person


class ReviewForm(forms.Form):
    result = forms.ChoiceField(
        choices=[
            ("", "Selecciona / Choose"),
            ("upheld", "Mantener rechazo / Uphold rejection"),
            ("approved", "Aprobar gestor / Approve manager"),
        ]
    )
    reason = forms.CharField(max_length=1000, widget=forms.Textarea, label="Motivo / Reason")


def entitled(user, person):
    return person.subject_id == user.pk or person_queryset(user).filter(pk=person.pk).exists()


@login_required
@require_http_methods(["GET", "POST"])
def submit(request, decision_id):
    decision = get_object_or_404(
        ManagerReview.objects.filter(
            Q(person__subject=request.user) | Q(person__in=person_queryset(request.user))
        ),
        pk=decision_id,
        outcome="failed",
        manager_version=F("person__manager_version"),
    )
    form = AppealForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if decision.person.agency_id:
                Agency.objects.select_for_update().get(pk=decision.person.agency_id)
            person = Person.objects.select_for_update().get(pk=decision.person_id)
            if (
                not entitled(request.user, person)
                or decision.manager_version != person.manager_version
            ):
                return HttpResponse("Manager changed", status=409)
            ManagerAppeal.objects.get_or_create(
                decision=decision,
                defaults={"actor": request.user, "explanation": form.cleaned_data["explanation"]},
            )
        return redirect("manager_appeal_submit", decision_id=decision.pk)
    return render(
        request,
        "core/manager_appeal.html",
        {
            "decision": decision,
            "appeal": ManagerAppeal.objects.filter(decision=decision).first(),
            "form": form,
        },
        status=400 if request.method == "POST" else 200,
    )


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "core/manager_appeal_queue.html",
        {
            "appeals": ManagerAppeal.objects.filter(status="open")
            .select_related("decision__person")
            .order_by("created_at")[:100]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, appeal_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    appeal = get_object_or_404(ManagerAppeal, pk=appeal_id)
    person = appeal.decision.person
    if appeal.decision.reviewer_id == request.user.pk or transfer_conflict(request.user, person):
        return HttpResponse("Independent reviewer required", status=403)
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if person.agency_id:
                Agency.objects.select_for_update().get(pk=person.agency_id)
            person = Person.objects.select_for_update().get(pk=person.pk)
            appeal = ManagerAppeal.objects.select_for_update().get(pk=appeal.pk)
            if transfer_conflict(request.user, person):
                return HttpResponse("Conflict of interest", status=403)
            if appeal.status != "open":
                return HttpResponse("Appeal already resolved", status=409)
            if form.cleaned_data["result"] == "approved" and (
                appeal.decision.manager_version != person.manager_version
                or person.manager_review_status != "failed"
                or not person.subject_id
                or person.age_status != "passed"
                or person.consent_revoked_at
                or person.consent_version != person.manager_version
                or (person.agency_id and person.agency.verification_status != "passed")
            ):
                form.add_error(
                    None, "Estado o autorizaciones cambiados / State or authorizations changed"
                )
            else:
                if form.cleaned_data["result"] == "approved":
                    person.manager_review_status = "approved"
                    person.save(update_fields=["manager_review_status"])
                appeal.status = "resolved"
                appeal.result = form.cleaned_data["result"]
                appeal.reason = form.cleaned_data["reason"]
                appeal.reviewer = request.user
                appeal.resolved_at = timezone.now()
                appeal.save(update_fields=["status", "result", "reason", "reviewer", "resolved_at"])
                return redirect("manager_appeal_review", appeal_id=appeal.pk)
    return render(
        request,
        "core/manager_appeal_review.html",
        {"appeal": appeal, "form": form},
        status=400 if request.method == "POST" else 200,
    )
