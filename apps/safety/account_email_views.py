from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.debug import sensitive_variables
from django.views.decorators.http import require_GET, require_http_methods

from apps.core.accounts import limited

from .account_email_confirmation import inspect_token
from .models import RightsAccountEmailConfirmation
from .views import private


class ConfirmationForm(forms.Form):
    confirmed = forms.BooleanField(label="Confirmar este destino / Confirm this destination")


def cookie_name(confirmation_id):
    return "account_confirmation_" + confirmation_id.hex


@require_GET
@sensitive_variables()
def exchange(request, confirmation_id, raw):
    try:
        inspect_token(confirmation_id, raw)
    except (ValidationError, RightsAccountEmailConfirmation.DoesNotExist):
        response = private(
            render(request, "safety/account_email_confirm.html", {"unavailable": True}, status=400)
        )
    else:
        response = private(redirect("account_email_confirmation", confirmation_id=confirmation_id))
        from django.conf import settings

        response.set_signed_cookie(
            cookie_name(confirmation_id),
            raw,
            salt="account-email-confirm",
            max_age=86400,
            httponly=True,
            secure=settings.PRODUCTION,
            samesite="Strict",
        )
    response["Referrer-Policy"] = "no-referrer"
    return response


@require_http_methods(["GET", "POST"])
@sensitive_variables()
def confirm(request, confirmation_id):
    raw = request.get_signed_cookie(
        cookie_name(confirmation_id), default=None, salt="account-email-confirm", max_age=86400
    )
    if request.method == "POST" and limited(request, "account-email-confirm", 15):
        response = private(HttpResponse("Too many attempts / Demasiados intentos", status=429))
    else:
        form = ConfirmationForm(request.POST if request.method == "POST" else None)
        try:
            token = inspect_token(confirmation_id, raw)
            if request.method == "POST" and form.is_valid():
                token = inspect_token(confirmation_id, raw, confirm=True)
        except (ValidationError, RightsAccountEmailConfirmation.DoesNotExist):
            response = private(
                render(
                    request, "safety/account_email_confirm.html", {"unavailable": True}, status=400
                )
            )
        else:
            response = private(
                render(
                    request,
                    "safety/account_email_confirm.html",
                    {
                        "form": form,
                        "confirmed": bool(token.confirmed_at),
                    },
                    status=400 if request.method == "POST" and not form.is_valid() else 200,
                )
            )
    return response
