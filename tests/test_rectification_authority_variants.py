"""Native stale-actor and replay regressions; no PostgreSQL wait claim here."""

import json
import os
import sys
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection
from test_operational_recovery_authority_wait import _snapshot
from test_rectification_authority_wait import (
    _files,
    _invoke,
    _observe_helpers,
    _prepare,
    _queries,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL rectification variants only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _observe_denied(prepared, family, key, request, settings, monkeypatch, record_property, label):
    actor = prepared["actor"]
    permission = Permission.objects.get(
        content_type__app_label="safety", codename=prepared["permission"].split(".")[1],
    )
    queries = _queries(actor, permission)
    before, files_before = _snapshot(queries), _files(settings)
    metrics = {
        label + suffix: 0
        for label in ("account_source", "source_snapshot", "process_blob_delay")
        for suffix in ("_calls", "_returns", "_calls_after_revocation", "_returns_after_revocation")
    }
    revoked = Event()
    revoked.set()
    _observe_helpers(monkeypatch, revoked, metrics)
    data = {"variant": label, "surface": "native_service", "actual_wait_claimed": False}
    try:
        with pytest.raises(PermissionDenied):
            _invoke(prepared, family, actor, key, metrics)
        after, files_after = _snapshot(queries), _files(settings)
        data.update(domain_before=before, domain_after=after,
                    files_before=files_before, files_after=files_after)
        assert after == before and files_after == files_before
        assert metrics["account_source_returns"] == 0
        assert metrics["source_snapshot_returns"] == 0
        assert metrics["process_blob_delay_calls"] == 0
    finally:
        data["metrics"] = metrics
        if sys.exc_info()[0] is not None:
            data["failure_type"] = sys.exc_info()[0].__name__
        record_property("rectification_authority_variant", json.dumps(data, sort_keys=True))


@pytest.mark.parametrize("change", ["session", "mfa", "inactive", "mfa_disabled"])
def test_stale_native_actor_cannot_read_rectification_source(
    request, settings, monkeypatch, record_property, change,
):
    _owned_serial(request, settings)
    prepared = _prepare(request, settings, monkeypatch, "preview")
    actor = prepared["actor"]
    assert actor.is_active and actor.mfa_enabled and actor.has_perm(prepared["permission"])
    changes = {
        "session": {"session_version": actor.session_version + 1},
        "mfa": {"mfa_version": actor.mfa_version + 1},
        "inactive": {"is_active": False},
        "mfa_disabled": {"mfa_enabled": False},
    }
    assert User.objects.filter(pk=actor.pk).update(**changes[change]) == 1
    fresh = User.objects.get(pk=actor.pk)
    assert all(getattr(fresh, field) == value for field, value in changes[change].items())
    # Pass the admitted original instance: a fresh instance would adopt new epochs.
    _observe_denied(prepared, "preview", uuid4(), request, settings, monkeypatch,
                    record_property, "stale_actor:" + change)


@pytest.mark.parametrize("family", [
    "propose", "upload", "discard", "review", "notify", "execute", "recipients",
])
def test_completed_rectification_replay_requires_current_permission(
    request, settings, monkeypatch, record_property, family,
):
    _owned_serial(request, settings)
    prepared = _prepare(request, settings, monkeypatch, family)
    actor, key = prepared["actor"], uuid4()
    permission = Permission.objects.get(
        content_type__app_label="safety", codename=prepared["permission"].split(".")[1],
    )
    assert actor.has_perm(prepared["permission"])
    # Preserve the original request payload/version/key for its genuine replay.
    _invoke(prepared, family, actor, key, {})
    actor.user_permissions.remove(permission)
    assert not User.objects.get(pk=actor.pk).has_perm(prepared["permission"])
    _observe_denied(prepared, family, key, request, settings, monkeypatch,
                    record_property, "completed_replay:" + family)
