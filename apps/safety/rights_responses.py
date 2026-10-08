"""Motivated private responses; closure requires recorded, current execution evidence."""

import json
import uuid

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods, require_POST

from apps.core.models import User

from .crypto import seal, unseal
from .models import (
    RightsAccess,
    RightsNotice,
    RightsRequest,
    RightsResponse,
    RightsResponseAcknowledgement,
    RightsWithdrawal,
)
from .rectification_presentation import caption
from .rights import allowed, fingerprint
from .rights_response_text import checked_response_text
from .rights_scope import locked_case, permitted
from .rights_verification import PROCEDURE, complete_read, enabled
from .views import private


def complete_response_read(user, case):
    ids = list(
        case.responses.filter(response_version__lte=case.response_version)
        .order_by("-pk")
        .values_list("pk", flat=True)
    )
    required = {None} | {ids[index] for index in range(49, len(ids) - 1, 50)}
    read = set(
        RightsAccess.objects.filter(
            request=case,
            actor=user,
            case_version=case.version,
            response_version=case.response_version,
        ).values_list("response_before", flat=True)
    )
    return required <= read


def current_response_actor(user, case, session_version, mfa_version, *, execution=False):
    actor = User.objects.get(pk=user.pk)
    if (
        not actor.is_active
        or not actor.mfa_enabled
        or actor.session_version != session_version
        or actor.mfa_version != mfa_version
        or not actor.has_perm("safety.review_rights_request")
        or not actor.has_perm("safety.respond_rights_request")
        or (execution and not actor.has_perm("safety.execute_rights_request"))
        or case.assigned_to_id != actor.pk
        or not permitted(actor, case)
    ):
        raise PermissionDenied
    return actor


@transaction.atomic
@sensitive_variables()
def issue(
    user, case_id, key, version, response_version, kind, reason, response, redaction_confirmed
):
    session_version, mfa_version = user.session_version, user.mfa_version
    if (
        not user.mfa_enabled
        or not user.has_perm("safety.review_rights_request")
        or not user.has_perm("safety.respond_rights_request")
    ):
        raise PermissionDenied
    case, person, listing = locked_case(
        case_id, lock_listing=True, allow_version_change=True, allow_erased_account=True
    )
    user = current_response_actor(
        user, case, session_version, mfa_version, execution=kind == "representation_complete"
    )
    signature = fingerprint(
        json.dumps(
            {
                "version": version,
                "response_version": response_version,
                "kind": kind,
                "reason": reason,
                "response": response,
                "redaction_confirmed": redaction_confirmed,
            },
            sort_keys=True,
        )
    )
    previous = RightsResponse.objects.filter(key=key).first()
    if previous:
        if (
            previous.request_id == case.pk
            and previous.actor_id == user.pk
            and previous.payload_digest == signature
        ):
            current_response_actor(
                user,
                case,
                session_version,
                mfa_version,
                execution=kind == "representation_complete",
            )
            return previous
        raise ValidationError("Conflicting response key / Clave de respuesta incompatible")
    if (
        case.version != version
        or case.response_version != response_version
        or case.assigned_to_id != user.pk
        or not complete_read(user, case)
        or not complete_response_read(user, case)
    ):
        raise ValidationError(
            "Inspect the current assigned request / Consulta la solicitud asignada actual"
        )
    checked_response_text(reason, response, redaction_confirmed)
    withdrawal = None
    if kind == "progress":
        if case.status not in {"reviewing", "withdrawn"}:
            raise ValidationError("Request already closed / Solicitud cerrada")
    elif kind == "representation_complete":
        if not user.has_perm("safety.execute_rights_request"):
            raise PermissionDenied
        withdrawal = (
            RightsWithdrawal.objects.select_related("proof", "action")
            .filter(action__request=case)
            .order_by("-pk")
            .first()
        )
        if not (
            enabled()
            and case.kind == "representation"
            and case.status == "withdrawn"
            and person
            and withdrawal
            and withdrawal.person_id == person.pk
            and withdrawal.proof.status == "passed"
            and withdrawal.proof.provider == "simulator"
            and withdrawal.proof.procedure == PROCEDURE
            and withdrawal.proof.person_id == person.pk
            and withdrawal.proof.manager_version == withdrawal.previous_manager_version
            and withdrawal.proof.case_version == withdrawal.action.expected_version
            and withdrawal.action.operation == "withdraw"
            and withdrawal.proof.scope == "representation"
            and withdrawal.proof.channel_digest == case.receipt_digest
            and withdrawal.proof.subject_id_snapshot == str(person.subject_id or "")
            and withdrawal.previous_manager_version == case.manager_version
            and withdrawal.resulting_manager_version == person.manager_version
            and person.consent_revoked_at
            and not person.consent_version
            and (not listing or listing.status == "withdrawn")
        ):
            raise ValidationError(
                "Current withdrawal evidence required / Evidencia de retirada actual obligatoria"
            )
    else:
        raise ValidationError("Unsupported response outcome / Resultado de respuesta no admitido")
    try:
        with transaction.atomic():
            recorded = RightsResponse.objects.create(
                key=key,
                request=case,
                actor=user,
                case_version=case.version,
                response_version=case.response_version + 1,
                kind=kind,
                payload_digest=signature,
                encrypted_reason=seal({"reason": reason}),
                encrypted_response=seal({"text": response, "simulation": bool(withdrawal)}),
                withdrawal=withdrawal,
            )
            contact = unseal(case.encrypted_payload).get("email")
            if contact:
                RightsNotice.objects.create(
                    response=recorded,
                    encrypted_payload=seal(
                        {
                            "recipient": contact,
                            "subject": "Respuesta privada / Private response",
                            "body": "Hay una respuesta disponible en tu acuse privado. A response is available in your private receipt.",
                        }
                    ),
                )
    except IntegrityError as error:
        raise ValidationError(
            "Conflicting response key / Clave de respuesta incompatible"
        ) from error
    case.response_version += 1
    if withdrawal:
        case.status = "resolved"
        case.version += 1
        case.scope_status = "unverified"
    # An outgoing progress message changes neither input evidence nor authorization of an existing copy.
    case.save(update_fields=["response_version", "status", "version", "scope_status"])
    current_response_actor(user, case, session_version, mfa_version, execution=bool(withdrawal))
    return recorded


class ResponseForm(forms.Form):
    def __init__(self, *args, language=None, **kwargs):
        super().__init__(*args, **kwargs)
        if language is None:
            return
        for field in self.fields.values():
            field.label = caption(field.label, language)
            if hasattr(field, "choices") and not hasattr(field, "queryset"):
                field.choices = [
                    (value, caption(label, language)) for value, label in field.choices
                ]
        self.fields["kind"].label = "Response type" if language == "en" else "Tipo de respuesta"

    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    response_version = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    kind = forms.ChoiceField(
        choices=[
            ("progress", "Respuesta de progreso; mantiene abierto / Progress response; stays open"),
            (
                "representation_complete",
                "Cerrar representación retirada / Close withdrawn representation",
            ),
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
        max_length=4000,
        widget=forms.Textarea,
        label="Respuesta privada minimizada / Minimized private response",
    )
    redaction_confirmed = forms.BooleanField(
        label="He revisado los datos de terceros y el alcance real de lo ejecutado / I reviewed third-party data and actual execution scope"
    )


@login_required
@sensitive_post_parameters("reason", "response")
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def respond(request, case_id):
    if not allowed(request) or not request.user.has_perm("safety.respond_rights_request"):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    case = RightsRequest.objects.filter(pk=case_id).first()
    if not case:
        raise Http404
    if not permitted(request.user, case):
        return private(
            HttpResponse(
                "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
            )
        )
    form = ResponseForm(
        request.POST or None,
        language=request.LANGUAGE_CODE,
        initial={
            "key": uuid.uuid4(),
            "version": case.version,
            "response_version": case.response_version,
        },
    )
    if case.kind != "representation" or case.status != "withdrawn":
        form.fields["kind"].choices = [
            (
                "progress",
                "Progress response" if request.LANGUAGE_CODE == "en" else "Respuesta de progreso",
            )
        ]
    status = 400 if request.method == "POST" else 200
    if request.method == "POST" and form.is_valid():
        try:
            issue(request.user, case_id, **form.cleaned_data)
        except PermissionDenied:
            return private(
                HttpResponse(
                    "Forbidden" if request.LANGUAGE_CODE == "en" else "Acceso denegado", status=403
                )
            )
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
        else:
            return private(redirect("rights_inspect", case_id=case.pk))
    return private(
        render(request, "safety/rights_response.html", {"case": case, "form": form}, status=status)
    )


@sensitive_variables("secret")
@require_POST
def acknowledge(request, case_id, secret, response_id):
    with transaction.atomic():
        case = (
            RightsRequest.objects.select_for_update()
            .filter(pk=case_id, receipt_expires_at__gt=timezone.now())
            .first()
        )
        if (
            not case
            or len(secret) != 43
            or not constant_time_compare(case.receipt_digest, fingerprint(secret))
        ):
            raise Http404
        response = RightsResponse.objects.filter(pk=response_id, request=case).first()
        if not response:
            raise Http404
        if request.POST.get("received") != "yes":
            return private(HttpResponse("Explicit receipt confirmation required", status=400))
        RightsResponseAcknowledgement.objects.get_or_create(
            response=response, defaults={"channel_digest": case.receipt_digest}
        )
    return private(redirect("rights_receipt", case_id=case.pk, secret=secret))


def response_page(case, before=None):
    records = case.responses.select_related("rightsnotice", "receipt_acknowledgement").order_by(
        "-pk"
    )
    if before:
        records = records.filter(pk__lt=before)
    items = list(records[:51])
    return [
        {
            "id": item.pk,
            "acknowledged_at": getattr(
                getattr(item, "receipt_acknowledgement", None), "created_at", None
            ),
            "created_at": item.created_at,
            "kind": item.kind,
            "body": unseal(item.encrypted_response),
            "notice_status": getattr(getattr(item, "rightsnotice", None), "status", ""),
        }
        for item in items[:50]
    ], items[49].pk if len(items) > 50 else None
