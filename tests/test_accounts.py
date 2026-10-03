import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core import mail
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone

from apps.core.accounts import send_token
from apps.core.models import AccountToken, LegalAcceptance, LegalDocument, User

PASSWORD = "A-long-random-passphrase!73"


@pytest.fixture
def legal_docs(transactional_db, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")


def registration(email="person@example.invalid", **extra):
    return {
        "email": email,
        "password": PASSWORD,
        "accept_terms": "on",
        "privacy_notice": "on",
        "version_terms": "dev-1",
        "version_privacy": "dev-1",
        **extra,
    }


def email_path():
    return re.search(r"http://localhost:8000([^\s]+)", mail.outbox[-1].body).group(1)


def verified_user():
    return User.objects.create_user(
        username="verified",
        email="verified@example.invalid",
        password=PASSWORD,
        email_verified_at=timezone.now(),
        is_active=True,
    )


def test_signup_requires_legal_and_stale_version_rejected(client, legal_docs):
    data = registration()
    del data["accept_terms"]
    assert client.post("/es/account/signup/", data).status_code == 400
    assert client.post("/es/account/signup/", registration(version_terms="old")).status_code == 400
    assert not User.objects.exists()
    assert not LegalAcceptance.objects.exists()


def test_signup_verified_login_replay_and_no_privilege_escalation(client, legal_docs):
    response = client.post(
        "/en/account/signup/", registration(is_staff="1", role="agency", is_superuser="1")
    )
    assert response.status_code == 200
    user = User.objects.get()
    assert not user.is_active and not user.is_staff and not user.is_superuser
    assert user.role == "visitor" and user.check_password(PASSWORD)
    assert LegalAcceptance.objects.filter(user=user).count() == 2
    assert all(a.document.language == "en" for a in LegalAcceptance.objects.all())
    assert PASSWORD not in mail.outbox[-1].body
    assert (
        client.post("/en/account/login/", {"email": user.email, "password": PASSWORD}).status_code
        == 400
    )
    assert "_auth_user_id" not in client.session
    path = email_path()
    assert path.startswith("/en/")
    assert client.get(path).status_code == 200
    user.refresh_from_db()
    assert not user.is_active  # Email scanner GET cannot confirm.
    assert client.post(path).status_code == 302
    user.refresh_from_db()
    assert user.is_active and user.email_verified_at
    assert client.post(path).status_code == 400
    assert (
        client.post("/en/account/login/", {"email": user.email, "password": PASSWORD}).status_code
        == 302
    )
    assert client.get("/en/account/").status_code == 200
    assert client.get("/en/account/logout/").status_code == 405
    assert client.post("/en/account/logout/").status_code == 302
    assert client.get("/en/account/").status_code == 302


def test_existing_email_and_recovery_do_not_enumerate(client, legal_docs):
    first = client.post("/es/account/signup/", registration()).content
    second = client.post(
        "/es/account/signup/", registration(email="PERSON@EXAMPLE.INVALID")
    ).content
    assert first == second
    assert User.objects.count() == 1
    assert len(mail.outbox) == 1
    user = verified_user()
    known = client.post("/es/account/recover/", {"email": user.email})
    unknown = client.post("/es/account/recover/", {"email": "missing@example.invalid"})
    assert known.content == unknown.content and known.status_code == unknown.status_code


def test_reset_one_use_expiry_and_existing_sessions_invalidated(client, legal_docs):
    user = verified_user()
    client.force_login(user)
    send_token(user, "reset", "es")
    path = email_path()
    new = "A-different-password!819"
    assert client.post(path, {"password": new, "confirm": new}).status_code == 302
    user.refresh_from_db()
    assert user.check_password(new) and user.session_version == 1
    assert client.get("/es/account/").status_code == 302
    assert client.post(path, {"password": PASSWORD, "confirm": PASSWORD}).status_code == 400
    send_token(user, "reset", "es")
    expired = email_path()
    AccountToken.objects.filter(used_at__isnull=True).update(
        expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert client.get(expired).status_code == 400
    user.refresh_from_db()
    assert user.check_password(new)


def test_csrf_throttle_and_token_headers(legal_docs):
    strict = Client(enforce_csrf_checks=True)
    assert strict.post("/es/account/signup/", registration()).status_code == 403
    assert not User.objects.exists()
    client = Client()
    for _ in range(5):
        assert (
            client.post("/es/account/recover/", {"email": "unknown@example.invalid"}).status_code
            == 200
        )
    assert (
        client.post("/es/account/recover/", {"email": "unknown@example.invalid"}).status_code == 429
    )
    user = verified_user()
    send_token(user, "verify", "es")
    path = email_path()
    response = client.get(path)
    assert response["Referrer-Policy"] == "same-origin"
    assert "no-store" in response["Cache-Control"]
    assert strict.post(path).status_code == 403
    token = AccountToken.objects.get(used_at__isnull=True)
    raw = path.strip("/").split("/")[-1]
    assert token.digest == hashlib.sha256(raw.encode()).hexdigest()
    assert client.post(path.replace(raw, raw + "x")).status_code == 400


@pytest.mark.django_db(transaction=True)
def test_concurrent_token_consumption(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    user = verified_user()
    send_token(user, "verify", "es")
    path = email_path()
    barrier = Barrier(2)

    def consume():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return Client().post(path).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: consume(), range(2)))
    assert sorted(responses) == [302, 400]
    assert AccountToken.objects.filter(used_at__isnull=False).count() == 1


def test_updated_terms_gate_retains_old_acceptance_and_supports_other_language(client, legal_docs):
    client.post("/es/account/signup/", registration())
    client.post(email_path())
    client.post("/es/account/login/", {"email": "person@example.invalid", "password": PASSWORD})
    assert client.get("/en/account/").status_code == 200
    old = LegalDocument.objects.get(slug="terms", language="es", active=True)
    old.active = False
    old.save()
    LegalDocument.objects.create(
        slug="terms",
        language="es",
        version="dev-2",
        title="Nuevas condiciones",
        body="Nuevo texto",
        published_at=timezone.now(),
    )
    response = client.get("/es/account/")
    assert response.status_code == 302 and response.url == "/es/account/accept/"
    assert client.post("/es/account/accept/", registration()).status_code == 400
    assert (
        client.post("/es/account/accept/", registration(version_terms="dev-2")).status_code == 302
    )
    assert client.get("/es/account/").status_code == 200
    assert LegalAcceptance.objects.filter(document=old).count() == 1
    assert LegalAcceptance.objects.filter(document__version="dev-2").count() == 1
    assert client.get("/en/account/").url == "/en/account/accept/"
    assert client.post("/en/account/accept/", registration()).status_code == 400


def test_resend_invalidates_older_token(client, legal_docs):
    client.post("/es/account/signup/", registration())
    original = email_path()
    client.post("/es/account/resend/", {"email": "person@example.invalid"})
    newer = email_path()
    assert original != newer
    assert client.post(original).status_code == 400
    assert client.post(newer).status_code == 302


def test_token_invalid_after_email_or_password_change(client, legal_docs):
    user = verified_user()
    send_token(user, "reset", "es")
    original = email_path()
    user.email = "changed@example.invalid"
    user.save(update_fields=["email"])
    assert client.post(original, {"password": PASSWORD, "confirm": PASSWORD}).status_code == 400


@pytest.mark.django_db(transaction=True)
def test_concurrent_signup_email_unicity(settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")
    barrier = Barrier(2)

    def signup_thread():
        close_old_connections()
        try:
            barrier.wait(timeout=5)
            return Client().post("/es/account/signup/", registration()).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: signup_thread(), range(2)))
    assert statuses == [200, 200]
    assert User.objects.count() == 1
    assert LegalAcceptance.objects.count() == 2
    assert AccountToken.objects.count() == 1


def test_email_delivery_failure_generic_response(client, legal_docs, monkeypatch):
    from smtplib import SMTPException

    def failed_delivery(*args, **kwargs):
        raise SMTPException("smtp unavailable")

    monkeypatch.setattr("apps.core.accounts.send_mail", failed_delivery)
    known = client.post("/es/account/signup/", registration())
    repeated = client.post("/es/account/signup/", registration())
    assert known.status_code == repeated.status_code == 200
    assert known.content == repeated.content
    assert User.objects.count() == 1
