"""Native MFA continuation, rejection and admitted-epoch scope regressions."""

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import pyotp
import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.test import Client
from django.utils import timezone
from django.utils.crypto import salted_hmac
from test_admin_group_crud import _transition
from test_admin_login_epoch import PASSWORD, _request, _session
from test_owned_interactive_rights_profile import _files, _state
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import decrypt
from apps.core.models import RateWindow, User

pytestmark = pytest.mark.django_db(transaction=True)


def _prepare(request, settings, *, staff=True):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL native Admin login regressions only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    _owned_database()
    request.getfixturevalue("directory")
    actor = User.objects.get(username="fixture-v1-moderator")
    assert actor.is_active and actor.email_verified_at and actor.mfa_enabled
    assert actor.account_erased_at is None and not actor.is_superuser
    actor.is_staff, actor.session_version = staff, 1
    actor.set_password(PASSWORD)
    actor.save(update_fields=["is_staff", "session_version", "password"])
    return actor, Client(enforce_csrf_checks=True)


def _csrf(client, settings, path):
    assert _request(client, "get", path)[0] == 200
    return client.cookies[settings.CSRF_COOKIE_NAME].value


def _password(client, actor, csrf, language="en", *, password=PASSWORD):
    return _request(client, "post", f"/{language}/admin/login/", {
        "username": actor.username, "password": password, "csrfmiddlewaretoken": csrf,
        "next": f"/{language}/admin/",
    })


def _login_delta(before, after, actor, row, extra=None):
    return _transition(before, after, additions={Session._meta.label: {row.pk}},
                       updates={(User._meta.label, actor.pk): {
                           "last_login": actor.last_login, **(extra or {})}})


def _same(before, settings, files):
    assert _transition(before, _state()) and _files(settings) == files


def _new_rate_window(action, before, began, ended):
    key = salted_hmac("rate-window", action + ":127.0.0.1", algorithm="sha256").hexdigest()
    assert key not in before[RateWindow._meta.label]
    window = RateWindow.objects.get(pk=key)
    assert window.attempts == 1 and began <= window.starts_at <= ended
    return window.pk


def _publish(record_property, observed):
    observed.setdefault("status", "not_passed")
    record_property("n10d_admin_login_guard", json.dumps(observed, sort_keys=True))


@pytest.mark.parametrize("language", ["es", "en"])
def test_native_admin_password_then_totp(request, settings, record_property, language):
    observed = {"kind": "mfa_continuation", "language": language}
    try:
        actor, client = _prepare(request, settings)
        csrf = _csrf(client, settings, f"/{language}/admin/login/")
        before, files = _state(), _files(settings)
        status, location = _password(client, actor, csrf, language)
        assert status == 302 and urlsplit(location).path == f"/{language}/admin/"
        actor.refresh_from_db()
        row, data = _session(client, settings)
        assert row is not None and data["account_version"] == 1 and "mfa_version" not in data
        assert data[SESSION_KEY] == str(actor.pk)
        after_login = _state()
        assert _login_delta(before, after_login, actor, row)
        status, location = _request(client, "get", f"/{language}/admin/")
        assert status == 302 and urlsplit(location).path == f"/{language}/account/mfa/"
        _same(after_login, settings, files)
        csrf = _csrf(client, settings, f"/{language}/account/mfa/")
        _same(after_login, settings, files)
        totp = pyotp.TOTP(decrypt(actor.mfa_secret_encrypted))
        counter = totp.timecode(timezone.now())
        code = totp.at(counter * totp.interval)
        began = timezone.now()
        status, _ = _request(client, "post", f"/{language}/account/mfa/", {
            "code": code, "csrfmiddlewaretoken": csrf,
        })
        ended = timezone.now()
        assert status == 302
        window_pk = _new_rate_window("mfa-challenge", after_login, began, ended)
        actor.refresh_from_db()
        mfa_row, mfa_data = _session(client, settings)
        assert mfa_row is not None and mfa_row.pk != row.pk
        assert mfa_data[SESSION_KEY] == str(actor.pk)
        assert mfa_data["account_version"] == 1 and mfa_data["mfa_version"] == actor.mfa_version
        assert actor.mfa_last_counter == counter
        after_mfa = _state()
        assert _transition(after_login, after_mfa,
                           additions={Session._meta.label: {mfa_row.pk},
                                      RateWindow._meta.label: {window_pk}},
                           deletions={Session._meta.label: {row.pk}},
                           updates={(User._meta.label, actor.pk): {"mfa_last_counter": counter}})
        assert _request(client, "get", f"/{language}/admin/")[0] == 200
        _same(after_mfa, settings, files)
        observed.update(status="passed", native_password=True, native_totp=True,
                        session_rotated=True, account_epoch=1, mfa_epoch_current=True,
                        admin_after_mfa=200, rate_window_exact=True,
                        exact_phase_effects=True, files_unchanged=True,
                        installed_models=len(before), media_files=files["count"])
    finally:
        _publish(record_property, observed)


@pytest.mark.parametrize("rejection", ["password", "csrf", "nonstaff"])
def test_native_admin_login_rejects_invalid_admission(
    request, settings, record_property, rejection
):
    observed = {"kind": "rejection", "rejection": rejection}
    try:
        actor, client = _prepare(request, settings, staff=rejection != "nonstaff")
        csrf = _csrf(client, settings, "/en/admin/login/")
        before, files = _state(), _files(settings)
        status, _ = _password(client, actor, "" if rejection == "csrf" else csrf,
                              password=PASSWORD + "wrong" if rejection == "password" else PASSWORD)
        assert status == (403 if rejection == "csrf" else 200)
        row, data = _session(client, settings)
        assert row is None and SESSION_KEY not in data
        assert "account_version" not in data and "mfa_version" not in data
        _same(before, settings, files)
        observed.update(status="passed", http_status=status, no_auth_or_epoch=True,
                        exact_no_effect=True, files_unchanged=True,
                        installed_models=len(before), media_files=files["count"])
    finally:
        _publish(record_property, observed)


def test_revocation_after_real_password_check_is_not_adopted(
    request, settings, monkeypatch, record_property
):
    observed = {"kind": "late_epoch", "actual_wait_claimed": False}
    try:
        actor, client = _prepare(request, settings)
        csrf = _csrf(client, settings, "/en/admin/login/")
        before, files = _state(), _files(settings)
        original, checks = User.check_password, []

        def checked(user, raw):
            valid = original(user, raw)
            if valid and user.pk == actor.pk:
                assert User.objects.filter(pk=user.pk).update(session_version=user.session_version + 1) == 1
                checks.append(user.session_version)
            return valid

        monkeypatch.setattr(User, "check_password", checked)
        assert _password(client, actor, csrf)[0] == 302
        actor.refresh_from_db()
        row, data = _session(client, settings)
        assert checks == [1] and actor.session_version == 2
        assert row is not None and data["account_version"] == 1 and "mfa_version" not in data
        after_login = _state()
        assert _login_delta(before, after_login, actor, row, {"session_version": 2})
        status, location = _request(client, "get", "/en/admin/")
        assert status == 302 and urlsplit(location).path == "/en/admin/login/"
        final, data = _session(client, settings)
        assert final is None and SESSION_KEY not in data
        assert _transition(after_login, _state(), deletions={Session._meta.label: {row.pk}})
        assert _files(settings) == files
        observed.update(status="passed", admitted_epoch=1, database_epoch=2,
                        real_password_check_forwarded=True, account_gate_closed=True,
                        exact_phase_effects=True, files_unchanged=True,
                        installed_models=len(before), media_files=files["count"])
    finally:
        _publish(record_property, observed)


@pytest.mark.parametrize("flow", ["force_login", "core_signin"])
def test_admin_epoch_receiver_does_not_bind_other_login_flows(
    request, settings, record_property, flow
):
    observed = {"kind": "scope", "flow": flow}
    sender_key = "n10d.scope." + flow
    seen = []

    def observe(sender, request, user, **kwargs):
        seen.append({"account_present": "account_version" in request.session,
                     "mfa_present": "mfa_version" in request.session})

    try:
        actor, client = _prepare(request, settings)
        csrf = _csrf(client, settings, "/en/account/login/") if flow == "core_signin" else None
        before, files = _state(), _files(settings)
        user_logged_in.connect(observe, sender=User, dispatch_uid=sender_key, weak=False)
        began = timezone.now()
        if flow == "force_login":
            client.force_login(actor)
        else:
            assert _request(client, "post", "/en/account/login/", {
                "email": actor.email, "password": PASSWORD, "csrfmiddlewaretoken": csrf,
            })[0] == 302
        ended = timezone.now()
        assert seen == [{"account_present": False, "mfa_present": False}]
        actor.refresh_from_db()
        row, data = _session(client, settings)
        assert row is not None and data[SESSION_KEY] == str(actor.pk)
        after_login = _state()
        additions = {Session._meta.label: {row.pk}}
        if flow == "core_signin":
            window_pk = _new_rate_window("login", before, began, ended)
            additions[RateWindow._meta.label] = {window_pk}
        assert _transition(before, after_login, additions=additions,
                           updates={(User._meta.label, actor.pk): {"last_login": actor.last_login}})
        assert "mfa_version" not in data
        if flow == "force_login":
            assert "account_version" not in data
            status, location = _request(client, "get", "/en/admin/")
            assert status == 302 and urlsplit(location).path == "/en/admin/login/"
            final, _ = _session(client, settings)
            assert final is None
            assert _transition(after_login, _state(), deletions={Session._meta.label: {row.pk}})
        else:
            assert data["account_version"] == 1
            status, location = _request(client, "get", "/en/admin/")
            assert status == 302 and urlsplit(location).path == "/en/account/mfa/"
            _same(after_login, settings, files)
        assert _files(settings) == files
        observed.update(status="passed", observer_saw_no_admin_binding=True,
                        core_owned_binding_preserved=flow == "core_signin",
                        rate_window_exact=flow == "core_signin",
                        exact_phase_effects=True, files_unchanged=True,
                        installed_models=len(before), media_files=files["count"])
    finally:
        user_logged_in.disconnect(sender=User, dispatch_uid=sender_key)
        _publish(record_property, observed)
