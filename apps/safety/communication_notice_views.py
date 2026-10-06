"""Recipient inbox: metadata on GET, audited POST read and exact acknowledgement."""

from django import forms
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import CharField, F, Q
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.views.decorators.http import require_http_methods

from apps.core.models import User

from .communication_notices import acknowledge, inspect_notice
from .models import RightsRecipientNotice
from .views import private


class NoticeForm(forms.Form):
    operation = forms.ChoiceField(
        choices=[("inspect", "Consultar / Inspect"), ("ack", "Confirmar recepción / Acknowledge")]
    )
    notice = forms.IntegerField(min_value=1, label="Notificación / Notice")
    read = forms.IntegerField(required=False, min_value=1, label="Consulta / Audited read")
    purpose = forms.CharField(
        required=False, min_length=10, max_length=200, label="Motivo de consulta / Access purpose"
    )

    def clean(self):
        values = super().clean()
        field = "purpose" if values.get("operation") == "inspect" else "read"
        if not values.get(field):
            self.add_error(field, "Obligatorio / Required")
        return values


def visible(user):
    profile = (
        Q(request__person__individual=user)
        | Q(request__person__agency__owner=user)
        | Q(
            request__person__assigned_editor=user,
            request__person__agency__memberships__user=user,
            request__person__agency__memberships__active=True,
        )
    )
    return (
        RightsRecipientNotice.objects.filter(recipient=user)
        .annotate(
            current_authority=Cast("request__person__manager_version", output_field=CharField()),
        )
        .filter(
            Q(
                request__person__isnull=True,
                request__account_subject=user,
                authorization_version="account",
            )
            | (profile & Q(authorization_version=F("current_authority")))
        )
        .distinct()
    )


@login_required
@sensitive_post_parameters()
@sensitive_variables()
@require_http_methods(["GET", "POST"])
def inbox(request):
    fresh = User.objects.get(pk=request.user.pk)
    if (
        not fresh.is_active
        or fresh.account_erased_at
        or not fresh.mfa_enabled
        or request.session.get("mfa_version") != fresh.mfa_version
        or request.user.session_version != fresh.session_version
    ):
        return private(HttpResponse("Forbidden", status=403))
    form = NoticeForm(request.POST or None)
    payload = None
    status = 200 if request.method == "GET" else 400
    if request.method == "POST" and form.is_valid():
        values = form.cleaned_data
        try:
            if values["operation"] == "inspect":
                read, payload = inspect_notice(request.user, values["notice"], values["purpose"])
                form = NoticeForm(
                    initial={"operation": "ack", "notice": values["notice"], "read": read.pk}
                )
                status = 200
            else:
                acknowledge(request.user, values["notice"], values["read"])
                return private(redirect("rights_recipient_notices"))
        except PermissionDenied:
            return private(HttpResponse("Forbidden", status=403))
        except ValidationError as error:
            form.add_error(None, error)
            status = 409
    return private(
        render(
            request,
            "safety/rights_recipient_notices.html",
            {
                "form": form,
                "payload": payload,
                "notices": Paginator(
                    visible(request.user)
                    .order_by("-pk")
                    .values("pk", "created_at", "acknowledged_at"),
                    50,
                ).get_page(request.GET.get("page")),
            },
            status=status,
        )
    )
