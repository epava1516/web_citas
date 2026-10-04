"""Separate public decision-complaint intake; references never confer case access."""

import json
import secrets
import uuid
from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.accounts import limited

from .crypto import digest, seal, unseal
from .models import Complaint, ComplaintAccess
from .views import private


class ComplaintForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    receipt_secret = forms.RegexField(r"^[A-Za-z0-9_-]{43}$", widget=forms.HiddenInput)
    relationship = forms.ChoiceField(
        choices=[
            ("represented", "Persona representada / Represented person"),
            ("advertiser", "Anunciante / Advertiser"),
            ("notifier", "Notificante / Notifier"),
            ("other", "Otra relación / Other relationship"),
        ],
        label="Relación que declaras / Your stated relationship",
    )
    reference = forms.CharField(
        max_length=600, label="Decisión o perfil al que te refieres / Decision or profile reference"
    )
    explanation = forms.CharField(
        min_length=20,
        max_length=4000,
        widget=forms.Textarea,
        label="Por qué solicitas revisión / Why you request review",
    )
    name = forms.CharField(required=False, max_length=120, label="Nombre / Name")
    email = forms.EmailField(required=False, label="Contacto privado propio / Your private contact")


@sensitive_post_parameters("receipt_secret", "reference", "explanation", "name", "email")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def submit(request):
    form = ComplaintForm(
        request.POST or None,
        initial={
            "key": uuid.uuid4(),
            "receipt_secret": secrets.token_urlsafe(32),
        },
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST":
        if limited(request, "complaint-create", limit=10):
            return private(HttpResponse("Too many requests / Demasiadas solicitudes", status=429))
        if form.is_valid():
            data = dict(form.cleaned_data)
            key, secret = data.pop("key"), data.pop("receipt_secret")
            actor_id = request.user.pk if request.user.is_authenticated else None
            fingerprint = digest(
                json.dumps(
                    {"payload": data, "actor": str(actor_id or "")},
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            with transaction.atomic():
                complaint, _ = Complaint.objects.get_or_create(
                    submission_key=key,
                    defaults={
                        "receipt_digest": digest(secret),
                        "payload_digest": fingerprint,
                        "encrypted_payload": seal(data),
                        "actor_id": actor_id,
                        "receipt_expires_at": timezone.now() + timedelta(days=180),
                    },
                )
            if (
                not constant_time_compare(complaint.receipt_digest, digest(secret))
                or complaint.payload_digest != fingerprint
            ):
                form.add_error(None, "Reintento incompatible / Conflicting replay")
                status = 409
            else:
                return private(
                    redirect("complaint_receipt", complaint_id=complaint.pk, secret=secret)
                )
    return private(render(request, "safety/complaint.html", {"form": form}, status=status))


@sensitive_variables("secret")
@require_GET
def receipt(request, complaint_id, secret):
    complaint = Complaint.objects.filter(
        pk=complaint_id, receipt_expires_at__gt=timezone.now()
    ).first()
    if (
        len(secret) != 43
        or not complaint
        or not constant_time_compare(complaint.receipt_digest, digest(secret))
    ):
        raise Http404
    return private(render(request, "safety/complaint_receipt.html", {"complaint": complaint}))


def allowed(request):
    return (
        request.user.has_perm("safety.review_complaint")
        and request.user.mfa_enabled
        and request.session.get("mfa_version") == request.user.mfa_version
    )


@login_required
@require_GET
def queue(request):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    complaints = Complaint.objects.filter(status="received").exclude(actor=request.user)
    return private(render(request, "safety/complaint_queue.html", {"complaints": complaints[:100]}))


class AccessForm(forms.Form):
    purpose = forms.CharField(
        min_length=10, max_length=200, label="Motivo de consulta / Purpose of access"
    )


@login_required
@sensitive_post_parameters("purpose")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inspect(request, complaint_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    complaint = Complaint.objects.filter(pk=complaint_id).first()
    if not complaint:
        raise Http404
    if complaint.actor_id == request.user.pk:
        return private(HttpResponse("Conflict of interest", status=403))
    form = AccessForm(request.POST or None)
    payload = None
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            complaint = Complaint.objects.select_for_update().get(pk=complaint_id)
            if complaint.actor_id == request.user.pk or not allowed(request):
                return private(HttpResponse("Forbidden", status=403))
            ComplaintAccess.objects.create(
                complaint=complaint,
                actor=request.user,
                purpose=form.cleaned_data["purpose"],
                case_version=complaint.version,
            )
            payload = unseal(complaint.encrypted_payload)
    return private(
        render(
            request,
            "safety/complaint_inspect.html",
            {
                "complaint": complaint,
                "form": form,
                "payload": payload,
            },
            status=400 if request.method == "POST" and not form.is_valid() else 200,
        )
    )
