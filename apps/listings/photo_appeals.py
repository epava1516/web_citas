from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.mediafiles.models import MatchResolution, PhotoAppeal

from .appeals import ReviewForm
from .match_review import locked_pair
from .moderation import conflict_of_interest, reviewer_allowed


@login_required
def queue(request):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    return render(
        request,
        "listings/photo_appeal_queue.html",
        {
            "appeals": PhotoAppeal.objects.filter(status="open")
            .select_related("restriction__person")
            .order_by("created_at")[:100]
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def review(request, appeal_id):
    if not reviewer_allowed(request):
        return HttpResponse("Forbidden", status=403)
    appeal = get_object_or_404(PhotoAppeal, pk=appeal_id)
    match = appeal.restriction.decision.match
    people = [match.photo.revision.listing.person, match.candidate.revision.listing.person]
    if appeal.restriction.decision.reviewer_id == request.user.pk or any(
        conflict_of_interest(request.user, p) for p in people
    ):
        return HttpResponse("Independent reviewer required", status=403)
    form = ReviewForm(request.POST or None)
    form.fields[
        "reason"
    ].label = (
        "Motivo para la persona; sin datos ajenos / Reason for the person; no third-party data"
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            try:
                _, people, _, matches, current = locked_pair(match.pk)
            except ValidationError:
                return HttpResponse("Manager changed", status=409)
            appeal = PhotoAppeal.objects.select_for_update().get(pk=appeal.pk)
            if any(conflict_of_interest(request.user, p) for p in people):
                return HttpResponse("Conflict of interest", status=403)
            if appeal.status != "open":
                return HttpResponse("Appeal already resolved", status=409)
            person = next(p for p in people if p.pk == appeal.restriction.person_id)
            if form.cleaned_data["result"] == "reconsider" and (
                appeal.restriction.manager_version != person.manager_version
                or current.review_version != appeal.review_version
                or current.decision != "conflict"
                or current.resolutions.order_by("-created_at", "-pk").first().pk
                != appeal.restriction.decision_id
                or current.photo.removed_at
                or current.candidate.removed_at
            ):
                form.add_error(None, "Restricción cambiada / Restriction changed")
            else:
                if form.cleaned_data["result"] == "reconsider":
                    for pair_match in matches:
                        MatchResolution.objects.create(
                            match=pair_match,
                            reviewer=request.user,
                            outcome="reopened",
                            reason=form.cleaned_data["reason"],
                            evidence_reference=f"photo-appeal:{appeal.pk}",
                        )
                        pair_match.decision = ""
                        pair_match.resolved_at = None
                        pair_match.review_version += 1
                        pair_match.save(update_fields=["decision", "resolved_at", "review_version"])
                appeal.status = "resolved"
                appeal.result = form.cleaned_data["result"]
                appeal.reason = form.cleaned_data["reason"]
                appeal.reviewer = request.user
                appeal.resolved_at = timezone.now()
                appeal.save(update_fields=["status", "result", "reason", "reviewer", "resolved_at"])
                return redirect("photo_appeal_review", appeal_id=appeal.pk)
    return render(
        request,
        "listings/photo_appeal_review.html",
        {"appeal": appeal, "form": form},
        status=400 if request.method == "POST" else 200,
    )
