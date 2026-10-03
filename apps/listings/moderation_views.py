from django import forms
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.mediafiles.models import Photo

from .models import Listing, Revision
from .moderation import (
    conflict_of_interest,
    decide,
    publicly_visible,
    reviewer_allowed,
    unresolved_matches,
)
from .presentation import describe


class DecisionForm(forms.Form):
    edit_version = forms.IntegerField(widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("", "Selecciona / Choose"),
            ("approved", "Aprobar / Approve"),
            ("rejected", "Rechazar / Reject"),
        ]
    )
    reason = forms.CharField(max_length=1000, widget=forms.Textarea, label="Motivo / Reason")


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "listings/moderation_queue.html",
        {
            "revisions": Revision.objects.filter(status="pending").order_by(
                "submission__created_at"
            )[:100]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, revision_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    revision = get_object_or_404(
        Revision.objects.select_related("listing__person__agency"), pk=revision_id
    )
    if conflict_of_interest(request.user, revision.listing.person):
        return HttpResponse("Conflict of interest", status=403)
    form = DecisionForm(request.POST or None, initial={"edit_version": revision.edit_version})
    if request.method == "POST" and form.is_valid():
        try:
            decide(
                request.user,
                revision.pk,
                form.cleaned_data["edit_version"],
                form.cleaned_data["outcome"],
                form.cleaned_data["reason"],
            )
            return redirect("moderation_review", revision_id=revision.pk)
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request,
        "listings/moderation_review.html",
        {
            "revision": revision,
            "form": form,
            "photos": revision.photos.filter(removed_at__isnull=True),
            "matches": unresolved_matches(revision),
            "decisions": revision.decisions.order_by("-created_at"),
        },
        status=400 if request.method == "POST" else 200,
    )


@login_required
def review_photo(request, photo_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    photo = get_object_or_404(
        Photo.objects.filter(
            Q(revision__status__in=["pending", "approved"])
            | Q(revision__status="rejected", revision__decisions__appeal__status="open")
        ).distinct(),
        pk=photo_id,
        removed_at__isnull=True,
    )
    if conflict_of_interest(request.user, photo.revision.listing.person):
        return HttpResponse("Conflict of interest", status=403)
    if photo.blob.status != "ready" or not photo.blob.derivative:
        return HttpResponse("Photo processing", status=409)
    response = FileResponse(photo.blob.derivative.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, no-store"
    return response


def public_detail(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related("person__agency", "approved_revision"), pk=listing_id
    )
    if not publicly_visible(listing):
        raise Http404
    response = render(
        request,
        "listings/public_detail.html",
        {
            "listing": listing,
            "revision": listing.approved_revision,
            "public": describe(listing, request.LANGUAGE_CODE),
            "report_target": signing.dumps(
                {"listing": str(listing.pk), "revision": str(listing.approved_revision_id)},
                salt="public-report-target-v1",
            ),
            "photos": listing.approved_revision.photos.filter(
                approved=True, removed_at__isnull=True
            ),
        },
    )
    response["Cache-Control"] = "no-store"
    return response


def public_photo(request, listing_id, photo_id):
    listing = get_object_or_404(Listing, pk=listing_id)
    if not publicly_visible(listing):
        raise Http404
    photo = get_object_or_404(
        Photo,
        pk=photo_id,
        revision=listing.approved_revision,
        approved=True,
        removed_at__isnull=True,
    )
    if photo.blob.status != "ready" or not photo.blob.derivative:
        raise Http404
    response = FileResponse(photo.blob.derivative.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "no-store"
    return response
