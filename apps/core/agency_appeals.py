from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.listings.appeals import AppealForm, ReviewForm

from .models import Agency, AgencyAppeal, AgencyMember, AgencyReview
from .organization_review import reviewer_allowed


def latest_decision(agency):
    return agency.reviews.order_by("-created_at", "-pk").first()


def conflict(user, agency):
    return (
        agency.owner_id == user.pk or AgencyMember.objects.filter(agency=agency, user=user).exists()
    )


@login_required
@require_http_methods(["GET", "POST"])
def submit(request, decision_id):
    decision = get_object_or_404(
        AgencyReview, pk=decision_id, agency__owner=request.user, outcome="failed"
    )
    if (
        latest_decision(decision.agency).pk != decision.pk
        and not AgencyAppeal.objects.filter(decision=decision).exists()
    ):
        return HttpResponse("Decision obsolete", status=404)
    form = AppealForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            agency = Agency.objects.select_for_update().get(pk=decision.agency_id)
            if agency.owner_id != request.user.pk:
                return HttpResponse("Decision changed", status=409)
            existing = AgencyAppeal.objects.filter(decision=decision).first()
            if not existing and (
                agency.verification_status != "failed" or latest_decision(agency).pk != decision.pk
            ):
                return HttpResponse("Organization changed", status=409)
            AgencyAppeal.objects.get_or_create(
                decision=decision,
                defaults={
                    "actor": request.user,
                    "review_version": agency.review_version,
                    "explanation": form.cleaned_data["explanation"],
                },
            )
        return redirect("agency_appeal_submit", decision_id=decision.pk)
    return render(
        request,
        "core/agency_appeal.html",
        {
            "decision": decision,
            "appeal": AgencyAppeal.objects.filter(decision=decision).first(),
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
        "core/agency_appeal_queue.html",
        {
            "appeals": AgencyAppeal.objects.filter(status="open")
            .select_related("decision__agency")
            .order_by("created_at")[:100]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, appeal_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    appeal = get_object_or_404(AgencyAppeal, pk=appeal_id)
    agency = appeal.decision.agency
    if appeal.decision.reviewer_id == request.user.pk or conflict(request.user, agency):
        return HttpResponse("Independent reviewer required", status=403)
    form = ReviewForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            agency = Agency.objects.select_for_update().get(pk=agency.pk)
            appeal = AgencyAppeal.objects.select_for_update().get(pk=appeal.pk)
            if conflict(request.user, agency):
                return HttpResponse("Conflict of interest", status=403)
            if appeal.status != "open":
                return HttpResponse("Appeal already resolved", status=409)
            if form.cleaned_data["result"] == "reconsider" and (
                agency.verification_status != "failed"
                or agency.review_version != appeal.review_version
                or latest_decision(agency).pk != appeal.decision_id
            ):
                form.add_error(
                    None, "Comprobación de agencia cambiada / Organization review changed"
                )
            else:
                if form.cleaned_data["result"] == "reconsider":
                    agency.verification_status = "pending"
                    agency.verification_procedure = ""
                    agency.review_version += 1
                    agency.save(
                        update_fields=[
                            "verification_status",
                            "verification_procedure",
                            "review_version",
                        ]
                    )
                appeal.status = "resolved"
                appeal.result = form.cleaned_data["result"]
                appeal.reason = form.cleaned_data["reason"]
                appeal.reviewer = request.user
                appeal.resolved_at = timezone.now()
                appeal.save(update_fields=["status", "result", "reason", "reviewer", "resolved_at"])
                return redirect("agency_appeal_review", appeal_id=appeal.pk)
    return render(
        request,
        "core/agency_appeal_review.html",
        {"appeal": appeal, "form": form},
        status=400 if request.method == "POST" else 200,
    )
