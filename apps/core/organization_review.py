from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Agency, AgencyMember, AgencyReview


class ReviewForm(forms.Form):
    review_version = forms.IntegerField(widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[("passed", "Aprobar / Approve"), ("failed", "Rechazar / Reject")]
    )
    reason = forms.CharField(max_length=500, label="Motivo / Reason", widget=forms.Textarea)
    evidence_reference = forms.CharField(
        max_length=80,
        label="Referencia sintética de comprobación / Synthetic verification reference",
    )


def reviewer_allowed(request):
    return bool(
        request.user.has_perm("core.review_agency")
        and request.user.mfa_enabled
        and request.session.get("mfa_version") == request.user.mfa_version
    )


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "core/organization_queue.html",
        {
            "agencies": Agency.objects.filter(verification_status="pending").order_by("created_at")[
                :100
            ]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, agency_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    agency = get_object_or_404(Agency, pk=agency_id)
    if (
        agency.owner_id == request.user.pk
        or AgencyMember.objects.filter(agency=agency, user=request.user, active=True).exists()
    ):
        return HttpResponse("Cannot review your own organization", status=403)
    form = ReviewForm(request.POST or None, initial={"review_version": agency.review_version})
    if request.method == "POST" and form.is_valid():
        # A local workflow is not evidence that a real organization was checked.
        if settings.PRODUCTION or settings.VERIFICATION_PROVIDER != "simulator":
            return HttpResponse("Organization verification adapter not integrated", status=503)
        with transaction.atomic():
            agency = Agency.objects.select_for_update().get(pk=agency.pk)
            if (
                agency.owner_id == request.user.pk
                or AgencyMember.objects.filter(
                    agency=agency, user=request.user, active=True
                ).exists()
            ):
                return HttpResponse("Conflict of interest", status=403)
            if (
                agency.verification_status != "pending"
                or agency.review_version != form.cleaned_data["review_version"]
            ):
                return HttpResponse("Organization review changed; reload", status=409)
            AgencyReview.objects.create(
                agency=agency,
                reviewer=request.user,
                outcome=form.cleaned_data["outcome"],
                reason=form.cleaned_data["reason"],
                evidence_reference=form.cleaned_data["evidence_reference"],
                procedure="simulator-v1",
            )
            agency.verification_status = form.cleaned_data["outcome"]
            agency.verification_procedure = "simulator-v1"
            agency.review_version += 1
            agency.save(
                update_fields=["verification_status", "verification_procedure", "review_version"]
            )
        return redirect("organization_review", agency_id=agency.pk)
    return render(
        request,
        "core/organization_review.html",
        {"agency": agency, "form": form, "reviews": agency.reviews.order_by("-created_at")[:10]},
        status=400 if request.method == "POST" else 200,
    )
