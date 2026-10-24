from django import forms
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core.models import Agency, Person
from apps.mediafiles.models import Photo

from .history import is_rectification_history, rectification_history_ids
from .models import Listing, Revision
from .moderation import (
    conflict_of_interest,
    decide,
    publicly_visible,
    reviewer_allowed,
    unresolved_matches,
)
from .presentation import describe
from .profile_contract import CURRENT_CONTRACT
from .public_validation import DetailQuery, PublicationContext, _prepared_page_binding


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

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        index = 1 if language == "en" else 0
        labels = {"outcome": ("Resultado", "Outcome"), "reason": ("Motivo", "Reason")}
        for name, translations in labels.items():
            self.fields[name].label = translations[index]
        choices = {
            "outcome": [
                ("", ("Selecciona", "Choose")),
                ("approved", ("Aprobar", "Approve")),
                ("rejected", ("Rechazar", "Reject")),
            ]
        }
        for name, options in choices.items():
            self.fields[name].choices = [
                (value, translations[index]) for value, translations in options
            ]


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "listings/moderation_queue.html",
        {
            "revisions": Revision.objects.filter(status="pending", content_contract=CURRENT_CONTRACT)
            .exclude(pk__in=rectification_history_ids())
            .exclude(photos__rectification_upload__isnull=False)
            .order_by("submission__created_at")[:100]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, revision_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    revision = get_object_or_404(
        Revision.objects.select_related("listing__person__agency")
        .exclude(pk__in=rectification_history_ids())
        .exclude(photos__rectification_upload__isnull=False),
        pk=revision_id,
    )
    if conflict_of_interest(request.user, revision.listing.person):
        return HttpResponse("Conflict of interest", status=403)
    form = DecisionForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"edit_version": revision.edit_version},
    )
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
@transaction.atomic
def review_photo(request, photo_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    photo = get_object_or_404(
        Photo.objects.filter(
            Q(revision__status__in=["pending", "approved"])
            | Q(revision__status="rejected", revision__decisions__appeal__status="open")
        )
        .exclude(revision_id__in=rectification_history_ids())
        .distinct(),
        rectification_upload__isnull=True,
        pk=photo_id,
        removed_at__isnull=True,
    )
    initial_person = photo.revision.listing.person
    if initial_person.agency_id:
        Agency.objects.select_for_update().get(pk=initial_person.agency_id)
    person = Person.objects.select_for_update().get(pk=initial_person.pk)
    revision = Revision.objects.select_for_update().get(pk=photo.revision_id)
    if (
        person.agency_id != initial_person.agency_id
        or revision.manager_version != person.manager_version
        or is_rectification_history(revision)
    ):
        return HttpResponse("Photo unavailable", status=404)
    photo = get_object_or_404(
        Photo,
        pk=photo_id,
        revision=revision,
        removed_at__isnull=True,
        rectification_upload__isnull=True,
    )
    if conflict_of_interest(request.user, person):
        return HttpResponse("Conflict of interest", status=403)
    if photo.blob.status != "ready" or not photo.blob.derivative:
        return HttpResponse("Photo processing", status=409)
    response = FileResponse(photo.blob.derivative.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, no-store"
    return response


def public_detail(request, listing_id):
    # A savepoint cannot give an inherited READ COMMITTED transaction a common
    # snapshot. Keep its caller's original read path and isolation unchanged.
    if connection.in_atomic_block:
        return _native_public_detail(request, listing_id)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        with _prepared_page_binding(enabled=True):
            context = PublicationContext(
                DetailQuery(listing_id, timezone.now()), page_read=True, prepared_page=True,
            )
            if not context.rows:
                raise Http404
            listing = context.rows[0]
            if not publicly_visible(listing, context=context):
                raise Http404
        # Render eagerly in the same snapshot: prefetch/guard/presentation must
        # never combine committed versions that were individually ineligible.
        return _public_detail_response(request, listing)


def _native_public_detail(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related("person__agency", "approved_revision"), pk=listing_id
    )
    # Only the native read guard; render and every other caller retain their
    # connection settings. get_object_or_404 above already connected this thread.
    with _prepared_page_binding(enabled=True):
        if not publicly_visible(listing):
            raise Http404
    return _public_detail_response(request, listing)


def _public_detail_response(request, listing):
    from .seo import listing_metadata

    response = render(
        request,
        "listings/public_detail.html",
        {
            "listing": listing,
            "seo": listing_metadata(request, listing),
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
