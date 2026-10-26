"""Current native Admin GET surfaces and direct request-time role denials."""

import json
import os
from pathlib import Path
from time import perf_counter

import pytest
from capacity_runtime_role import _owned_database
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import Client
from test_admin_group_crud import _actor, _group, _permission
from test_owned_interactive_rights_profile import _files, _snapshot_digest, _state
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL Admin surface reference only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    _owned_database()


def _request(client, path, label, observations, expected, params=None):
    totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

    def observe(execute, sql, values, many, context):
        totals["sql_queries"] += 1
        began = perf_counter()
        try:
            return execute(sql, values, many, context)
        finally:
            totals["sql_execute_seconds"] += perf_counter() - began

    response = None
    try:
        began = perf_counter()
        with connection.execute_wrapper(observe):
            response = client.get(path, params or {})
            body = bytes(response.content)
        elapsed = perf_counter() - began
        assert response.status_code == expected
        assert "no-store" in response.headers["Cache-Control"]
        observations.append({"label": label, "http_status": response.status_code,
                             "body_bytes": len(body), "seconds_instrumented": elapsed,
                             **totals})
        return response
    finally:
        if response is not None:
            response.close()


def _unchanged(before, files, settings):
    assert _snapshot_digest(_state()) == _snapshot_digest(before)
    assert _files(settings) == files


@pytest.mark.parametrize("language", ["es", "en"])
def test_current_native_admin_surfaces(request, settings, record_property, language):
    _guard(request, settings)
    actor, client = _actor(request, "change_group")
    actor.user_permissions.add(_permission("add_group"), _permission("delete_group"))
    group = _group()
    assert set(admin.site._registry) == {Group}
    ct = ContentType.objects.get_for_model(Group)
    root = f"/{language}/admin/"
    target = root + f"auth/group/{group.pk}/"
    observations = []
    before, files = _state(), _files(settings)
    surfaces = [
        ("index", root, 200), ("app_list", root + "auth/", 200),
        ("login_admitted", root + "login/", 302),
        ("logout_GET_no_effect", root + "logout/", 405),
        ("password_change_form", root + "password_change/", 200),
        ("password_change_done", root + "password_change/done/", 200),
        ("jsi18n", root + "jsi18n/", 200),
        ("group_add_form", root + "auth/group/add/", 200),
        ("group_change_form", target + "change/", 200),
        ("group_delete_confirmation", target + "delete/", 200),
        ("group_history_empty", target + "history/", 200),
        ("legacy_group_redirect", target, 302),
        ("catch_all_missing", root + "synthetic-not-a-route/", 404),
        ("view_on_site_no_absolute_url", root + f"r/{ct.pk}/{group.pk}/", 404),
    ]
    for label, path, expected in surfaces:
        _request(client, path, label, observations, expected)
    autocomplete = {"app_label": "core", "model_name": "user", "field_name": "groups",
                    "term": group.name}
    response = _request(client, root + "autocomplete/", "autocomplete_group", observations,
                        200, autocomplete)
    assert response.json() == {"results": [{"id": str(group.pk), "text": group.name}],
                               "pagination": {"more": False}}
    for sample in range(6):
        response = _request(client, root + "auth/group/", f"group_list_{sample}",
                            observations, 200)
        assert group.name.encode() in response.content
    _unchanged(before, files, settings)
    # Commit the intentional permission removal before taking the denial baseline.
    actor.user_permissions.remove(_permission("view_group"), _permission("change_group"))
    assert not User.objects.get(pk=actor.pk).has_perm("auth.view_group")
    before = _state()
    for label, path, params in [
        ("no_view_change", target + "change/", None),
        ("no_view_history", target + "history/", None),
        ("no_view_list", root + "auth/group/", None),
        ("no_view_autocomplete", root + "autocomplete/", autocomplete),
    ]:
        _request(client, path, label, observations, 403, params)
    _unchanged(before, files, settings)
    User.objects.filter(pk=actor.pk).update(is_staff=False)
    before = _state()
    _request(client, root, "nonstaff_index", observations, 302)
    _request(client, target + "change/", "nonstaff_change", observations, 302)
    anonymous = Client()
    _request(anonymous, root, "anonymous_index", observations, 302)
    _unchanged(before, files, settings)
    record_property("n10c_admin_surface", json.dumps({
        "language": language, "samples": observations, "registry_only_group": True,
        "models_including_through": len(before), "media_files": files["count"],
        "rows_unchanged_per_phase": True, "files_unchanged": True,
        "scope": "Native GET surfaces and six changelist samples at fixed one-target "
                 "cohort; direct request-time permission/staff/anonymous denial, not "
                 "a concurrent revocation test. Force-login native synthetic actor with "
                 "current MFA epochs; no password/TOTP or POST/logout/password-change "
                 "ceremony. No traffic, backlog, browser, p95 or causal improvement claim.",
    }, sort_keys=True))
