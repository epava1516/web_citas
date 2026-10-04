"""Private operational recovery; never reveals or sends notice envelopes."""

import json
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.models import Agency, Person
from apps.listings.models import Listing

from .complaint_scope import locked as locked_complaint
from .complaint_scope import permitted as complaint_permitted
from .crypto import digest, seal
from .models import ComplaintNotice, NoticeRecovery, Report, ReportNotice
from .views import permitted as report_permitted
from .views import private

MODELS = {"report": ReportNotice, "complaint": ComplaintNotice}


def allowed(user):
    return user.mfa_enabled and user.has_perm("safety.manage_notice_delivery")


def scoped(user, kind, notice):
    if kind == "report":
        return user.has_perm("safety.review_report") and report_permitted(user, notice.report)
    return user.has_perm("safety.review_complaint") and complaint_permitted(
        user, notice.resolution.complaint
    )


def locked_report(report_id):
    initial = Report.objects.select_related("listing__person").get(pk=report_id)
    person = initial.listing.person if initial.listing_id else None
    agencies = {
        value
        for value in [initial.reported_agency_id, person.agency_id if person else None]
        if value
    }
    list(Agency.objects.select_for_update().filter(pk__in=agencies).order_by("pk"))
    if person:
        current = Person.objects.select_for_update().get(pk=person.pk)
        if current.agency_id != person.agency_id:
            raise ValidationError("Management changed; reload / Gestor cambiado; recarga")
        listing = Listing.objects.select_for_update().get(pk=initial.listing_id)
        listing.person = current
    report = Report.objects.select_for_update().get(pk=report_id)
    if report.listing_id != initial.listing_id:
        raise ValidationError("Reference changed; reload / Referencia cambiada; recarga")
    if person:
        report.listing = listing
    return report


@transaction.atomic
@sensitive_variables()
def requeue(user, kind, notice_id, key, version, reason):
    if not allowed(user):
        raise PermissionDenied
    model = MODELS.get(kind)
    if not model or not 1 <= notice_id <= 9223372036854775807:
        raise Http404
    initial = model.objects.filter(pk=notice_id).first()
    if not initial:
        raise Http404
    # Cooperates with publication/management locks; worker holds only the notice lock.
    if kind == "report":
        source = locked_report(initial.report_id)
    else:
        source, _ = locked_complaint(initial.resolution.complaint_id)
    notice = model.objects.select_for_update().get(pk=notice_id)
    if kind == "report":
        notice.report = source
    else:
        notice.resolution.complaint = source
    if not scoped(user, kind, notice):
        raise PermissionDenied
    fingerprint = digest(
        json.dumps(
            {"kind": kind, "notice": notice_id, "version": version, "reason": reason},
            sort_keys=True,
        )
    )
    previous = NoticeRecovery.objects.filter(key=key).first()
    if previous:
        if previous.actor_id == user.pk and previous.payload_digest == fingerprint:
            return notice
        raise ValidationError("Conflicting action replay / Reintento incompatible")
    if not 20 <= len(reason.strip()) <= 2000:
        raise ValidationError("Reason required / Motivo obligatorio")
    if notice.status != "failed" or notice.recovery_version != version:
        raise ValidationError("Notice changed; reload / Aviso cambiado; recarga")
    if source.receipt_expires_at <= timezone.now():
        raise ValidationError(
            "Expired case requires separate review / Caso caducado requiere revisión separada"
        )
    try:
        with transaction.atomic():
            NoticeRecovery.objects.create(
                key=key,
                actor=user,
                expected_version=version,
                previous_attempts=notice.attempts,
                encrypted_reason=seal({"reason": reason}),
                payload_digest=fingerprint,
                **{kind + "_notice": notice},
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting action replay / Reintento incompatible") from error
    notice.recovery_version += 1
    notice.status = "queued"
    notice.attempts = 0
    notice.next_attempt_at = None
    notice.error_code = ""
    notice.save(
        update_fields=["recovery_version", "status", "attempts", "next_attempt_at", "error_code"]
    )
    return notice


class RecoveryForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado de recuperación / Private recovery reason",
    )


@login_required
@require_GET
def queue(request):
    if not allowed(request.user) or request.session.get("mfa_version") != request.user.mfa_version:
        return private(HttpResponse("Forbidden", status=403))
    kind = request.GET.get("kind", "report")
    try:
        after = int(request.GET.get("after", "0"))
    except ValueError:
        return private(HttpResponse("Invalid cursor", status=400))
    if kind not in MODELS or not 0 <= after <= 9223372036854775807:
        return private(HttpResponse("Invalid queue or cursor", status=400))
    items = []
    more = False
    # No global totals: operational alerts respect the same case scope as reviewers.
    for notice in (
        MODELS[kind]
        .objects.filter(status__in=["queued", "retry", "failed"], pk__gt=after)
        .order_by("pk")
        .iterator()
    ):
        if scoped(request.user, kind, notice):
            if len(items) == 50:
                more = True
                break
            items.append({"kind": kind, "notice": notice})
    cursor = items[-1]["notice"].pk if more else None
    return private(
        render(
            request, "safety/notice_queue.html", {"items": items, "kind": kind, "cursor": cursor}
        )
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def recover(request, kind, notice_id):
    if not allowed(request.user) or request.session.get("mfa_version") != request.user.mfa_version:
        return private(HttpResponse("Forbidden", status=403))
    model = MODELS.get(kind)
    if not model or not 1 <= notice_id <= 9223372036854775807:
        raise Http404
    notice = model.objects.filter(pk=notice_id).first()
    if not notice:
        raise Http404
    if not scoped(request.user, kind, notice):
        return private(HttpResponse("Forbidden", status=403))
    try:
        before = int(request.GET.get("before", "9223372036854775807"))
    except ValueError:
        return private(HttpResponse("Invalid history cursor", status=400))
    if not 1 <= before <= 9223372036854775807:
        return private(HttpResponse("Invalid history cursor", status=400))
    form = RecoveryForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": notice.recovery_version}
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            requeue(request.user, kind, notice_id, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("notice_recover", kind=kind, notice_id=notice_id))
    records = list(
        NoticeRecovery.objects.filter(**{kind + "_notice": notice}, pk__lt=before).order_by("-pk")[
            :51
        ]
    )
    history = records[:50]
    cursor = history[-1].pk if len(records) > 50 else None
    return private(
        render(
            request,
            "safety/notice_recover.html",
            {"form": form, "notice": notice, "history": history, "history_cursor": cursor},
            status=status,
        )
    )
