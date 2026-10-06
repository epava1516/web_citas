"""Private operational acknowledgement, distinct from evidence access or a decision."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.core.models import Agency, Person, User

from .models import Report, UrgentReportAlert
from .views import permitted, private


def authorized(request):
    return (
        request.user.has_perm("safety.review_report")
        and request.user.mfa_enabled
        and request.session.get("mfa_version") == request.user.mfa_version
    )


def fresh_authority(request):
    """Recheck revocation after lock waits, including legitimate replays."""
    actor = User.objects.get(pk=request.user.pk)
    if (
        not actor.is_active
        or not actor.has_perm("safety.review_report")
        or not actor.mfa_enabled
        or actor.session_version != request.user.session_version
        or actor.mfa_version != request.user.mfa_version
        or request.session.get("mfa_version") != actor.mfa_version
        or request.session.get("account_version") != actor.session_version
    ):
        raise PermissionDenied
    return actor


@login_required
@require_http_methods(["GET", "POST"])
def queue(request):
    if not authorized(request):
        raise PermissionDenied
    attention = request.GET.get("attention", "unacknowledged")
    if attention not in {"unacknowledged", "follow_up"}:
        return private(HttpResponse("Invalid attention", status=400))
    if request.method == "POST":
        import uuid

        try:
            report_id = uuid.UUID(request.POST.get("report_id", ""))
        except (ValueError, TypeError, AttributeError):
            return private(HttpResponse("Invalid report", status=400))
        report = (
            Report.objects.select_related("listing__person__agency", "reported_agency")
            .filter(pk=report_id)
            .first()
        )
        if not report:
            raise Http404
        if not permitted(request.user, report):
            raise PermissionDenied
        with transaction.atomic():
            person = report.listing.person if report.listing_id else None
            agency_ids = {
                value
                for value in [report.reported_agency_id, person.agency_id if person else None]
                if value
            }
            list(Agency.objects.select_for_update().filter(pk__in=agency_ids).order_by("pk"))
            if person:
                previous_agency = person.agency_id
                person = Person.objects.select_for_update().get(pk=person.pk)
                if person.agency_id != previous_agency:
                    return private(HttpResponse("Management changed; reload", status=409))
            report = (
                Report.objects.select_for_update(of=("self",))
                .select_related("listing__person__agency", "reported_agency")
                .get(pk=report.pk)
            )
            if person:
                report.listing.person = person
            if not permitted(request.user, report):
                raise PermissionDenied
            alert = UrgentReportAlert.objects.select_for_update().filter(report=report).first()
            if not alert:
                return private(HttpResponse("Alert unavailable", status=409))
            actor = fresh_authority(request)
            if not permitted(actor, report):
                raise PermissionDenied
            if alert.acknowledged_at is None:
                alert.acknowledged_at = timezone.now()
                alert.acknowledged_by = actor
                alert.save(update_fields=["acknowledged_at", "acknowledged_by"])
            fresh_authority(request)
        return private(redirect("urgent_report_alerts"))
    alerts = UrgentReportAlert.objects.all()
    if attention == "unacknowledged":
        alerts = alerts.filter(acknowledged_at__isnull=True)
    else:
        # Recognition never closes operational follow-up. Unknown states remain
        # visible for triage rather than being silently classified as resolved.
        alerts = alerts.filter(acknowledged_at__isnull=False).exclude(
            report__status__in=["dismissed", "lifted"]
        )
    alerts = (
        alerts.select_related(
            "report__listing__person__agency", "report__reported_agency", "report__assigned_to"
        )
        .order_by("created_at", "pk")
    )
    visible = [alert for alert in alerts if permitted(request.user, alert.report)]
    page = Paginator(visible, 50).get_page(request.GET.get("page"))
    return private(
        render(request, "safety/urgent_alerts.html", {"page": page, "attention": attention})
    )
