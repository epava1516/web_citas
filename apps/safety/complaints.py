"""Separate public decision-complaint intake; references never confer case access."""

import json
import secrets
import uuid
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.accounts import limited

from .complaint_scope import locked, permitted
from .crypto import digest, seal, unseal
from .models import Complaint, ComplaintAccess, ComplaintNotice, ComplaintResolution
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
    from django.core.paginator import Paginator

    from .complaint_messages import PROMPTS, MessageForm

    complaint = Complaint.objects.filter(
        pk=complaint_id, receipt_expires_at__gt=timezone.now()
    ).first()
    if (
        len(secret) != 43
        or not complaint
        or not constant_time_compare(complaint.receipt_digest, digest(secret))
    ):
        raise Http404
    resolution = ComplaintResolution.objects.filter(complaint=complaint).first()
    notice = ComplaintNotice.objects.filter(resolution=resolution).first() if resolution else None
    response = unseal(resolution.encrypted_response)["response"] if resolution else None
    return private(
        render(
            request,
            "safety/complaint_receipt.html",
            {
                "complaint": complaint,
                "secret": secret,
                "message_form": MessageForm(
                    initial={"key": uuid.uuid4(), "version": complaint.version}
                ),
                "message_count": complaint.messages.count(),
                "questions": Paginator(
                    [
                        {
                            "created_at": action.created_at,
                            "es": PROMPTS[action.clarification_prompt][0],
                            "en": PROMPTS[action.clarification_prompt][1],
                        }
                        for action in complaint.actions.filter(operation="clarify").order_by("-pk")
                        if action.clarification_prompt in PROMPTS
                    ],
                    50,
                ).get_page(request.GET.get("questions_page")),
                "resolution": resolution,
                "response": response,
                "notice": notice,
                "notice_simulator": bool(
                    notice and notice.status == "simulated" and not settings.PRODUCTION
                ),
            },
        )
    )


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
    complaints = (
        Complaint.objects.filter(status__in=["received", "reviewing"])
        .exclude(actor=request.user)
        .select_related("assigned_to")
    )
    visible = [case for case in complaints[:100] if permitted(request.user, case)]
    return private(render(request, "safety/complaint_queue.html", {"complaints": visible}))


class AccessForm(forms.Form):
    message_before = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, widget=forms.HiddenInput
    )
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
    if not permitted(request.user, complaint):
        return private(HttpResponse("Conflict of interest", status=403))
    form = AccessForm(request.POST or None)
    payload = None
    source_evidence = None
    messages = []
    next_message_cursor = None
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            try:
                complaint, _ = locked(complaint_id)
            except ValidationError:
                return private(HttpResponse("Case changed; reload", status=409))
            if not permitted(request.user, complaint) or not allowed(request):
                return private(HttpResponse("Forbidden", status=403))
            from .complaint_resolutions import source_permission, source_version

            source_allowed = source_permission(request.user, complaint)
            source_evidence = (
                complaint.listing_decision
                if source_allowed and complaint.listing_decision_id
                else None
            )
            ComplaintAccess.objects.create(
                complaint=complaint,
                actor=request.user,
                purpose=form.cleaned_data["purpose"],
                case_version=complaint.version,
                source_version=source_version(complaint) if source_allowed else None,
                message_before=form.cleaned_data["message_before"],
            )
            payload = unseal(complaint.encrypted_payload)
            records = complaint.messages.order_by("-pk")
            if form.cleaned_data["message_before"]:
                records = records.filter(pk__lt=form.cleaned_data["message_before"])
            rows = list(records[:51])
            messages = [
                {"created_at": row.created_at, "text": unseal(row.encrypted_payload)["text"]}
                for row in rows[:50]
            ]
            next_message_cursor = rows[49].pk if len(rows) > 50 else None
    return private(
        render(
            request,
            "safety/complaint_inspect.html",
            {
                "complaint": complaint,
                "form": form,
                "payload": payload,
                "source_evidence": source_evidence,
                "clarification_messages": messages,
                "next_message_cursor": next_message_cursor,
                "source_photos": source_evidence.revision.photos.filter(removed_at__isnull=True)
                if source_evidence
                else [],
            },
            status=400 if request.method == "POST" and not form.is_valid() else 200,
        )
    )


class ActionForm(forms.Form):
    from .complaint_messages import PROMPTS

    clarification_prompt = forms.ChoiceField(
        required=False,
        choices=[("", "—")]
        + [(key, value[0] + " / " + value[1]) for key, value in PROMPTS.items()],
        label="Pregunta pública minimizada / Minimized public question",
    )
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    operation = forms.ChoiceField(
        choices=[
            ("claim", "Asignarme la reclamación / Assign request to me"),
            ("unassign", "Devolver a cola / Return request to queue"),
            ("link", "Enlazar decisión / Link decision"),
            ("link_listing", "Enlazar revisión de anuncio / Link listing review"),
            ("clarify", "Solicitar aclaración de referencia / Request reference clarification"),
        ]
    )
    decision_id = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=9223372036854775807,
        label="ID de decisión / Decision ID",
    )
    decision_case_version = forms.IntegerField(
        required=False,
        min_value=1,
        label="Versión del expediente de decisión / Decision case version",
    )
    reason = forms.CharField(
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def action(request, complaint_id):
    from .complaint_actions import act

    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    complaint = Complaint.objects.filter(pk=complaint_id).first()
    if not complaint:
        raise Http404
    if not permitted(request.user, complaint):
        return private(HttpResponse("Conflict of interest", status=403))
    form = ActionForm(
        request.POST or None, initial={"key": uuid.uuid4(), "version": complaint.version}
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            act(request.user, complaint_id, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("complaint_inspect", complaint_id=complaint.pk))
    return private(
        render(
            request,
            "safety/complaint_action.html",
            {"form": form, "complaint": complaint},
            status=status,
        )
    )


@login_required
@sensitive_variables()
@require_GET
def photo(request, complaint_id, photo_id):
    from .complaint_resolutions import source_version

    if not allowed(request) or not request.user.has_perm("listings.review_listing"):
        return private(HttpResponse("Forbidden", status=403))
    if not Complaint.objects.filter(pk=complaint_id).exists():
        raise Http404
    with transaction.atomic():
        try:
            complaint, _ = locked(complaint_id)
        except ValidationError:
            return private(HttpResponse("Case changed; reload", status=409))
        if not permitted(request.user, complaint) or not complaint.listing_decision_id:
            return private(HttpResponse("Forbidden", status=403))
        current_version = source_version(complaint)
        if not ComplaintAccess.objects.filter(
            complaint=complaint,
            actor=request.user,
            case_version=complaint.version,
            source_version=current_version,
            kind="intake",
        ).exists():
            return private(HttpResponse("Inspect current request first", status=409))
        photo = (
            complaint.listing_decision.revision.photos.filter(pk=photo_id, removed_at__isnull=True)
            .select_related("blob")
            .first()
        )
        if not photo:
            raise Http404
        if photo.blob.status != "ready" or not photo.blob.derivative:
            return private(HttpResponse("Image processing", status=409))
        response = FileResponse(photo.blob.derivative.open("rb"), content_type="image/webp")
        ComplaintAccess.objects.create(
            complaint=complaint,
            actor=request.user,
            purpose="Linked revision image delivery",
            case_version=complaint.version,
            source_version=current_version,
            kind="image",
            photo=photo,
        )
    return private(response)


class ResolutionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    source_version = forms.IntegerField(min_value=1, required=False, widget=forms.HiddenInput)
    outcome = forms.ChoiceField(
        choices=[
            ("upheld", "Mantener decisión / Uphold decision"),
            ("reconsidered", "Reconsiderar decisión / Reconsider decision"),
            ("unidentified", "Referencia sin identificar / Reference unidentified"),
        ]
    )
    reason = forms.CharField(
        min_length=20,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo interno / Internal reason",
    )
    response = forms.CharField(
        min_length=50,
        max_length=2000,
        widget=forms.Textarea,
        label="Respuesta motivada al solicitante, sin información de terceros / Motivated response to requester, without third party information",
    )
    redaction_confirmed = forms.BooleanField(
        label="He revisado la respuesta y eliminado datos de terceros y notas internas / I reviewed the response and removed third party information and internal notes"
    )


@login_required
@sensitive_post_parameters("reason", "response")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def resolve(request, complaint_id):
    from .complaint_resolutions import resolve as resolve_case
    from .complaint_resolutions import source_permission, source_version

    if not allowed(request) or not request.user.has_perm("safety.resolve_complaint"):
        return private(HttpResponse("Forbidden", status=403))
    complaint = Complaint.objects.filter(pk=complaint_id).first()
    if not complaint:
        raise Http404
    if not permitted(request.user, complaint) or (
        (complaint.decision_id or complaint.listing_decision_id)
        and not source_permission(request.user, complaint)
    ):
        return private(HttpResponse("Forbidden", status=403))
    form = ResolutionForm(
        request.POST or None,
        initial={
            "key": uuid.uuid4(),
            "version": complaint.version,
            "source_version": source_version(complaint),
        },
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            resolve_case(request.user, complaint_id, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("complaint_inspect", complaint_id=complaint.pk))
    return private(
        render(
            request,
            "safety/complaint_resolution.html",
            {"complaint": complaint, "form": form},
            status=status,
        )
    )
