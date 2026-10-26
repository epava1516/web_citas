"""Native Admin password/logout POST effects on explicitly admitted own sessions."""

import json
import os
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.models import Session
from django.db import connection
from django.test import Client
from test_admin_group_crud import _transition
from test_admin_login_epoch import PASSWORD, _request, _session
from test_owned_interactive_rights_profile import _files, _state
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)
NEW_PASSWORD = "Second-synthetic-admin-password!918273"


def _prepare(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL Admin account POST reference only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    _owned_database()
    request.getfixturevalue("directory")
    actor = User.objects.get(username="fixture-v1-moderator")
    assert actor.is_active and actor.email_verified_at and actor.mfa_enabled
    assert not actor.is_superuser and actor.account_erased_at is None
    actor.is_staff, actor.session_version = True, 1
    actor.set_password(PASSWORD)
    actor.save(update_fields=["is_staff", "session_version", "password"])
    clients = [Client(enforce_csrf_checks=True), Client(enforce_csrf_checks=True)]
    for client in clients:
        client.force_login(actor)
        session = client.session
        session["account_version"] = actor.session_version
        session["mfa_version"] = actor.mfa_version
        session.save()
    actor.refresh_from_db()
    return actor, *clients


def _same(before, settings, files):
    assert _transition(before, _state()) and _files(settings) == files


def _measure(client, method, path, data, label, samples):
    totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

    def observe(execute, sql, params, many, context):
        totals["sql_queries"] += 1
        began = perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            totals["sql_execute_seconds"] += perf_counter() - began

    began = perf_counter()
    response = None
    try:
        with connection.execute_wrapper(observe):
            response = getattr(client, method)(path, data or {})
            status, location = response.status_code, response.headers.get("Location", "")
            body_bytes = len(response.content)
        assert "no-store" in response.headers["Cache-Control"]
        samples.append({"label": label, "http_status": status, "body_bytes": body_bytes,
                        "seconds_instrumented": perf_counter() - began, **totals})
        return status, location
    finally:
        if response is not None:
            response.close()


@pytest.mark.parametrize("language", ["es", "en"])
def test_native_admin_password_change_and_logout(request, settings, record_property, language):
    observed = {"language": language, "status": "not_passed", "samples": [],
                "authentication_scope": "force_login plus explicit current account/MFA epochs; "
                                        "native password/logout POST and CSRF real, not a new "
                                        "login or TOTP ceremony; no concurrent wait or load claim"}
    try:
        actor, client, peer = _prepare(request, settings)
        root = f"/{language}/admin/"
        before, files = _state(), _files(settings)
        assert _request(client, "get", root + "password_change/")[0] == 200
        csrf = client.cookies[settings.CSRF_COOKIE_NAME].value
        own_row, own_data = _session(client, settings)
        peer_row, _ = _session(peer, settings)
        assert own_row is not None and peer_row is not None and own_row.pk != peer_row.pk
        assert own_data[SESSION_KEY] == str(actor.pk) and own_data["account_version"] == 1
        assert own_data["mfa_version"] == actor.mfa_version
        _same(before, settings, files)
        data = {"old_password": PASSWORD, "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD, "csrfmiddlewaretoken": csrf}
        assert _request(client, "post", root + "password_change/", data | {"csrfmiddlewaretoken": ""})[0] == 403
        _same(before, settings, files)
        assert _request(client, "post", root + "password_change/", data | {"old_password": PASSWORD + "wrong"})[0] == 200
        _same(before, settings, files)
        status, location = _measure(client, "post", root + "password_change/", data,
                                    "password_change", observed["samples"])
        assert status == 302 and urlsplit(location).path == root + "password_change/done/"
        actor.refresh_from_db()
        assert actor.check_password(NEW_PASSWORD) and not actor.check_password(PASSWORD)
        changed_row, changed_data = _session(client, settings)
        assert changed_row is not None and changed_row.pk not in {own_row.pk, peer_row.pk}
        assert changed_data[SESSION_KEY] == str(actor.pk)
        assert changed_data["account_version"] == 1 and changed_data["mfa_version"] == actor.mfa_version
        assert changed_data[HASH_SESSION_KEY] == actor.get_session_auth_hash()
        assert changed_data[HASH_SESSION_KEY] != own_data[HASH_SESSION_KEY]
        after_password = _state()
        assert _transition(before, after_password,
                           additions={Session._meta.label: {changed_row.pk}},
                           deletions={Session._meta.label: {own_row.pk}},
                           updates={(User._meta.label, actor.pk): {"password": actor.password}})
        assert _request(client, "get", root + "password_change/done/")[0] == 200
        assert _request(client, "get", root)[0] == 200
        _same(after_password, settings, files)
        status, location = _measure(peer, "get", root, None,
                                    "old_peer_closed", observed["samples"])
        assert status == 302 and urlsplit(location).path == root + "login/"
        assert _session(peer, settings)[0] is None
        after_peer = _state()
        assert _transition(after_password, after_peer,
                           deletions={Session._meta.label: {peer_row.pk}})
        assert _files(settings) == files
        assert _request(client, "get", root + "logout/")[0] == 405
        assert _request(client, "post", root + "logout/", {"csrfmiddlewaretoken": ""})[0] == 403
        _same(after_peer, settings, files)
        csrf = client.cookies[settings.CSRF_COOKIE_NAME].value
        status, location = _measure(client, "post", root + "logout/", {"csrfmiddlewaretoken": csrf},
                                    "logout", observed["samples"])
        assert status == 302 and urlsplit(location).path == f"/{language}/"
        assert _session(client, settings)[0] is None
        after_logout = _state()
        assert _transition(after_peer, after_logout,
                           deletions={Session._meta.label: {changed_row.pk}})
        assert _request(client, "get", root)[0] == 302
        _same(after_logout, settings, files)
        observed.update(status="passed", native_old_password_verified=True,
                        current_password_verified=True, own_session_rotated=True,
                        current_auth_hash=True, account_and_mfa_epochs_preserved=True,
                        peer_old_hash_closed=True, csrf_rejections_no_effect=True,
                        logout_deletes_exact_own_session=True, exact_phase_effects=True,
                        installed_models=len(before), media_files=files["count"], files_unchanged=True)
    finally:
        record_property("n10e_admin_account_post", json.dumps(observed, sort_keys=True))
