from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from apps.core.agencies import person_queryset
from apps.mediafiles.models import PhotoRestriction


@login_required
@require_GET
def detail(request, restriction_id):
    restriction = get_object_or_404(
        PhotoRestriction.objects.filter(
            Q(person__subject=request.user) | Q(person__in=person_queryset(request.user))
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
    return render(
        request, "listings/photo_restriction.html", {"restriction": restriction, "active": active}
    )
