"""Private clarification channel; it never identifies a source decision automatically."""

import json

from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.crypto import constant_time_compare
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_POST

from apps.core.accounts import limited

from .crypto import digest, seal
from .models import Complaint, ComplaintAccess, ComplaintMessage
from .views import private

PROMPTS = {
    "reference_unknown": (
        "No hemos podido identificar la decisión. Aporta una referencia más precisa sin datos de terceros.",
        "We could not identify the decision. Provide a more precise reference without third-party data.",
    ),
    "reference_stale": (
        "La referencia corresponde a una versión anterior. Aclara qué decisión solicitas revisar sin datos de terceros.",
        "The reference relates to an earlier version. Clarify which decision you request us to review without third-party data.",
    ),
    "reference_details": (
        "Aclara la referencia y el motivo de revisión, sin documentos ni datos de otras personas.",
        "Clarify the reference and review grounds without documents or other people’s data.",
    ),
}


def complete_read(user, complaint, source_version=None):
    ids = list(complaint.messages.order_by("-pk").values_list("pk", flat=True))
    required = {None} | {ids[index] for index in range(49, len(ids) - 1, 50)}
    read = set(
        ComplaintAccess.objects.filter(
            complaint=complaint,
            actor=user,
            case_version=complaint.version,
            source_version=source_version,
            kind="intake",
        ).values_list("message_before", flat=True)
    )
    return required <= read


class MessageForm(forms.Form):
    key = forms.UUIDField(widget=forms.HiddenInput)
    version = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    text = forms.CharField(
        min_length=20,
        max_length=4000,
        widget=forms.Textarea,
        label="Aclaración privada / Private clarification",
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["text"].label = (
            "Private clarification" if language == "en" else "Aclaración privada"
        )


@transaction.atomic
@sensitive_variables()
def append(complaint_id, secret, key, version, text, actor_id=None):
    complaint = (
        Complaint.objects.select_for_update()
        .filter(pk=complaint_id, receipt_expires_at__gt=timezone.now())
        .first()
    )
    if (
        not complaint
        or len(secret) != 43
        or not constant_time_compare(complaint.receipt_digest, digest(secret))
    ):
        raise Http404
    signature = digest(
        json.dumps(
            {"version": version, "text": text, "actor": str(actor_id or "")},
            sort_keys=True,
            ensure_ascii=False,
        )
    )
    previous = ComplaintMessage.objects.filter(key=key).first()
    if previous:
        if (
            previous.complaint_id == complaint.pk
            and previous.actor_id == actor_id
            and previous.payload_digest == signature
        ):
            return complaint
        raise ValidationError("Conflicting replay / Reintento incompatible")
    if (
        complaint.status not in {"received", "reviewing"}
        or complaint.version != version
        or not 20 <= len(text.strip()) <= 4000
    ):
        raise ValidationError("Request changed or closed / Solicitud cambiada o cerrada")
    try:
        with transaction.atomic():
            ComplaintMessage.objects.create(
                key=key,
                complaint=complaint,
                actor_id=actor_id,
                expected_version=version,
                payload_digest=signature,
                encrypted_payload=seal({"text": text}),
            )
    except IntegrityError as error:
        raise ValidationError("Conflicting message key / Clave incompatible") from error
    complaint.version += 1
    complaint.save(update_fields=["version"])
    return complaint


@sensitive_post_parameters("text")
@sensitive_variables("secret")
@require_POST
def submit(request, complaint_id, secret):
    # Validate the channel before rate limiting; invalid keys disclose no case state.
    complaint = Complaint.objects.filter(
        pk=complaint_id, receipt_expires_at__gt=timezone.now()
    ).first()
    if (
        not complaint
        or len(secret) != 43
        or not constant_time_compare(complaint.receipt_digest, digest(secret))
    ):
        raise Http404
    if limited(request, "complaint-message:" + str(complaint_id), limit=10):
        return private(
            HttpResponse(
                "Too many requests" if request.LANGUAGE_CODE == "en" else "Demasiadas solicitudes",
                status=429,
            )
        )
    form = MessageForm(request.POST, language=request.LANGUAGE_CODE)
    if not form.is_valid():
        return private(
            HttpResponse(
                "Invalid clarification" if request.LANGUAGE_CODE == "en" else "Aclaración inválida",
                status=400,
            )
        )
    try:
        append(
            complaint_id,
            secret,
            **form.cleaned_data,
            actor_id=request.user.pk if request.user.is_authenticated else None,
        )
    except ValidationError:
        return private(
            HttpResponse(
                "Request changed; reload"
                if request.LANGUAGE_CODE == "en"
                else "Solicitud cambiada; recarga",
                status=409,
            )
        )
    return private(redirect("complaint_receipt", complaint_id=complaint_id, secret=secret))
