import hashlib
import logging
import secrets
import uuid
from datetime import timedelta
from smtplib import SMTPException

from django import forms
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.crypto import constant_time_compare, salted_hmac
from django.views.decorators.http import require_http_methods, require_POST

from .models import AccountToken, LegalAcceptance, LegalDocument, RateWindow, User

logger = logging.getLogger(__name__)

ACCOUNT_DOCUMENTS = ("terms", "privacy")


def docs(language):
    available = list(
        LegalDocument.objects.filter(active=True, slug__in=ACCOUNT_DOCUMENTS).order_by(
            "-published_at", "-pk"
        )
    )
    canonical = {}
    for document in available:
        canonical.setdefault(document.slug, document.version)
    translated = [doc for doc in available if doc.language == language]
    # A stale translation must never allow switching language to evade updated terms.
    if any(doc.version != canonical.get(doc.slug) for doc in translated):
        return []
    return sorted(translated, key=lambda doc: doc.slug)


def limited(request, action, limit=10):
    # Never trust forwarded IP headers without an explicitly configured proxy.
    value = f"{action}:{request.META.get('REMOTE_ADDR', '')}"
    key = salted_hmac("rate-window", value, algorithm="sha256").hexdigest()
    now = timezone.now()
    with transaction.atomic():
        RateWindow.objects.get_or_create(key=key, defaults={"starts_at": now})
        window = RateWindow.objects.select_for_update().get(key=key)
        if window.starts_at < now - timedelta(minutes=15):
            window.starts_at, window.attempts = now, 0
        window.attempts += 1
        window.save(update_fields=["starts_at", "attempts"])
        return window.attempts > limit


class SignupForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(
        label="Contraseña / Password", widget=forms.PasswordInput, min_length=12
    )
    accept_terms = forms.BooleanField(label="Acepto las condiciones / I accept the terms")
    privacy_notice = forms.BooleanField(
        label="He leído la información de privacidad / I have read the privacy notice"
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.language = language
        self.documents = docs(language)
        for doc in self.documents:
            self.fields[f"version_{doc.slug}"] = forms.CharField(
                widget=forms.HiddenInput, initial=doc.version
            )

        if language == "en":
            self.fields["password"].label = "Password"
            self.fields["accept_terms"].label = "I accept the terms of use"
            self.fields["privacy_notice"].label = "I have read the privacy information"
        else:
            self.fields["password"].label = "Contraseña"
            self.fields["accept_terms"].label = "Acepto las condiciones de uso"
            self.fields["privacy_notice"].label = "He leído la información de privacidad"
        self.fields["password"].widget.attrs["autocomplete"] = "new-password"
        self.fields["email"].widget.attrs["autocomplete"] = "email"

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        data = super().clean()
        if {doc.slug for doc in self.documents} != set(ACCOUNT_DOCUMENTS):
            raise ValidationError(
                "Documents unavailable" if self.language == "en" else "Documentación no disponible"
            )
        for doc in self.documents:
            if data.get(f"version_{doc.slug}") != doc.version:
                raise ValidationError(
                    "Terms changed. Reload the form"
                    if self.language == "en"
                    else "Las condiciones han cambiado. Recarga el formulario"
                )
        if data.get("password"):
            validate_password(data["password"], User(email=data.get("email", "")))
        return data


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Contraseña / Password", widget=forms.PasswordInput)

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = "Password" if language == "en" else "Contraseña"
        self.fields["email"].widget.attrs["autocomplete"] = "username"
        self.fields["password"].widget.attrs["autocomplete"] = "current-password"


class EmailForm(forms.Form):
    email = forms.EmailField(label="Email")


class ResetForm(forms.Form):
    password = forms.CharField(
        label="Nueva contraseña / New password", widget=forms.PasswordInput, min_length=12
    )
    confirm = forms.CharField(
        label="Repetir contraseña / Repeat password", widget=forms.PasswordInput
    )

    def __init__(self, *args, user=None, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.language = language
        self.fields["password"].label = "New password" if language == "en" else "Nueva contraseña"
        self.fields["confirm"].label = (
            "Repeat password" if language == "en" else "Repetir contraseña"
        )
        for field in self.fields.values():
            field.widget.attrs["autocomplete"] = "new-password"

    def clean(self):
        data = super().clean()
        if data.get("password") != data.get("confirm"):
            raise ValidationError(
                "Passwords do not match"
                if self.language == "en"
                else "Las contraseñas no coinciden"
            )
        if data.get("password"):
            validate_password(data["password"], self.user)
        return data


def token_user_state(user):
    return salted_hmac(
        "account-token-state",
        f"{user.email}:{user.password}:{user.session_version}",
        algorithm="sha256",
    ).hexdigest()


def send_token(user, purpose, language):
    raw = secrets.token_urlsafe(32)
    now = timezone.now()
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        if user.account_erased_at:
            return None
        AccountToken.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(
            used_at=now
        )
        token = AccountToken.objects.create(
            user=user,
            user_state=token_user_state(user),
            digest=hashlib.sha256(raw.encode()).hexdigest(),
            purpose=purpose,
            expires_at=now + timedelta(hours=24 if purpose == "verify" else 1),
        )
    url = settings.PUBLIC_ORIGIN + f"/{language}/account/token/{token.pk}/{raw}/"
    try:
        send_mail(
            "Account confirmation" if language == "en" else "Confirmación de cuenta",
            ("Single-use link:\n" if language == "en" else "Enlace de un solo uso:\n") + url,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
    except (SMTPException, OSError):
        logger.error("account_email_delivery_failed", extra={"token_id": str(token.pk)})


@require_http_methods(["GET", "POST"])
def signup(request):
    form = SignupForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST":
        if limited(request, "signup", 5):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Document rows lock against concurrent version activation by supported services.
                    current = list(
                        LegalDocument.objects.select_for_update().filter(
                            pk__in=[d.pk for d in form.documents], active=True
                        )
                    )
                    if len(current) != 2:
                        form.add_error(
                            None,
                            "Terms updated"
                            if request.LANGUAGE_CODE == "en"
                            else "Condiciones actualizadas",
                        )
                        return render(
                            request, "core/form.html", {"form": form, "kind": "signup"}, status=400
                        )
                    user = User.objects.create_user(
                        username=uuid.uuid4().hex,
                        email=form.cleaned_data["email"],
                        password=form.cleaned_data["password"],
                        is_active=False,
                    )
                    for doc in current:
                        LegalAcceptance.objects.create(
                            user=user,
                            document=doc,
                            action="account_terms" if doc.slug == "terms" else "privacy_notice",
                        )
                    transaction.on_commit(lambda: send_token(user, "verify", request.LANGUAGE_CODE))
            except IntegrityError:
                # Identical response for an existing address. No privilege changes or password overwrite.
                pass
            return render(request, "core/account_sent.html")
    return render(
        request,
        "core/form.html",
        {"form": form, "kind": "signup", "documents": form.documents},
        status=400 if request.method == "POST" else 200,
    )


@require_http_methods(["GET", "POST"])
def signin(request):
    form = LoginForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST":
        if limited(request, "login"):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            candidate = User.objects.filter(email__iexact=email).first()
            user = authenticate(
                request,
                username=candidate.username if candidate else "unknown",
                password=form.cleaned_data["password"],
            )
            if user and user.email_verified_at:
                login(request, user)
                request.session["account_version"] = user.session_version
                return redirect("dashboard")
            form.add_error(
                None,
                "Invalid credentials"
                if request.LANGUAGE_CODE == "en"
                else "Credenciales no válidas",
            )
    return render(
        request,
        "core/form.html",
        {"form": form, "kind": "login"},
        status=400 if request.method == "POST" else 200,
    )


@require_POST
def signout(request):
    logout(request)
    return redirect("home")


@require_http_methods(["GET", "POST"])
def recover(request):
    form = EmailForm(request.POST or None)
    if request.method == "POST":
        if limited(request, "recover", 5):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form.is_valid():
            user = User.objects.filter(
                email__iexact=form.cleaned_data["email"],
                is_active=True,
                email_verified_at__isnull=False,
            ).first()
            if user:
                send_token(user, "reset", request.LANGUAGE_CODE)
            return render(request, "core/account_sent.html")
    return render(
        request,
        "core/form.html",
        {"form": form, "kind": "recover"},
        status=400 if request.method == "POST" else 200,
    )


@require_http_methods(["GET", "POST"])
def token_view(request, token_id, raw):
    digest = hashlib.sha256(raw.encode()).hexdigest()
    # GET previews only. A scanner following the URL must not consume a code.
    token = (
        AccountToken.objects.select_related("user")
        .filter(pk=token_id, digest=digest, used_at__isnull=True, expires_at__gt=timezone.now())
        .first()
    )
    if not token or not constant_time_compare(token.user_state, token_user_state(token.user)):
        return render(request, "core/token_invalid.html", status=400)
    form = (
        ResetForm(request.POST or None, user=token.user, language=request.LANGUAGE_CODE)
        if token.purpose == "reset"
        else None
    )
    if request.method == "POST":
        if limited(request, "token", 15):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form is None or form.is_valid():
            with transaction.atomic():
                user = User.objects.select_for_update().get(pk=token.user_id)
                locked = AccountToken.objects.select_for_update().filter(pk=token.pk).first()
                if not locked or user.account_erased_at:
                    return render(request, "core/token_invalid.html", status=400)
                now = timezone.now()
                if (
                    locked.used_at
                    or locked.expires_at <= now
                    or not constant_time_compare(locked.user_state, token_user_state(user))
                ):
                    return render(request, "core/token_invalid.html", status=400)
                if locked.purpose == "verify":
                    user.is_active = True
                    user.email_verified_at = now
                else:
                    user.set_password(form.cleaned_data["password"])
                    user.session_version += 1
                user.save()
                locked.used_at = now
                locked.save(update_fields=["used_at"])
            return redirect("login")
    response = render(request, "core/token.html", {"form": form, "purpose": token.purpose})
    response["Referrer-Policy"] = "same-origin"
    response["Cache-Control"] = "no-store"
    return response


@login_required
def dashboard(request):
    from apps.listings.history import rectification_history_ids
    from apps.listings.profile_contract import CURRENT_CONTRACT
    from apps.listings.profile_status import publication_summary, revision_summary

    from .agencies import person_queryset

    person = person_queryset(request.user).filter(individual=request.user).select_related(
        "listing"
    ).first()
    listing = getattr(person, "listing", None)
    revisions = (listing.revisions.filter(
        manager_version=person.manager_version, content_contract=CURRENT_CONTRACT,
    ).exclude(pk__in=rectification_history_ids()) if listing else None)
    draft = revisions.filter(status="draft").order_by("-created_at").first() if listing else None
    current = (revisions.filter(status__in=["draft", "processing", "pending", "rejected"])
               .order_by("-created_at").first() if listing else None)
    return render(request, "core/dashboard.html", {
        "own_profile": person, "own_listing": listing, "own_draft": draft,
        "publication_status": publication_summary(listing, request.LANGUAGE_CODE),
        "own_revision": current,
        "revision_status": revision_summary(current, request.LANGUAGE_CODE),
    })


@require_http_methods(["GET", "POST"])
def resend(request):
    form = EmailForm(request.POST or None)
    if request.method == "POST":
        if limited(request, "resend", 5):
            return HttpResponse(
                "Too many attempts" if request.LANGUAGE_CODE == "en" else "Demasiados intentos",
                status=429,
            )
        if form.is_valid():
            user = User.objects.filter(
                email__iexact=form.cleaned_data["email"],
                is_active=False,
                email_verified_at__isnull=True,
            ).first()
            if user:
                send_token(user, "verify", request.LANGUAGE_CODE)
            return render(request, "core/account_sent.html")
    return render(request, "core/form.html", {"form": form, "kind": "resend"})


class AcceptanceForm(forms.Form):
    accept_terms = forms.BooleanField(label="Acepto las condiciones / I accept the terms")
    privacy_notice = forms.BooleanField(
        label="He leído el aviso de privacidad / I have read the privacy notice"
    )

    def __init__(self, *args, language="es", **kwargs):
        super().__init__(*args, **kwargs)
        self.language = language
        self.fields["accept_terms"].label = (
            "I accept the terms of use" if language == "en" else "Acepto las condiciones de uso"
        )
        self.fields["privacy_notice"].label = (
            "I have read the privacy information"
            if language == "en"
            else "He leído la información de privacidad"
        )
        self.documents = docs(language)
        for document in self.documents:
            self.fields[f"version_{document.slug}"] = forms.CharField(
                widget=forms.HiddenInput, initial=document.version
            )

    def clean(self):
        data = super().clean()
        if {doc.slug for doc in self.documents} != set(ACCOUNT_DOCUMENTS):
            raise ValidationError(
                "Documents unavailable" if self.language == "en" else "Documentos no disponibles"
            )
        if any(data.get(f"version_{doc.slug}") != doc.version for doc in self.documents):
            raise ValidationError(
                "Documents updated. Reload"
                if self.language == "en"
                else "Documentos actualizados. Recarga"
            )
        return data


@login_required
@require_http_methods(["GET", "POST"])
def accept_current(request):
    form = AcceptanceForm(request.POST or None, language=request.LANGUAGE_CODE)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            current = list(
                LegalDocument.objects.select_for_update().filter(
                    pk__in=[d.pk for d in form.documents], active=True
                )
            )
            if len(current) != 2:
                return HttpResponse(
                    "Documents updated"
                    if request.LANGUAGE_CODE == "en"
                    else "Documentos actualizados",
                    status=409,
                )
            for document in current:
                LegalAcceptance.objects.get_or_create(
                    user=request.user,
                    document=document,
                    action="account_terms" if document.slug == "terms" else "privacy_notice",
                )
        return redirect("dashboard")
    return render(
        request,
        "core/form.html",
        {"form": form, "kind": "accept", "documents": form.documents},
        status=400 if request.method == "POST" else 200,
    )
