"""Bounded private operational publication review queue with encrypted keyset cursor."""

from datetime import date, datetime, timedelta

from cryptography.fernet import InvalidToken
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET

from .crypto import seal, unseal
from .models import PrivacyPublicationHold
from .processing_review import authorize
from .purpose_calendar_views import CalendarFilterForm as BaseFilterForm
from .rights import allowed
from .views import private


class CalendarFilterForm(BaseFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("purpose")


@login_required
@require_GET
def queue(request):
    if not allowed(request) or not all(
        request.user.has_perm("safety." + name)
        for name in ["execute_rights_request", "review_purpose_calendar"]
    ):
        return private(HttpResponse("Forbidden", status=403))
    values = request.GET.copy()
    if "attention" not in values:
        values["attention"] = "due"
    form = CalendarFilterForm(values)
    if not form.is_valid():
        return private(HttpResponse("Invalid filters / Filtros inválidos", status=400))
    filters = form.cleaned_data
    rows = PrivacyPublicationHold.objects.filter(
        active=True, purpose_execution__isnull=False, purpose_review_on__isnull=False
    ).select_related(
        "action__request__person",
        "action__request__referenced_revision__publisher_acceptance",
    )
    if filters["attention"] != "all":
        rows = rows.filter(
            purpose_review_on__lte=timezone.localdate()
            + timedelta(days=7 if filters["attention"] == "soon" else 0)
        )
    if filters["mode"]:
        rows = rows.filter(ground="purpose_" + filters["mode"])
    cursor = request.GET.get("cursor")
    if cursor:
        try:
            token = unseal(cursor)
            if (
                token["user"] != request.user.pk
                or token["session"] != request.user.session_version
                or token["mfa"] != request.user.mfa_version
                or token["filters"] != filters
                or datetime.fromisoformat(token["expires"]) <= timezone.now()
            ):
                raise ValueError
            day = date.fromisoformat(token["review_on"])
            pk = token["pk"]
            if (
                isinstance(pk, bool)
                or not isinstance(pk, int)
                or not 1 <= pk <= 9223372036854775807
            ):
                raise ValueError
        except (InvalidToken, ValueError, KeyError, TypeError):
            return private(HttpResponse("Invalid cursor / Cursor inválido", status=400))
        rows = rows.filter(Q(purpose_review_on__gt=day) | Q(purpose_review_on=day, pk__gt=pk))
    candidates = list(rows.order_by("purpose_review_on", "pk")[:101])
    visible = []
    for restriction in candidates[:100]:
        case = restriction.action.request
        try:
            fresh = authorize(request.user, case, review_permission=False)
        except PermissionDenied:
            continue
        if not fresh.has_perm("safety.review_purpose_calendar"):
            return private(HttpResponse("Forbidden", status=403))
        visible.append(restriction)
    next_cursor = None
    if len(candidates) > 100:
        last = candidates[99]
        next_cursor = seal(
            {
                "user": request.user.pk,
                "session": request.user.session_version,
                "mfa": request.user.mfa_version,
                "filters": filters,
                "expires": (timezone.now() + timedelta(hours=1)).isoformat(),
                "review_on": last.purpose_review_on.isoformat(),
                "pk": last.pk,
            }
        )
    query = request.GET.copy()
    query.pop("cursor", None)
    return private(
        render(
            request,
            "safety/publication_calendar_queue.html",
            {
                "form": form,
                "restrictions": visible,
                "next_cursor": next_cursor,
                "filters": query.urlencode(),
            },
        )
    )
