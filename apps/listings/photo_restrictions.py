from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from apps.core.agencies import person_queryset
from apps.mediafiles.models import Match, PhotoAppeal, PhotoRestriction

from .appeals import AppealForm
from .history import ordinary_matches
from .match_review import locked_pair


@login_required
@require_http_methods(["GET", "POST"])
def detail(request, restriction_id):
    restriction = get_object_or_404(
        PhotoRestriction.objects.filter(
            Q(person__subject=request.user) | Q(person__in=person_queryset(request.user)),
            decision__match__in=ordinary_matches(Match.objects.all()),
        ),
        pk=restriction_id,
        manager_version=F("person__manager_version"),
    )
    current = restriction.decision.match
    active = (
        current.decision == "conflict"
        and current.resolutions.order_by("-created_at", "-pk").first().pk == restriction.decision_id
        and not current.photo.removed_at
        and not current.candidate.removed_at
    )
    form = AppealForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            try:
                _, people, _, _, current = locked_pair(restriction.decision.match_id)
            except ValidationError:
                return HttpResponse("Manager changed", status=409)
            person = next(p for p in people if p.pk == restriction.person_id)
            if restriction.manager_version != person.manager_version or not (
                person.subject_id == request.user.pk
                or person_queryset(request.user).filter(pk=person.pk).exists()
            ):
                return HttpResponse("Access changed", status=409)
            existing = PhotoAppeal.objects.filter(restriction=restriction).first()
            if not existing and (
                current.decision != "conflict"
                or current.resolutions.order_by("-created_at", "-pk").first().pk
                != restriction.decision_id
                or current.photo.removed_at
                or current.candidate.removed_at
            ):
                return HttpResponse("Restriction changed", status=409)
            PhotoAppeal.objects.get_or_create(
                restriction=restriction,
                defaults={
                    "actor": request.user,
                    "review_version": current.review_version,
                    "explanation": form.cleaned_data["explanation"],
                },
            )
        return redirect("photo_restriction", restriction_id=restriction.pk)
    return render(
        request,
        "listings/photo_restriction.html",
        {
            "restriction": restriction,
            "active": active,
            "pending_review": current.resolved_at is None,
            "appeal": PhotoAppeal.objects.filter(restriction=restriction).first(),
            "form": form,
        },
        status=400 if request.method == "POST" else 200,
    )
