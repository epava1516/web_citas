"""Native password/CSRF Admin login must preserve admitted account epochs."""

import json
import os
from pathlib import Path
from urllib.parse import urlsplit

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.sessions.models import Session
from django.test import Client
from django.utils import timezone
from test_admin_group_crud import _transition
from test_owned_interactive_rights_profile import _files, _state
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)
PASSWORD = "Synthetic-native-admin-password!827361"


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL native Admin login diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    _owned_database()


def _session(client, settings):
    cookie = client.cookies.get(settings.SESSION_COOKIE_NAME)
    row = Session.objects.filter(session_key=cookie.value).first() if cookie and cookie.value else None
    return row, row.get_decoded() if row else {}


def _request(client, method, path, data=None):
    response = getattr(client, method)(path, data or {})
    try:
        return response.status_code, response.headers.get("Location", "")
    finally:
        response.close()


@pytest.mark.parametrize("epoch", [0, 1], ids=["initial_epoch", "revoked_epoch"])
def test_native_admin_password_login_preserves_account_epoch(
    request, settings, record_property, epoch
):
    observed = {"epoch": epoch, "status": "not_started",
                "scope": "Native Admin password POST with CSRF enforced, then Admin index "
                         "must route to MFA while preserving admitted session. No force_login, "
                         "no TOTP ceremony, no concurrent revocation or latency claim."}
    try:
        _guard(request, settings)
        request.getfixturevalue("directory")
        actor = User.objects.get(username="fixture-v1-moderator")
        assert actor.is_active and actor.mfa_enabled and actor.email_verified_at
        assert not actor.is_superuser and actor.account_erased_at is None
        actor.is_staff, actor.session_version = True, epoch
        actor.set_password(PASSWORD)
        actor.save(update_fields=["is_staff", "session_version", "password"])
        assert actor.check_password(PASSWORD)
        client = Client(enforce_csrf_checks=True)
        before, files = _state(), _files(settings)
        get_status, _ = _request(client, "get", "/en/admin/login/")
        assert get_status == 200 and settings.CSRF_COOKIE_NAME in client.cookies
        assert _transition(before, _state()) and _files(settings) == files
        csrf = client.cookies[settings.CSRF_COOKIE_NAME].value
        began = timezone.now()
        post_status, post_location = _request(client, "post", "/en/admin/login/", {
            "username": actor.username, "password": PASSWORD, "csrfmiddlewaretoken": csrf,
            "next": "/en/admin/",
        })
        ended = timezone.now()
        actor.refresh_from_db()
        post_row, post_data = _session(client, settings)
        post_state = _state()
        assert post_status == 302 and urlsplit(post_location).path == "/en/admin/"
        assert post_row is not None and post_data.get(SESSION_KEY) == str(actor.pk)
        assert {SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY} <= set(post_data)
        assert "mfa_version" not in post_data
        assert actor.last_login is not None and began <= actor.last_login <= ended
        post_effects = _transition(before, post_state,
                                   additions={Session._meta.label: {post_row.pk}},
                                   updates={(User._meta.label, actor.pk): {
                                       "last_login": actor.last_login}})
        assert post_effects and _files(settings) == files
        next_status, next_location = _request(client, "get", "/en/admin/")
        final_row, final_data = _session(client, settings)
        final_state = _state()
        # Describe the actual native effect first, even if the following expectation fails.
        if final_row is None:
            final_effects = _transition(post_state, final_state,
                                        deletions={Session._meta.label: {post_row.pk}})
        else:
            assert final_row.pk == post_row.pk
            final_effects = _transition(post_state, final_state,
                                        updates={(Session._meta.label, post_row.pk): {
                                            "session_data": final_row.session_data,
                                            "expire_date": final_row.expire_date}})
        observed.update(
            get_status=get_status, post_status=post_status, post_native_auth_succeeded=True,
            post_epoch_present="account_version" in post_data,
            post_epoch=post_data.get("account_version"),
            next_status=next_status,
            next_is_mfa=urlsplit(next_location).path == "/en/account/mfa/",
            next_is_admin_login=urlsplit(next_location).path == "/en/admin/login/",
            admitted_session_survives=final_data.get(SESSION_KEY) == str(actor.pk),
            final_epoch=final_data.get("account_version"),
            mfa_not_implicitly_granted="mfa_version" not in final_data,
            exact_native_login_effects=post_effects,
            exact_observed_index_effects=final_effects,
            files_unchanged=_files(settings) == files,
            models_including_through=len(before), media_files=files["count"],
        )
        assert final_effects and _files(settings) == files
        assert next_status == 302 and observed["next_is_mfa"]
        assert observed["admitted_session_survives"] and final_data["account_version"] == epoch
        assert observed["mfa_not_implicitly_granted"]
        observed["status"] = "passed"
    finally:
        if observed["status"] != "passed":
            observed["status"] = "not_passed"
        record_property("n10d_native_admin_login_epoch", json.dumps(observed, sort_keys=True))
