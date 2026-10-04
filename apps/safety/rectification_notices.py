"""Private in-app notices; current managers only, no outbound provider."""

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from apps.core.agencies import person_queryset
from apps.core.models import AgencyMember, User
from apps.core.verification import locked_manager_person

from .models import RightsRectificationManagerNotice
from .views import private


def create(execution, person):
    recipients = {person.individual_id} if person.individual_id else {person.agency.owner_id}
    if (
        person.agency_id
        and person.assigned_editor_id
        and AgencyMember.objects.filter(
            agency_id=person.agency_id, user_id=person.assigned_editor_id, active=True
        ).exists()
    ):
        recipients.add(person.assigned_editor_id)
    active = User.objects.filter(pk__in=recipients, is_active=True, account_erased_at__isnull=True)
    RightsRectificationManagerNotice.objects.bulk_create(
        [
            RightsRectificationManagerNotice(
                execution=execution, recipient=user, manager_version=person.manager_version
            )
            for user in active
        ]
    )


def allowed(request):
    return bool(
        request.user.is_active
        and not request.user.account_erased_at
        and request.user.mfa_enabled
        and request.session.get("mfa_version") == request.user.mfa_version
    )


def visible(user):
    return RightsRectificationManagerNotice.objects.filter(
        recipient=user,
        execution__notification__review__proposal__person__in=person_queryset(user),
        manager_version=F("execution__notification__review__proposal__person__manager_version"),
    )


@login_required
@require_GET
def inbox(request):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    notices = (
        visible(request.user)
        .select_related("execution__corrected_revision")
        .order_by("-created_at", "-pk")
    )
    return private(
        render(
            request,
            "safety/rectification_notices.html",
            {"notices": Paginator(notices, 50).get_page(request.GET.get("page"))},
        )
    )


@login_required
@require_POST
def acknowledge(request, notice_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    notice = (
        visible(request.user)
        .select_related("execution__notification__review__proposal")
        .filter(pk=notice_id)
        .first()
    )
    if not notice:
        raise Http404
    with transaction.atomic():
        person = locked_manager_person(
            request.user, notice.execution.notification.review.proposal.person_id
        )
        notice = RightsRectificationManagerNotice.objects.select_for_update().get(pk=notice.pk)
        if person.manager_version != notice.manager_version:
            raise Http404
        if not notice.acknowledged_at:
            notice.acknowledged_at = timezone.now()
            notice.save(update_fields=["acknowledged_at"])
    return private(redirect("rectification_notices"))
