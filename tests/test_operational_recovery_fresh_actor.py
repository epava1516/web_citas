"""Fourteen finite service denials with legitimately cached, subsequently stale actors."""

import json
import os
import sys
import uuid
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.models import F
from django.utils import timezone
from test_media_operations import REASON, exhausted
from test_notice_operations import data, failed_report
from test_operational_recovery_authority_wait import _snapshot
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.mediafiles.models import Blob, MediaErasure, MediaErasureRecovery
from apps.safety import media_operations, notice_operations
from apps.safety.models import (
    ErasureExecution,
    NoticeRecovery,
    Report,
    ReportNotice,
    RightsAction,
    RightsRequest,
)

pytestmark = pytest.mark.django_db(transaction=True)
CHANGES = [
    "primary_permission", "review_permission", "inactive", "account_erased",
    "mfa_disabled", "mfa_version", "session_version",
]


def _owned_serial_here(request, settings):
    # Do not reuse the wait module's __file__-based selection guard.
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit finite owned serial stale-actor recovery negatives only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()


def _case(request, settings, monkeypatch, service):
    if service == "notice":
        notice, actor, _ = failed_report(request)
        assert notice.status == "failed" and notice.attempts == 5
        assert notice.report.receipt_expires_at > timezone.now()
        assert notice.report.actor_id != actor.pk
        queries = {
            "report": Report.objects.all(), "notice": ReportNotice.objects.all(),
            "notice_recovery": NoticeRecovery.objects.all(), "rights_action": RightsAction.objects.all(),
        }
        payload = data(notice.recovery_version)

        def invoke():
            return notice_operations.requeue(actor, "report", notice.pk, **payload)

        permissions = ("safety.manage_notice_delivery", "safety.review_report")
        return actor, permissions, queries, invoke
    case, actor, person, job = exhausted(request, settings, monkeypatch)
    job.refresh_from_db()  # exhausted updates the stored job with QuerySet.update.
    assert job.status == "failed" and job.attempts == 5
    assert job.blob.status == "erasing" and job.encrypted_paths
    assert actor.pk not in (case.actor_id, person.subject_id, person.agency.owner_id)
    queries = {
        "case": RightsRequest.objects.all(), "blob": Blob.objects.all(),
        "job": MediaErasure.objects.all(), "execution": ErasureExecution.objects.all(),
        "media_recovery": MediaErasureRecovery.objects.all(), "rights_action": RightsAction.objects.all(),
    }
    key, version = uuid.uuid4(), job.recovery_version

    def invoke():
        return media_operations.requeue(actor, case.pk, job.pk, key, version, REASON)

    permissions = ("mediafiles.manage_media_erasure", "safety.review_rights_request")
    return actor, permissions, queries, invoke


def _revoke_externally(actor, change, permissions):
    if change in {"primary_permission", "review_permission"}:
        permission_name = permissions[change == "review_permission"]
        app_label, codename = permission_name.split(".")
        permission = Permission.objects.get(content_type__app_label=app_label, codename=codename)
        external_actor = User.objects.get(pk=actor.pk)
        assert external_actor.user_permissions.filter(pk=permission.pk).exists()
        external_actor.user_permissions.remove(permission)
        assert not User.objects.get(pk=actor.pk).has_perm(permission_name)
        return
    values = {
        "inactive": {"is_active": False},
        "account_erased": {"account_erased_at": timezone.now()},
        "mfa_disabled": {"mfa_enabled": False},
        "mfa_version": {"mfa_version": F("mfa_version") + 1},
        "session_version": {"session_version": F("session_version") + 1},
    }
    assert User.objects.filter(pk=actor.pk).update(**values[change]) == 1
    fresh = User.objects.get(pk=actor.pk)
    if change == "inactive":
        assert not fresh.is_active
    elif change == "account_erased":
        assert fresh.account_erased_at is not None
    elif change == "mfa_disabled":
        assert not fresh.mfa_enabled
    else:
        assert getattr(fresh, change) == getattr(actor, change) + 1


@pytest.mark.parametrize("service", ["notice", "media"])
@pytest.mark.parametrize("change", CHANGES)
def test_recovery_service_denies_legitimately_cached_revoked_actor(
    request, settings, monkeypatch, record_property, service, change
):
    _owned_serial_here(request, settings)
    actor, permissions, queries, invoke = _case(request, settings, monkeypatch, service)
    assert actor.is_active and not actor.account_erased_at and actor.mfa_enabled
    assert not actor.is_superuser
    # Warm the real backend caches through legitimate permissions; never inject caches.
    assert all(actor.has_perm(permission) for permission in permissions)
    assert "_perm_cache" in actor.__dict__ and "_user_perm_cache" in actor.__dict__
    cached_permissions = {
        name: frozenset(actor.__dict__[name])
        for name in ["_perm_cache", "_user_perm_cache", "_group_perm_cache"]
        if name in actor.__dict__
    }
    actor_fields = (actor.is_active, actor.account_erased_at, actor.mfa_enabled,
                    actor.mfa_version, actor.session_version)
    before = _snapshot(queries)
    observed = {"service": service, "revocation": change, "denied": False,
                "initial_permissions_legitimate": True, "domain_before": before,
                "scope": "Direct public requeue service denial; stale actor prepared by external ORM mutation. "
                         "User/permission setup excluded from business snapshot. No concurrency, latency, provider or worker claim."}
    try:
        _revoke_externally(actor, change, permissions)
        assert (actor.is_active, actor.account_erased_at, actor.mfa_enabled,
                actor.mfa_version, actor.session_version) == actor_fields
        assert all(actor.has_perm(permission) for permission in permissions)
        assert all(frozenset(actor.__dict__[name]) == value
                   for name, value in cached_permissions.items())
        with pytest.raises(PermissionDenied):
            invoke()
        observed["denied"] = True
        assert _snapshot(queries) == before
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["domain_after"] = _snapshot(queries)
        observed["domain_unchanged"] = observed["domain_after"] == before
        record_property("operational_recovery_fresh_actor", json.dumps(
            observed, allow_nan=False, sort_keys=True,
        ))
