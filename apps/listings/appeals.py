from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core.agencies import person_queryset
from apps.core.models import Agency, Person
from apps.core.verification import locked_manager_person

from .models import Appeal, Listing, ModerationDecision, Revision
from .moderation import conflict_of_interest, reviewer_allowed


class AppealForm(forms.Form):
    explanation = forms.CharField(
        max_length=2000, label="Explicación / Explanation", widget=forms.Textarea
    )


class ReviewForm(forms.Form):
    result = forms.ChoiceField(
        choices=[
            ("", "Selecciona / Choose"),
            ("upheld", "Mantener decisión / Uphold decision"),
            ("reconsider", "Reabrir revisión / Reopen review"),
        ]
    )
    reason = forms.CharField(max_length=1000, label="Motivo / Reason", widget=forms.Textarea)


@login_required
@require_http_methods(["GET", "POST"])
def submit(request, decision_id):
    decision = get_object_or_404(
        ModerationDecision,
        pk=decision_id,
        revision__listing__person__in=person_queryset(request.user),
        outcome="rejected",
        revision__manager_version=F("revision__listing__person__manager_version"),
    )
    form = AppealForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            person = locked_manager_person(request.user, decision.revision.listing.person_id)
            Listing.objects.select_for_update().get(pk=decision.revision.listing_id)
            revision = Revision.objects.select_for_update().get(pk=decision.revision_id)
            if revision.manager_version != person.manager_version:
                return HttpResponse("Manager changed", status=409)
            Appeal.objects.get_or_create(
                decision=decision,
                defaults={"actor": request.user, "explanation": form.cleaned_data["explanation"]},
            )
        return redirect("appeal_submit", decision_id=decision.pk)
    return render(
        request,
        "listings/appeal.html",
        {
            "decision": decision,
            "appeal": Appeal.objects.filter(decision=decision).first(),
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
        "listings/appeal_queue.html",
        {"appeals": Appeal.objects.filter(status="open").order_by("created_at")[:100]},
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, appeal_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    appeal = get_object_or_404(Appeal, pk=appeal_id)
    person = appeal.decision.revision.listing.person
    if appeal.decision.reviewer_id == request.user.pk or conflict_of_interest(request.user, person):
        return HttpResponse("Independent reviewer required", status=403)
    form = ReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            if person.agency_id:
                Agency.objects.select_for_update().get(pk=person.agency_id)
            person = Person.objects.select_for_update().get(pk=person.pk)
            listing = Listing.objects.select_for_update().get(
                pk=appeal.decision.revision.listing_id
            )
            revision = Revision.objects.select_for_update().get(pk=appeal.decision.revision_id)
            appeal = Appeal.objects.select_for_update().get(pk=appeal.pk)
            if conflict_of_interest(request.user, person):
                return HttpResponse("Conflict of interest", status=403)
            if appeal.status != "open":
                return HttpResponse("Appeal already resolved", status=409)
            if form.cleaned_data["result"] == "reconsider" and (
                revision.status != "rejected"
                or revision.manager_version != person.manager_version
                or revision.submission.approved_base_id != listing.approved_revision_id
                or listing.revisions.filter(status__in=["draft", "processing", "pending"]).count()
                >= 3
                or revision.decisions.filter(outcome="rejected")
                .order_by("-created_at", "-pk")
                .first()
                .pk
                != appeal.decision_id
            ):
                form.add_error(
                    None,
                    "Estado de revisión cambiado; se requiere un borrador o reclamación vigente / Review state changed; a current draft or appeal is required",
                )
            else:
                if form.cleaned_data["result"] == "reconsider":
                    revision.status = "pending"
                    revision.edit_version += 1
                    revision.save(update_fields=["status", "edit_version", "updated_at"])
                    if not listing.approved_revision_id:
                        listing.status = "pending"
                        listing.save(update_fields=["status"])
                appeal.status, appeal.result = "resolved", form.cleaned_data["result"]
                appeal.reason, appeal.reviewer, appeal.resolved_at = (
                    form.cleaned_data["reason"],
                    request.user,
                    timezone.now(),
                )
                appeal.save(update_fields=["status", "result", "reason", "reviewer", "resolved_at"])
                return redirect("appeal_review", appeal_id=appeal.pk)
    return render(
        request,
        "listings/appeal_review.html",
        {"appeal": appeal, "form": form},
        status=400 if request.method == "POST" else 200,
    )
