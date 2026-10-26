"""Eight finite real-view denials for a legitimate cached actor/request made stale."""

import json
import os
import sys
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.db import connection
from django.db.models import F
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone, translation
from test_operational_recovery_authority_wait import _snapshot
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_linking import ready

from apps.core.models import User
from apps.safety import rights
from apps.safety.models import RightsAccess, RightsAction, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)
CHANGES = [
    "review_permission", "inactive", "account_erased", "mfa_disabled",
    "mfa_version", "session_version", "request_mfa_version", "request_account_version",
]


def _owned_serial_here(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit finite owned serial rights inspection negatives only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()


def _actor_fields(actor):
    return (actor.is_active, actor.account_erased_at, actor.mfa_enabled,
            actor.mfa_version, actor.session_version)


def _invalidate_externally(actor, view_request, change):
    if change in {"request_mfa_version", "request_account_version"}:
        field = "mfa_version" if change == "request_mfa_version" else "account_version"
        view_request.session[field] += 1
        expected = actor.mfa_version if field == "mfa_version" else actor.session_version
        assert view_request.session[field] != expected
        assert _actor_fields(User.objects.get(pk=actor.pk)) == _actor_fields(actor)
        return
    if change == "review_permission":
        permission = Permission.objects.get(
            content_type__app_label="safety", codename="review_rights_request")
        external_actor = User.objects.get(pk=actor.pk)
        assert external_actor.user_permissions.filter(pk=permission.pk).exists()
        external_actor.user_permissions.remove(permission)
        assert not User.objects.get(pk=actor.pk).has_perm("safety.review_rights_request")
        return
    changes = {
        "inactive": {"is_active": False},
        "account_erased": {"account_erased_at": timezone.now()},
        "mfa_disabled": {"mfa_enabled": False},
        "mfa_version": {"mfa_version": F("mfa_version") + 1},
        "session_version": {"session_version": F("session_version") + 1},
    }
    assert User.objects.filter(pk=actor.pk).update(**changes[change]) == 1
    fresh = User.objects.get(pk=actor.pk)
    if change == "inactive":
        assert not fresh.is_active
    elif change == "account_erased":
        assert fresh.account_erased_at is not None
    elif change == "mfa_disabled":
        assert not fresh.mfa_enabled
    else:
        assert getattr(fresh, change) == getattr(actor, change) + 1


@pytest.mark.parametrize("change", CHANGES)
def test_inspection_view_denies_legitimately_cached_stale_authority(
    request, settings, record_property, change
):
    _owned_serial_here(request, settings)
    case, actor, client = ready(request)
    case.refresh_from_db()
    assert case.person_id is None and case.account_subject_id is None
    assert case.assigned_to_id == actor.pk and case.status == "reviewing"
    assert RightsAccess.objects.filter(request=case, actor=actor).count() == 1
    assert actor.is_active and not actor.account_erased_at and actor.mfa_enabled
    assert not actor.is_superuser and actor.is_authenticated
    assert _actor_fields(User.objects.get(pk=actor.pk)) == _actor_fields(actor)
    # Populate only the backend's natural caches while this actor is authorized.
    assert actor.has_perm("safety.review_rights_request")
    assert "_perm_cache" in actor.__dict__ and "_user_perm_cache" in actor.__dict__
    cached_permissions = {
        name: frozenset(actor.__dict__[name])
        for name in ["_perm_cache", "_user_perm_cache", "_group_perm_cache"]
        if name in actor.__dict__
    }
    original_fields = _actor_fields(actor)
    session = client.session
    assert session["mfa_version"] == actor.mfa_version
    assert session["account_version"] == actor.session_version
    with translation.override("en"):
        view_request = RequestFactory().post(
            reverse("rights_inspect", args=[case.pk]),
            {"purpose": "Synthetic current scoped inspection with original authority context"},
        )
        view_request.user = actor
        view_request.session = {
            "mfa_version": session["mfa_version"],
            "account_version": session["account_version"],
        }
        view_request.LANGUAGE_CODE = "en"
        queries = {
            "case": RightsRequest.objects.filter(pk=case.pk),
            "access": RightsAccess.objects.all(), "action": RightsAction.objects.all(),
        }
        before = _snapshot(queries)
        observed = {
            "change": change, "view": "rights_inspect", "status": None,
            "initial_permission_legitimate": True,
            "legitimate_initial_actor": True, "legitimate_initial_session": True,
            "natural_permission_cache_retained": False, "domain_before": before,
            "scope": "RequestFactory POST invokes the real decorated view. External ORM actor "
                     "mutation or explicit request-session mismatch; User/session setup excluded "
                     "from business snapshot. No middleware, HTTP transport, concurrency, "
                     "latency, decryption instrumentation, worker or provider claim.",
        }
        try:
            _invalidate_externally(actor, view_request, change)
            assert view_request.user is actor and _actor_fields(actor) == original_fields
            assert actor.has_perm("safety.review_rights_request")
            assert all(frozenset(actor.__dict__[name]) == values
                       for name, values in cached_permissions.items())
            observed["natural_permission_cache_retained"] = True
            response = rights.inspect(view_request, case.pk)
            observed["status"] = response.status_code
            assert response.status_code == 403
            assert response["Cache-Control"] == "private, no-store"
            assert response["X-Robots-Tag"] == "noindex, nofollow"
            assert response.content == b"Forbidden"
            assert _snapshot(queries) == before
            assert RightsAccess.objects.filter(request=case, actor=actor).count() == 1
        finally:
            if sys.exc_info()[0] is not None:
                observed["failure_type"] = sys.exc_info()[0].__name__
            observed["domain_after"] = _snapshot(queries)
            observed["domain_unchanged"] = observed["domain_after"] == before
            record_property("rights_inspection_fresh_actor", json.dumps(
                observed, allow_nan=False, sort_keys=True,
            ))
