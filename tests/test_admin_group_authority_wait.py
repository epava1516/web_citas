"""Two native Admin POST diagnostics; no vulnerability claim before execution."""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from time import perf_counter
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.contrib import admin
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection, connections, transaction
from django.test import Client
from django.utils import timezone
from test_owned_interactive_rights_profile import (
    _assert_delta,
    _digest,
    _files,
    _snapshot_digest,
    _state,
)
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)


def _guard(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL Admin diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _matches_delta(before, after, *, additions=None, updates=None):
    try:
        _assert_delta(before, after, additions=additions, updates=updates)
    except AssertionError:
        return False
    return True


def _actor_state(actor):
    return {field: getattr(actor, field) for field in (
        "is_active", "is_staff", "is_superuser", "email_verified_at",
        "mfa_enabled", "mfa_version", "session_version", "account_erased_at",
    )}


@pytest.mark.parametrize("revoke", [False, True], ids=["control", "permission_revoked"])
def test_group_admin_rechecks_authority_after_update_wait(
    request, settings, monkeypatch, record_property, revoke
):
    observed = {
        "revoke": revoke, "status": "not_started", "actual_wait": False,
        "expected_http_status": 403 if revoke else 302,
        "surface": "Actual default GroupAdmin change POST; Group UPDATE row wait",
        "timing_scope": "QA setup, induced wait, snapshots and cleanup; not app latency",
        "authentication_scope": "Synthetic native directory actor, force_login and native "
                                "account/MFA session epochs; no password or TOTP ceremony",
    }
    started = perf_counter()
    runtime, pool, future = {}, None, None
    try:
        _guard(request, settings)
        request.getfixturevalue("directory")
        actor = User.objects.get(username="fixture-v1-moderator")
        actor.is_staff = True
        actor.save(update_fields=["is_staff"])
        permission = Permission.objects.get(content_type__app_label="auth", codename="change_group")
        view_permission = Permission.objects.get(content_type__app_label="auth", codename="view_group")
        actor.user_permissions.add(permission, view_permission)
        actor = User.objects.get(pk=actor.pk)
        actor_valid = (actor.is_active and actor.is_staff and not actor.is_superuser
                       and actor.email_verified_at is not None and actor.mfa_enabled
                       and actor.account_erased_at is None
                       and actor.has_perm("auth.change_group") and actor.has_perm("auth.view_group"))
        assert actor_valid
        original_actor = _actor_state(actor)
        client = Client()
        client.force_login(actor)
        session = client.session
        session["mfa_version"] = actor.mfa_version
        session["account_version"] = actor.session_version
        session.save()
        session_before = _digest(dict(client.session))
        group = Group.objects.create(name="synthetic-admin-original-" + uuid4().hex)
        new_name = "synthetic-admin-changed-" + uuid4().hex
        assert not group.permissions.exists() and not group.user_set.exists()
        group_content_type = ContentType.objects.get(app_label="auth", model="group")
        path = f"/en/admin/auth/group/{group.pk}/change/"
        response = client.get(path)
        try:
            assert response.status_code == 200
            assert response.resolver_match.view_name == "admin:auth_group_change"
            assert response.context["original"].pk == group.pk
        finally:
            response.close()
        # All setup/form/session effects precede the held row and baseline.
        actor = User.objects.get(pk=actor.pk)
        assert _digest(_actor_state(actor)) == _digest(original_actor)
        assert _digest(dict(client.session)) == session_before
        files_before = _files(settings)
        model_admin = admin.site._registry[Group]
        real_save_model = model_admin.save_model
        pids = Queue()

        def observe_save_model(req, obj, form, change):
            # Pure observer: always forward the original bound native method.
            if not runtime.get("save_observed"):
                runtime["save_observed"] = True
                allowed = req.user.has_perm("auth.change_group")
                observed.update(
                    initial_request_permission=bool(allowed),
                    permission_cache_warmed=hasattr(req.user, "_perm_cache"),
                    cached_effective_change_permission="auth.change_group" in getattr(req.user, "_perm_cache", set()),
                    actor_matches_request=req.user.pk == actor.pk,
                    native_change_flag=bool(change),
                    exact_target_seen=obj.pk == group.pk,
                    changed_fields_name_only=form.changed_data == ["name"],
                    submitted_permissions_empty=not form.cleaned_data["permissions"].exists(),
                    request_actor_state_matches=_digest(_actor_state(req.user)) == _digest(original_actor),
                    request_session_epochs_match=(req.session.get("mfa_version") == actor.mfa_version
                                                  and req.session.get("account_version") == actor.session_version),
                )
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
            return real_save_model(req, obj, form, change)

        def worker():
            connections.close_all()
            response = None
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                response = client.post(path, {"name": new_name, "permissions": [], "_save": "Save"})
                observed["response_obtained"] = True
                # No response body, URL, messages, cookies or IDs are recorded.
                if response.streaming:
                    for _ in response.streaming_content:
                        pass
                observed["http_status"] = response.status_code
                return response.status_code
            finally:
                if response is not None:
                    response.close()
                observed["response_closed"] = response is None or response.closed
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        pool = ThreadPoolExecutor(max_workers=1)
        with monkeypatch.context() as patch:
            patch.setattr(model_admin, "save_model", observe_save_model)
            with transaction.atomic():
                Group.objects.select_for_update().get(pk=group.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder_pid = cursor.fetchone()[0]
                future = pool.submit(worker)
                worker_pid = pids.get(timeout=5)
                observed["distinct_postgresql_pids"] = worker_pid != holder_pid
                assert observed["distinct_postgresql_pids"]
                observe_blocked(worker_pid, holder_pid)
                assert not future.done()
                observed["actual_wait"] = True
                readiness = all(observed.get(name) for name in (
                    "initial_request_permission", "permission_cache_warmed",
                    "cached_effective_change_permission", "actor_matches_request",
                    "native_change_flag", "exact_target_seen", "changed_fields_name_only",
                    "submitted_permissions_empty", "request_actor_state_matches", "request_session_epochs_match",
                ))
                observed["native_readiness_verified"] = readiness
                assert readiness
                grants_before = set(actor.user_permissions.values_list("pk", flat=True))
                groups_before = set(actor.groups.values_list("pk", flat=True))
                assert permission.pk in grants_before
                if revoke:
                    actor.user_permissions.remove(permission)
                grants_after = set(actor.user_permissions.values_list("pk", flat=True))
                groups_after = set(actor.groups.values_list("pk", flat=True))
                observed["direct_grant_delta_exact"] = grants_after == (
                    grants_before - {permission.pk} if revoke else grants_before
                )
                observed["actor_group_memberships_unchanged"] = groups_before == groups_after
                assert observed["direct_grant_delta_exact"]
                assert observed["actor_group_memberships_unchanged"]
                fresh = User.objects.get(pk=actor.pk)
                observed["fresh_effective_permission"] = fresh.has_perm("auth.change_group")
                observed["actor_state_unchanged_after_intervention"] = (
                    _digest(_actor_state(fresh)) == _digest(original_actor)
                )
                observed["session_unchanged_after_intervention"] = _digest(dict(client.session)) == session_before
                assert observed["fresh_effective_permission"] is (not revoke)
                assert observed["actor_state_unchanged_after_intervention"]
                assert observed["session_unchanged_after_intervention"]
                # Intentional grant removal is included in this full snapshot.
                before = _state()
                effect_start = timezone.now()
            observed["holder_released_after_intervention"] = not connection.in_atomic_block
            observed["revocation_committed_with_holder_release"] = revoke
            code = future.result(timeout=15)
        effect_end = timezone.now()
        after, files_after = _state(), _files(settings)
        label, log_label = Group._meta.label, LogEntry._meta.label
        target_before, target_after = before[label][group.pk], after[label][group.pk]
        new_logs = set(after[log_label]) - set(before[log_label])
        changed_fields = sorted(k for k in target_before if target_before[k] != target_after[k])
        audit_valid = False
        if len(new_logs) == 1:
            entry = LogEntry.objects.get(pk=next(iter(new_logs)))
            audit_valid = (entry.action_flag == CHANGE and entry.user_id == actor.pk
                           and entry.content_type_id == group_content_type.pk
                           and entry.object_id == str(group.pk) and entry.object_repr == new_name
                           and effect_start <= entry.action_time <= effect_end
                           and _digest(json.loads(entry.change_message)) == _digest([
                               {"changed": {"fields": ["Name"]}},
                           ]))
        no_effect = _matches_delta(before, after)
        native_effect = _matches_delta(
            before, after, additions={log_label: new_logs},
            updates={(label, group.pk): {"name": new_name}},
        ) and len(new_logs) == 1 and audit_valid
        groups_still_empty = not group.permissions.exists() and not group.user_set.exists()
        current_actor = User.objects.get(pk=actor.pk)
        observed.update(
            status="observed",
            domain_before_sha256=_snapshot_digest(before), domain_after_sha256=_snapshot_digest(after),
            installed_models=len(before), group_changed_fields=changed_fields,
            group_name_changed=target_before["name"] != target_after["name"],
            exact_requested_name=target_after["name"] == new_name,
            new_log_entries=len(new_logs), native_audit_valid=bool(audit_valid),
            full_snapshot_no_effect=bool(no_effect), full_snapshot_exact_native_change=bool(native_effect),
            files_before=files_before, files_after=files_after, files_unchanged=files_before == files_after,
            target_group_remains_without_members_or_permissions=groups_still_empty,
            actor_state_preserved=_digest(_actor_state(current_actor)) == _digest(original_actor),
            effective_permission_after=current_actor.has_perm("auth.change_group"),
            session_preserved=_digest(dict(client.session)) == session_before,
            actual_effect_shape="native_change_and_one_log" if native_effect else "none" if no_effect else "unexpected",
        )
        # Actual outcome is fully captured before deliberate security expectations.
        assert observed["files_unchanged"] and groups_still_empty
        assert observed["actor_state_preserved"] and observed["session_preserved"]
        assert observed["effective_permission_after"] is (not revoke)
        if revoke:
            assert no_effect
            assert code == 403
        else:
            assert native_effect and changed_fields == ["name"]
            assert code == 302
        observed["status"] = "passed"
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        if future is not None and not future.done():
            raw = runtime.get("raw")
            if raw is not None and not raw.closed:
                try:
                    raw.cancel()
                except Exception:
                    observed["cleanup_cancel_exception"] = True
            try:
                future.result(timeout=15)
            except Exception:
                observed["cleanup_worker_exception"] = True
        if pool is not None:
            pool.shutdown(wait=True, cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        observed["holder_released"] = not connection.in_atomic_block
        observed["case_seconds"] = perf_counter() - started
        cleanup_valid = (observed["thread_finished"] and observed["holder_released"]
                         and observed.get("worker_connections_closed", future is None)
                         and observed.get("response_closed", future is None))
        observed["cleanup_valid"] = bool(cleanup_valid)
        record_property("owned_admin_group_authority_wait", json.dumps(
            observed, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ))
        assert cleanup_valid
