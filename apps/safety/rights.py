import calendar
import json
import secrets
import uuid
from datetime import timedelta

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.accounts import limited

from .crypto import seal, unseal
from .models import RightsAccess, RightsMessage, RightsRequest
from .rights_prompts import PROMPTS
from .rights_scope import locked_case, permitted
from .views import private


def fingerprint(value):
    return salted_hmac("rights-request-v1", value, algorithm="sha256").hexdigest()


def calendar_months(value, months):
    if months not in {1, 2, 3}:
        raise ValueError("Unsupported calendar target")
    local = timezone.localtime(value)
    year, offset = divmod(local.year * 12 + local.month - 1 + months, 12)
    month = offset + 1
    day = min(local.day, calendar.monthrange(year, month)[1])
    return local.replace(year=year, month=month, day=day)


def next_month(value):
    return calendar_months(value, 1)


class RequestForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    receipt_secret = forms.RegexField(r"^[A-Za-z0-9_-]{43}$", widget=forms.HiddenInput)
    kind = forms.ChoiceField(
        choices=[
            ("access", "Acceso a datos / Data access"),
            ("rectify", "Rectificación / Rectification"),
            ("erase", "Supresión / Erasure"),
            ("portability", "Portabilidad / Portability"),
            ("restriction", "Limitación / Restriction"),
            ("object", "Oposición / Objection"),
            ("representation", "Reclamación de representación / Representation complaint"),
        ]
    )
    reference = forms.CharField(
        required=False,
        max_length=600,
        label="Perfil o referencia de tus datos / Profile or reference to your data",
    )
    explanation = forms.CharField(
        min_length=1,
        max_length=4000,
        widget=forms.Textarea,
        label="Solicitud y alcance / Request and scope",
    )
    name = forms.CharField(required=False, max_length=120, label="Nombre / Name")
    email = forms.EmailField(
        required=False, label="Contacto privado opcional / Optional private contact"
    )


class RightsAccessForm(forms.Form):
    response_before = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, widget=forms.HiddenInput
    )
    message_before = forms.IntegerField(
        required=False, min_value=1, max_value=9223372036854775807, widget=forms.HiddenInput
    )
    purpose = forms.CharField(
        min_length=10, max_length=200, label="Motivo de consulta / Purpose of access"
    )


@sensitive_post_parameters("receipt_secret", "reference", "explanation", "name", "email")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def submit(request):
    form = RequestForm(
        request.POST or None,
        initial={"key": uuid.uuid4(), "receipt_secret": secrets.token_urlsafe(32)},
    )
    status = 400 if request.method == "POST" else 200
    if request.method == "POST":
        if limited(request, "rights-create", limit=20):
            return private(HttpResponse("Too many requests / Demasiadas solicitudes", status=429))
        if form.is_valid():
            data = dict(form.cleaned_data)
            key, secret = data.pop("key"), data.pop("receipt_secret")
            signature = fingerprint(json.dumps(data, sort_keys=True, ensure_ascii=False))
            now = timezone.now()
            with transaction.atomic():
                case, _ = RightsRequest.objects.get_or_create(
                    submission_key=key,
                    defaults={
                        "receipt_digest": fingerprint(secret),
                        "payload_digest": signature,
                        "encrypted_payload": seal(data),
                        "kind": data["kind"],
                        "priority": 0 if data["kind"] == "representation" else 1,
                        "actor": request.user if request.user.is_authenticated else None,
                        "received_at": now,
                        "initial_due_at": next_month(now),
                        "receipt_expires_at": now + timedelta(days=180),
                    },
                )
            if (
                not constant_time_compare(case.receipt_digest, fingerprint(secret))
                or case.payload_digest != signature
            ):
                form.add_error(None, "Reintento incompatible / Conflicting request replay")
                status = 409
            else:
                return private(redirect("rights_receipt", case_id=case.pk, secret=secret))
    return private(render(request, "safety/rights_form.html", {"form": form}, status=status))


class MessageForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    text = forms.CharField(
        min_length=1,
        max_length=4000,
        widget=forms.Textarea,
        label="Aclaración sobre tu solicitud / Clarification about your request",
    )


@sensitive_post_parameters("text")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def receipt(request, case_id, secret):
    case = RightsRequest.objects.filter(pk=case_id, receipt_expires_at__gt=timezone.now()).first()
    if (
        not case
        or len(secret) != 43
        or not constant_time_compare(case.receipt_digest, fingerprint(secret))
    ):
        raise Http404
    from .rights_responses import response_page

    try:
        before = forms.IntegerField(
            required=False, min_value=1, max_value=9223372036854775807
        ).clean(request.GET.get("response_before"))
    except ValidationError:
        return private(HttpResponse("Invalid response cursor", status=400))
    responses, response_cursor = response_page(case, before)
    form = MessageForm(request.POST or None, initial={"key": uuid.uuid4(), "version": case.version})
    status = 400 if request.method == "POST" else 200
    if request.method == "POST":
        if limited(request, "rights-message", limit=10):
            return private(HttpResponse("Too many requests / Demasiadas solicitudes", status=429))
        if form.is_valid():
            signature = fingerprint(
                json.dumps(
                    {
                        "case": str(case_id),
                        "version": form.cleaned_data["version"],
                        "text": form.cleaned_data["text"],
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
            )
            with transaction.atomic():
                case = RightsRequest.objects.select_for_update().get(pk=case_id)
                if case.receipt_expires_at <= timezone.now() or not constant_time_compare(
                    case.receipt_digest, fingerprint(secret)
                ):
                    raise Http404
                previous = RightsMessage.objects.filter(key=form.cleaned_data["key"]).first()
                if previous:
                    if previous.request_id != case.pk or previous.payload_digest != signature:
                        form.add_error(None, "Reintento incompatible / Conflicting replay")
                        status = 409
                    else:
                        return private(redirect("rights_receipt", case_id=case.pk, secret=secret))
                elif case.version != form.cleaned_data["version"] or case.status not in {
                    "received",
                    "reviewing",
                }:
                    form.add_error(None, "Solicitud cambiada; recarga / Request changed; reload")
                    status = 409
                else:
                    try:
                        with transaction.atomic():
                            RightsMessage.objects.create(
                                key=form.cleaned_data["key"],
                                request=case,
                                actor=request.user if request.user.is_authenticated else None,
                                expected_version=case.version,
                                payload_digest=signature,
                                encrypted_payload=seal({"text": form.cleaned_data["text"]}),
                            )
                    except IntegrityError:
                        form.add_error(None, "Clave incompatible / Conflicting request key")
                        status = 409
                    else:
                        case.version += 1
                        case.scope_status = "unverified"
                        case.save(update_fields=["version", "scope_status"])
                        return private(redirect("rights_receipt", case_id=case.pk, secret=secret))
    return private(
        render(
            request,
            "safety/rights_receipt.html",
            {
                "case": case,
                "responses": responses,
                "response_cursor": response_cursor,
                "form": form,
                "message_count": case.messages.count(),
                "exports": case_export_forms(case),
                "secret": secret,
                "questions": [
                    {
                        "created_at": item.created_at,
                        "es": PROMPTS[item.clarification_prompt][0],
                        "en": PROMPTS[item.clarification_prompt][1],
                    }
                    for item in case.actions.filter(operation="clarify").order_by("-pk")[:50]
                    if item.clarification_prompt in PROMPTS
                ],
            },
            status=status,
        )
    )


def allowed(request):
    return (
        request.user.has_perm("safety.review_rights_request")
        and request.user.mfa_enabled
        and request.session.get("mfa_version") == request.user.mfa_version
    )


@login_required
@require_GET
def queue(request):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    attention = request.GET.get("attention", "all")
    choices = {"all", "overdue", "due_soon", "priority", "unassigned", "media_failed"}
    media_access = request.user.has_perm("mediafiles.manage_media_erasure")
    if attention not in choices:
        return private(HttpResponse("Invalid attention filter", status=400))
    if attention == "media_failed" and not media_access:
        return private(HttpResponse("Forbidden", status=403))
    cases = (
        RightsRequest.objects.all()
        .exclude(actor=request.user)
        .select_related("extension", "person", "referenced_revision__publisher_acceptance")
        .annotate(current_target=Coalesce("extension__new_due_at", "initial_due_at"))
        .order_by("priority", "current_target", "created_at", "pk")
    )
    if media_access:
        from apps.mediafiles.models import MediaErasure

        cases = cases.annotate(
            exhausted_media=Exists(
                MediaErasure.objects.filter(
                    execution__action__request_id=OuterRef("pk"),
                    status="failed",
                    attempts__gte=5,
                )
            )
        )
    if attention == "media_failed":
        # Physical deletion may remain outstanding even after the case changes status.
        cases = cases.filter(exhausted_media=True)
    else:
        cases = cases.filter(status__in=["received", "reviewing"])
    now = timezone.now()
    if attention == "overdue":
        cases = cases.filter(current_target__lte=now)
    elif attention == "due_soon":
        cases = cases.filter(current_target__gt=now, current_target__lte=now + timedelta(days=7))
    elif attention == "priority":
        cases = cases.filter(priority=0)
    elif attention == "unassigned":
        cases = cases.filter(assigned_to__isnull=True)
    visible = [case for case in cases if permitted(request.user, case)]
    page = Paginator(visible, 50).get_page(request.GET.get("page"))
    return private(
        render(
            request,
            "safety/rights_queue.html",
            {"cases": page, "page": page, "attention": attention, "media_access": media_access},
        )
    )


@login_required
@sensitive_post_parameters("purpose")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inspect(request, case_id):
    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Conflict of interest", status=403))
    form = RightsAccessForm(request.POST or None)
    payload = None
    messages = []
    next_message_cursor = None
    outgoing_responses = []
    outgoing_cursor = None
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            try:
                case, _, _ = locked_case(case.pk, allow_erased_account=True)
            except ValidationError:
                return private(HttpResponse("Management changed; reload", status=409))
            if not permitted(request.user, case):
                return private(HttpResponse("Conflict of interest", status=403))
            payload = unseal(case.encrypted_payload)
            RightsAccess.objects.create(
                request=case,
                actor=request.user,
                purpose=form.cleaned_data["purpose"],
                case_version=case.version,
                message_before=form.cleaned_data["message_before"],
                response_version=case.response_version,
                response_before=form.cleaned_data["response_before"],
            )
            from .rights_responses import response_page

            outgoing_responses, outgoing_cursor = response_page(
                case, form.cleaned_data["response_before"]
            )
            records = case.messages.order_by("-pk")
            if form.cleaned_data["message_before"]:
                records = records.filter(pk__lt=form.cleaned_data["message_before"])
            records = list(records[:51])
            messages = [
                {
                    "created_at": message.created_at,
                    "text": unseal(message.encrypted_payload)["text"],
                }
                for message in records[:50]
            ]
            if len(records) > 50:
                next_message_cursor = records[49].pk
    from django.core.paginator import Paginator

    from .models import RightsRectificationRecipientAssessment

    recipient_assessments = None
    if request.user.has_perm("safety.review_recipient_assessment"):
        recipient_assessments = Paginator(
            RightsRectificationRecipientAssessment.objects.filter(action__request=case)
            .exclude(action__actor=request.user)
            .select_related("action")
            .only("pk", "created_at", "action__actor_id")
            .order_by("-created_at", "-pk"),
            50,
        ).get_page(request.GET.get("recipient_page"))
    return private(
        render(
            request,
            "safety/rights_inspect.html",
            {
                "case": case,
                "form": form,
                "payload": payload,
                "messages": messages,
                "next_message_cursor": next_message_cursor,
                "outgoing_responses": outgoing_responses,
                "outgoing_cursor": outgoing_cursor,
                "recipient_assessments": recipient_assessments,
            },
            status=400 if request.method == "POST" and not form.is_valid() else 200,
        )
    )


class ActionForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    link_listing_id = forms.UUIDField(
        required=False, label="ID del anuncio de referencia / Referenced listing ID"
    )
    link_account_id = forms.IntegerField(
        required=False, min_value=1, label="Cuenta propia: ID / Own account: ID"
    )
    link_person_id = forms.UUIDField(
        required=False,
        label="ID de perfil sin anuncio / Profile ID without listing",
    )
    operation = forms.ChoiceField(
        choices=[
            ("claim", "Asignarme la solicitud / Assign request to me"),
            ("link", "Vincular referencia al perfil / Link reference to profile"),
            ("clarify", "Pedir aclaración / Request clarification"),
            ("withdraw", "Retirar representación comprobada / Withdraw checked representation"),
            ("extend", "Ampliar objetivo de respuesta / Extend response target"),
            ("unassign", "Devolver a cola (coordinación) / Return to queue (coordination)"),
        ]
    )
    clarification_prompt = forms.ChoiceField(
        required=False,
        choices=[
            ("", "---------"),
            ("reference", "Referencia / Reference"),
            ("scope", "Alcance / Scope"),
            ("contact", "Contacto propio opcional / Optional own contact"),
        ],
        label="Pregunta al solicitante (solo aclaración) / Requester question (clarification only)",
    )
    reason = forms.CharField(
        min_length=10,
        max_length=2000,
        widget=forms.Textarea,
        label="Motivo privado / Private reason",
    )
    additional_months = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=2,
        label="Meses adicionales (solo ampliación) / Additional months (extension only)",
    )
    extension_reason = forms.ChoiceField(
        required=False,
        choices=[
            ("", "---------"),
            ("complexity", "Complejidad / Complexity"),
            ("volume", "Número de solicitudes / Number of requests"),
        ],
        label="Motivo comunicable de ampliación / Communicable extension grounds",
    )


@login_required
@sensitive_post_parameters("reason")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def action(request, case_id):
    from .rights_actions import act

    if not allowed(request):
        return private(HttpResponse("Forbidden", status=403))
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(HttpResponse("Conflict of interest", status=403))
    form = ActionForm(request.POST or None, initial={"key": uuid.uuid4(), "version": case.version})
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            act(request.user, case_id, **form.cleaned_data)
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("rights_inspect", case_id=case.pk))
    return private(
        render(request, "safety/rights_action.html", {"case": case, "form": form}, status=status)
    )


def case_export_forms(case):
    from .models import RightsExport
    from .rights_verification import enabled

    if not enabled():
        return []

    return [
        {
            "id": item.pk,
            "expires_at": item.expires_at,
            "key": uuid.uuid4(),
            "images": [{"id": image.pk, "key": uuid.uuid4()} for image in item.images.all()],
            "parts": [
                {
                    "id": part.pk,
                    "key": uuid.uuid4(),
                    "position": part.position,
                    "data": not part.attachments,
                }
                for part in item.parts.order_by("position")
            ],
        }
        for item in RightsExport.objects.filter(
            action__request=case,
            case_version=case.version,
            expires_at__gt=timezone.now(),
            purged_at__isnull=True,
        ).order_by("-created_at")[:10]
    ]
