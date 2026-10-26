"""Seven finite native Group Admin candidate waits; source variants, no prior PASS."""

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from time import perf_counter

import pytest
from django.contrib import admin
from django.contrib.admin.models import CHANGE, DELETION, LogEntry
from django.db import connection, connections, transaction
from django.utils import timezone
from test_admin_group_crud import (
    _actor,
    _actor_state,
    _bulk_data,
    _deleted_targets,
    _get,
    _group,
    _guard,
    _logs,
    _path,
    _permission,
    _post,
    _transition,
)
from test_owned_interactive_rights_profile import _digest, _files, _snapshot_digest, _state
from test_photo_reuse_races import observe_blocked
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)
VARIANTS = [
    ("delete", "none"), ("delete", "permission"),
    ("bulk", "none"), ("bulk", "permission"),
    ("change", "session"), ("change", "mfa"), ("change", "staff"),
]


@pytest.mark.parametrize("operation,intervention", VARIANTS, ids=[
    "delete_control", "delete_revoked", "bulk_control", "bulk_revoked",
    "change_session", "change_mfa", "change_staff",
])
def test_group_admin_current_authority_after_native_target_wait(
    request, settings, monkeypatch, record_property, operation, intervention
):
    negative = intervention != "none"
    observed = {"operation": operation, "intervention": intervention, "status": "not_started",
                "expected_http_status": 403 if negative else 302, "actual_wait": False,
                "scope": "Native HTTP, actual registered ModelAdmin forwarding observer and PG row wait",
                "timing_scope": "QA setup, induced wait, snapshots and cleanup; not app latency"}
    started = perf_counter()
    runtime, pool, future = {}, None, None
    try:
        _guard(request, settings)
        role = "change_group" if operation == "change" else "delete_group"
        actor, client = _actor(request, role)
        original_actor = _actor_state(actor)
        original_session = _digest(dict(client.session))
        targets = [_group(), _group()] if operation == "bulk" else [_group()]
        pin = _group()
        for group in [*targets, pin]:
            assert not group.permissions.exists() and not group.user_set.exists()
        path = _path(action="list") if operation == "bulk" else _path(
            targets[0], "change" if operation == "change" else "delete",
        )
        assert _get(client, path) == 200
        permission = _permission(role)
        files_before = _files(settings)
        original_log_ids = set(LogEntry.objects.values_list("pk", flat=True))
        before_grants = set(actor.user_permissions.values_list("pk", flat=True))
        before_memberships = set(actor.groups.values_list("pk", flat=True))
        ma = admin.site._registry[type(targets[0])]
        hook = "save_model" if operation == "change" else "delete_queryset" if operation == "bulk" else "delete_model"
        real_hook = getattr(ma, hook)
        pids = Queue()
        target_ids = {group.pk for group in targets}
        new_name = "synthetic-after-wait-" + targets[0].name.rsplit("-", 1)[1]

        def observer(req, *args, **kwargs):
            # Observe but always forward the original registered native operation.
            if not runtime.get("observed"):
                runtime["observed"] = True
                allowed = req.user.has_perm("auth." + role)
                seen = set(args[0].values_list("pk", flat=True)) if operation == "bulk" else {args[0].pk}
                observed.update(
                    initial_permission=bool(allowed),
                    permission_cache_warmed=hasattr(req.user, "_perm_cache"),
                    cached_operation_permission="auth." + role in getattr(req.user, "_perm_cache", set()),
                    actor_matches_request=req.user.pk == actor.pk,
                    actor_state_matches_admission=_digest(_actor_state(req.user)) == _digest(original_actor),
                    request_session_epochs_match=(req.session.get("account_version") == actor.session_version
                                                  and req.session.get("mfa_version") == actor.mfa_version),
                    exact_target_selection=seen == target_ids,
                    target_count=len(seen),
                )
                if operation == "change":
                    form, change = args[1], args[2]
                    observed["native_form_name_only"] = bool(change) and form.changed_data == ["name"]
                    observed["submitted_permissions_empty"] = not form.cleaned_data["permissions"].exists()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
            return real_hook(req, *args, **kwargs)

        def worker():
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                data = _bulk_data(targets) if operation == "bulk" else {
                    "name": new_name, "permissions": [], "_save": "Save",
                } if operation == "change" else {"post": "yes"}
                code = _post(client, path, data, observed)
                observed["http_status"] = code
                return code
            finally:
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        pool = ThreadPoolExecutor(max_workers=1)
        request_start = timezone.now()
        with monkeypatch.context() as patch:
            patch.setattr(ma, hook, observer)
            with transaction.atomic():
                type(targets[0]).objects.select_for_update().get(pk=targets[0].pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                future = pool.submit(worker)
                pid = pids.get(timeout=5)
                observed["distinct_postgresql_pids"] = pid != holder
                assert observed["distinct_postgresql_pids"]
                observe_blocked(pid, holder)
                assert not future.done()
                observed["actual_wait"] = True
                ready_fields = ["initial_permission", "permission_cache_warmed",
                                "cached_operation_permission", "actor_matches_request",
                                "actor_state_matches_admission", "request_session_epochs_match",
                                "exact_target_selection"]
                if operation == "change":
                    ready_fields += ["native_form_name_only", "submitted_permissions_empty"]
                observed["native_readiness_valid"] = all(observed.get(field) for field in ready_fields)
                assert observed["native_readiness_valid"]
                expected_actor = dict(original_actor)
                if intervention == "permission":
                    actor.user_permissions.remove(permission)
                elif intervention != "none":
                    values = {
                        "session": {"session_version": actor.session_version + 1},
                        "mfa": {"mfa_version": actor.mfa_version + 1},
                        "staff": {"is_staff": False},
                    }[intervention]
                    User.objects.filter(pk=actor.pk).update(**values)
                    expected_actor.update(values)
                fresh = User.objects.get(pk=actor.pk)
                observed.update(
                    intentional_actor_state_exact=_digest(_actor_state(fresh)) == _digest(expected_actor),
                    direct_grants_delta_exact=set(fresh.user_permissions.values_list("pk", flat=True)) == (
                        before_grants - {permission.pk} if intervention == "permission" else before_grants
                    ),
                    memberships_unchanged=set(fresh.groups.values_list("pk", flat=True)) == before_memberships,
                    effective_permission_after_intervention=fresh.has_perm("auth." + role),
                    session_material_unchanged=_digest(dict(client.session)) == original_session,
                )
                assert observed["intentional_actor_state_exact"] and observed["direct_grants_delta_exact"]
                assert observed["memberships_unchanged"] and observed["session_material_unchanged"]
                assert observed["effective_permission_after_intervention"] is (intervention != "permission")
                before = _state()
                visible = set(before[LogEntry._meta.label]) - original_log_ids
                observed["worker_logs_visible_before_release"] = len(visible)
            observed["intervention_committed_with_holder_release"] = negative
            observed["holder_released_after_intervention"] = not connection.in_atomic_block
            code = future.result(timeout=15)
        request_end = timezone.now()
        after, files_after = _state(), _files(settings)
        if operation == "change":
            expected_logs = {str(targets[0].pk): new_name}
            updates = {(targets[0]._meta.label, targets[0].pk): {"name": new_name}}
            deletions, flag, fields = {}, CHANGE, ["Name"]
        else:
            expected_logs = {str(group.pk): group.name for group in targets}
            updates, deletions, flag, fields = {}, _deleted_targets(before, targets), DELETION, None
        log_ids, log_valid = _logs(before, after, actor, expected_logs, flag,
                                  request_start, request_end, fields)
        native_effect = _transition(before, after, additions={LogEntry._meta.label: log_ids},
                                    deletions=deletions, updates=updates) and log_valid
        no_effect = _transition(before, after)
        groups_after = after[targets[0]._meta.label]
        observed.update(
            status="observed", new_log_entries=len(log_ids), native_logs_valid=log_valid,
            native_control_effect_valid=native_effect, no_additional_effect=no_effect,
            exact_expected_effect=no_effect if negative else native_effect,
            remaining_target_count=sum(group.pk in groups_after for group in targets),
            unselected_pin_preserved=_digest(before[pin._meta.label][pin.pk]) == _digest(groups_after.get(pin.pk)),
            domain_before_sha256=_snapshot_digest(before), domain_after_sha256=_snapshot_digest(after),
            installed_models=len(before), files_before=files_before, files_after=files_after,
            files_unchanged=files_before == files_after,
            final_actor_state_exact=_digest(_actor_state(User.objects.get(pk=actor.pk))) == _digest(expected_actor),
            final_session_unchanged=_digest(dict(client.session)) == original_session,
        )
        # Preserve actual HTTP/SQL/audit outcome before candidate expectations.
        assert observed["worker_logs_visible_before_release"] == 0
        assert observed["files_unchanged"] and observed["unselected_pin_preserved"]
        assert observed["final_actor_state_exact"] and observed["final_session_unchanged"]
        assert observed["exact_expected_effect"]
        assert code == (403 if negative else 302)
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
        observed["cleanup_valid"] = bool(observed["thread_finished"] and observed["holder_released"]
                                         and observed.get("worker_connections_closed", future is None)
                                         and observed.get("response_closed", future is None))
        observed["case_seconds"] = perf_counter() - started
        record_property("owned_admin_group_wait_variant", json.dumps(
            observed, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ))
        assert observed["cleanup_valid"]
