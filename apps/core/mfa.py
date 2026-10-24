import base64
import hashlib
import secrets
from datetime import datetime

import pyotp
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import salted_hmac
from django.views.decorators.http import require_http_methods

from .accounts import limited
from .encryption import encryption_cipher
from .models import RecoveryCode, User


def cipher():
    key = settings.MFA_ENCRYPTION_KEY
    if not key:
        if settings.MFA_ENCRYPTION_KEY_FALLBACKS:
            raise ImproperlyConfigured("Explicit active encryption key required with fallbacks")
        key = base64.urlsafe_b64encode(
            hashlib.sha256((settings.SECRET_KEY + ":dev-mfa").encode()).digest()
        )
    return encryption_cipher(key, settings.MFA_ENCRYPTION_KEY_FALLBACKS)


def encrypt(secret):
    return cipher().encrypt(secret.encode()).decode()


def decrypt(secret):
    return cipher().decrypt(secret.encode()).decode()


def recovery_digest(code):
    return salted_hmac("mfa-recovery", code.strip().upper(), algorithm="sha256").hexdigest()


def requires_mfa(user):
    return (
        user.mfa_enabled
        or user.is_staff
        or user.has_perm("safety.manage_notice_delivery")
        or user.has_perm("safety.review_report")
        or user.has_perm("safety.review_complaint")
        or user.has_perm("safety.respond_rights_request")
        or user.has_perm("safety.review_rights_request")
        or user.has_perm("safety.verify_rights_scope")
        or user.has_perm("safety.execute_rights_request")
        or user.has_perm("safety.extend_rights_deadline")
        or user.has_perm("core.review_agency")
        or user.has_perm("listings.review_listing")
        or user.role == "agency"
        or user.agency_memberships.filter(active=True).exists()
    )


def consume_totp(user, code):
    if not user.mfa_secret_encrypted:
        return False
    totp = pyotp.TOTP(decrypt(user.mfa_secret_encrypted))
    now = timezone.now()
    counter = totp.timecode(now)
    for delta in [0, -1, 1]:
        current = counter + delta
        if current > user.mfa_last_counter and secrets.compare_digest(
            totp.at(datetime.fromtimestamp(current * totp.interval, tz=now.tzinfo)), code.strip()
        ):
            user.mfa_last_counter = current
            user.save(update_fields=["mfa_last_counter"])
            return True
    return False


class PasswordForm(forms.Form):
    password = forms.CharField(
        label="Contraseña / Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = "Password" if language == "en" else "Contraseña"


class CodeForm(forms.Form):
    code = forms.CharField(
        label="Código TOTP o recuperación / TOTP or recovery code",
        max_length=40,
        widget=forms.TextInput(attrs={"autocomplete": "one-time-code"}),
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["code"].label = (
            "TOTP or recovery code" if language == "en" else "Código TOTP o recuperación"
        )


@login_required
@require_http_methods(["GET", "POST"])
def enroll(request):
    secret = None
    if request.user.mfa_enabled:
        return redirect("mfa_challenge")
    form = (
        CodeForm(request.POST or None, language=request.LANGUAGE_CODE)
        if request.POST.get("stage") == "confirm"
        else PasswordForm(request.POST or None, language=request.LANGUAGE_CODE)
    )
    if request.method == "POST":
        if limited(request, "mfa-enroll", 10):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                if user.account_erased_at or not user.is_active:
                    return HttpResponse(
                        "Account access revoked"
                        if request.LANGUAGE_CODE == "en"
                        else "Acceso a cuenta revocado",
                        status=409,
                    )
                if user.mfa_enabled:
                    return redirect("mfa_challenge")
                if request.POST.get("stage") == "confirm":
                    if consume_totp(user, form.cleaned_data["code"]):
                        user.mfa_enabled = True
                        user.mfa_version += 1
                        user.save(update_fields=["mfa_enabled", "mfa_version"])
                        codes = [secrets.token_hex(8).upper() for _ in range(10)]
                        RecoveryCode.objects.filter(user=user).delete()
                        RecoveryCode.objects.bulk_create(
                            [
                                RecoveryCode(user=user, digest=recovery_digest(code))
                                for code in codes
                            ]
                        )
                        request.session["mfa_version"] = user.mfa_version
                        return render(request, "core/mfa_recovery.html", {"codes": codes})
                    form.add_error(
                        None,
                        "Invalid code" if request.LANGUAGE_CODE == "en" else "Código no válido",
                    )
                    if user.mfa_secret_encrypted:
                        secret = decrypt(user.mfa_secret_encrypted)
                elif user.check_password(form.cleaned_data["password"]):
                    secret = pyotp.random_base32()
                    user.mfa_secret_encrypted = encrypt(secret)
                    user.save(update_fields=["mfa_secret_encrypted"])
                    form = CodeForm(language=request.LANGUAGE_CODE)
                else:
                    form.add_error(
                        None,
                        "Invalid credentials"
                        if request.LANGUAGE_CODE == "en"
                        else "Credenciales no válidas",
                    )
    return render(request, "core/mfa.html", {"form": form, "secret": secret, "enroll": True})


@login_required
@require_http_methods(["GET", "POST"])
def challenge(request):
    if not request.user.mfa_enabled:
        return redirect("mfa_enroll")
    form = CodeForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST":
        if limited(request, "mfa-challenge", 10):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form.is_valid():
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=request.user.pk)
                if user.account_erased_at or not user.is_active:
                    return HttpResponse(
                        "Account access revoked"
                        if request.LANGUAGE_CODE == "en"
                        else "Acceso a cuenta revocado",
                        status=409,
                    )
                code = form.cleaned_data["code"]
                valid = consume_totp(user, code)
                if not valid:
                    recovery = (
                        RecoveryCode.objects.select_for_update()
                        .filter(user=user, digest=recovery_digest(code), used_at__isnull=True)
                        .first()
                    )
                    if recovery:
                        recovery.used_at = timezone.now()
                        recovery.save(update_fields=["used_at"])
                        valid = True
                if valid:
                    request.session["mfa_version"] = user.mfa_version
                    request.session.cycle_key()
                    return redirect("dashboard")
                form.add_error(
                    None, "Invalid code" if request.LANGUAGE_CODE == "en" else "Código no válido"
                )
    return render(request, "core/mfa.html", {"form": form, "enroll": False})
