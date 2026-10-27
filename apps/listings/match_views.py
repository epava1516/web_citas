from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.mediafiles.models import Match, Photo

from .history import is_rectification_history, ordinary_matches
from .match_review import locked_pair, resolve
from .moderation import conflict_of_interest, reviewer_allowed


class ResolutionForm(forms.Form):
    review_version = forms.IntegerField(widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("", "Selecciona / Choose"),
            ("false_positive", "Falso positivo visual / Visual false positive"),
            ("distinct_people", "Personas distintas autorizadas / Distinct authorized people"),
            ("conflict", "Conflicto; restringir publicación / Conflict; restrict publication"),
        ]
    )
    reason = forms.CharField(max_length=1000, label="Motivo / Reason", widget=forms.Textarea)
    evidence_reference = forms.CharField(
        max_length=80, label="Referencia de revisión / Review reference"
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        english = language == "en"
        self.fields["outcome"].label = "Outcome" if english else "Resultado"
        self.fields["reason"].label = "Reason" if english else "Motivo"
        self.fields["evidence_reference"].label = (
            "Review reference" if english else "Referencia de revisión"
        )
        self.fields["outcome"].choices = [
            ("", "Choose" if english else "Selecciona"),
            ("false_positive", "Visual false positive" if english else "Falso positivo visual"),
            (
                "distinct_people",
                "Distinct authorized people" if english else "Personas distintas autorizadas",
            ),
            (
                "conflict",
                "Conflict; restrict publication"
                if english
                else "Conflicto; restringir publicación",
            ),
        ]


def allowed_match(request, match_id):
    match = get_object_or_404(
        Match.objects.select_related(
            "photo__revision__listing__person__agency",
            "candidate__revision__listing__person__agency",
        ),
        pk=match_id,
    )
    if (
        Match.objects.filter(pk=match.pk)
        .filter(
            Q(photo__rectification_upload__isnull=False)
            | Q(candidate__rectification_upload__isnull=False)
        )
        .exists()
    ):
        return None
    if (
        match.photo.revision.status == "rights-stage"
        or match.candidate.revision.status == "rights-stage"
    ):
        return None
    if any(is_rectification_history(photo.revision) for photo in [match.photo, match.candidate]):
        return None
    if any(
        conflict_of_interest(request.user, photo.revision.listing.person)
        for photo in [match.photo, match.candidate]
    ):
        return None
    return match


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    matches = ordinary_matches(
        Match.objects.filter(
            Q(resolved_at__isnull=True) | Q(decision="conflict"),
            photo__removed_at__isnull=True,
            candidate__removed_at__isnull=True,
        )
    ).order_by("created_at")[:100]
    return render(request, "listings/match_queue.html", {"matches": matches})


@login_required
@require_http_methods(["GET", "POST"])
def review(request, match_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    match = allowed_match(request, match_id)
    if not match:
        return HttpResponse("Conflict of interest", status=403)
    form = ResolutionForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={"review_version": match.review_version},
    )
    if request.method == "POST" and form.is_valid():
        try:
            resolve(
                request.user,
                match.pk,
                form.cleaned_data["review_version"],
                form.cleaned_data["outcome"],
                form.cleaned_data["reason"],
                form.cleaned_data["evidence_reference"],
            )
            return redirect("match_review", match_id=match.pk)
        except ValidationError as error:
            form.add_error(None, error)
    return render(
        request,
        "listings/match_review.html",
        {"match": match, "form": form, "resolutions": match.resolutions.order_by("-created_at")},
        status=400 if request.method == "POST" else 200,
    )


@login_required
@transaction.atomic
def image(request, match_id, side):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    match = allowed_match(request, match_id)
    if not match:
        return HttpResponse("Conflict of interest", status=403)
    if side not in ["photo", "candidate"]:
        return HttpResponse("Unknown side", status=404)
    try:
        _, people, _, _, _ = locked_pair(match_id)
    except ValidationError:
        return HttpResponse("Photo unavailable", status=404)
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    if any(conflict_of_interest(request.user, person) for person in people):
        return HttpResponse("Forbidden", status=403)
    photo = Photo.objects.select_related("blob").get(pk=getattr(match, side).pk)
    if photo.removed_at or photo.blob.status != "ready" or not photo.blob.derivative:
        return HttpResponse("Photo unavailable", status=404)
    response = FileResponse(photo.blob.derivative.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, no-store"
    return response
