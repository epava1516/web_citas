"""Seven native Group CRUD regressions, including deliberate own-role removal."""

import copy
import json
import os
import sys
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.test import Client
from django.utils import timezone
from test_owned_interactive_rights_profile import _digest, _files, _snapshot_digest, _state
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User

pytestmark = pytest.mark.django_db(transaction=True)


def _guard(request, settings):
    node_file = Path(str(request.node.path)).resolve()
    assert node_file.name in {"test_admin_group_crud.py", "test_admin_group_wait_variants.py"}
    explicit = any(Path(str(arg).split("::")[0]).resolve() == node_file
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL Group candidate regressions only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _permission(codename):
    return Permission.objects.get(content_type__app_label="auth", codename=codename)


def _actor(request, role, *, own_group=None):
    request.getfixturevalue("directory")
    actor = User.objects.get(username="fixture-v1-moderator")
    assert not actor.is_superuser and actor.is_active and actor.mfa_enabled
    assert actor.email_verified_at is not None and actor.account_erased_at is None
    actor.is_staff = True
    actor.save(update_fields=["is_staff"])
    actor.groups.clear()
    # No inherited or direct unrelated Group role can mask the required role.
    actor.user_permissions.set([_permission("view_group")])
    if own_group is None:
        actor.user_permissions.add(_permission(role))
    else:
        own_group.permissions.set([_permission(role)])
        actor.groups.add(own_group)
    actor = User.objects.get(pk=actor.pk)
    group_roles = {"auth.add_group", "auth.change_group", "auth.delete_group", "auth.view_group"}
    effective = actor.get_all_permissions() & group_roles
    assert effective == {"auth.view_group", "auth." + role}
    assert actor.user_permissions.filter(pk=_permission(role).pk).exists() is (own_group is None)
    client = Client()
    client.force_login(actor)
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session["account_version"] = actor.session_version
    session.save()
    return actor, client


def _group():
    return Group.objects.create(name="synthetic-native-group-" + uuid4().hex)


def _path(group=None, action="change"):
    if group is None:
        return "/en/admin/auth/group/" if action == "list" else "/en/admin/auth/group/add/"
    return f"/en/admin/auth/group/{group.pk}/{action}/"


def _post(client, path, data, observed=None):
    response = None
    try:
        response = client.post(path, data)
        if response.streaming:
            for _ in response.streaming_content:
                pass
        return response.status_code
    finally:
        if response is not None:
            response.close()
        if observed is not None:
            observed["response_obtained"] = response is not None
            observed["response_closed"] = response is None or response.closed


def _get(client, path):
    response = client.get(path)
    try:
        return response.status_code
    finally:
        response.close()


def _bulk_data(groups):
    return {"action": "delete_selected", "index": "0", "select_across": "0",
            "_selected_action": [str(group.pk) for group in groups], "post": "yes"}


def _transition(before, after, *, additions=None, deletions=None, updates=None):
    """Construct the exact allowed full state; never exclude an entire table."""
    expected = copy.deepcopy(before)
    for label, pks in (deletions or {}).items():
        if not pks <= set(expected[label]):
            return False
        for pk in pks:
            del expected[label][pk]
    for (label, pk), fields in (updates or {}).items():
        if pk not in expected[label]:
            return False
        expected[label][pk].update(fields)
    for label, pks in (additions or {}).items():
        if pks & set(expected[label]) or not pks <= set(after[label]):
            return False
        for pk in sorted(pks, key=str):
            expected[label][pk] = after[label][pk]
    # Snapshot keys may be UUIDs; hash only ordered row sequences.
    def normalized(value):
        return {label: sorted(rows.values(), key=lambda row: _digest(row))
                for label, rows in value.items()}
    return _digest(normalized(expected)) == _digest(normalized(after))


def _deleted_targets(before, groups):
    pks = {group.pk for group in groups}
    deleted = {Group._meta.label: pks}
    for model in (Group.permissions.through, User.groups.through):
        label = model._meta.label
        deleted[label] = {pk for pk, row in before[label].items() if row["group_id"] in pks}
    return deleted


def _new_ids(before, after, model):
    label = model._meta.label
    return set(after[label]) - set(before[label])


def _logs(before, after, actor, expected, flag, start, end, fields=None):
    """Expected maps object ID to native object_repr; both remain local."""
    ids = _new_ids(before, after, LogEntry)
    if len(ids) != len(expected):
        return ids, False
    content_type = ContentType.objects.get(app_label="auth", model="group")
    actual = {}
    for entry in LogEntry.objects.filter(pk__in=ids):
        valid = (entry.user_id == actor.pk and entry.content_type_id == content_type.pk
                 and entry.action_flag == flag and start <= entry.action_time <= end
                 and entry.object_id in expected and entry.object_repr == expected[entry.object_id])
        if not valid or entry.object_id in actual:
            return ids, False
        if flag == DELETION:
            if entry.change_message != "":
                return ids, False
        else:
            message = [{"added": {}}] if flag == ADDITION else [{"changed": {"fields": fields}}]
            try:
                actual_message = json.loads(entry.change_message)
            except (ValueError, TypeError):
                return ids, False
            if _digest(actual_message) != _digest(message):
                return ids, False
        actual[entry.object_id] = entry.object_repr
    return ids, set(actual) == set(expected)


def _actor_state(actor):
    return {field: getattr(actor, field) for field in (
        "is_active", "is_staff", "is_superuser", "mfa_enabled", "mfa_version",
        "session_version", "email_verified_at", "account_erased_at",
    )}


@pytest.mark.parametrize("operation", [
    "add", "permissions", "delete", "bulk", "own_change", "own_delete", "own_bulk",
])
def test_group_crud_and_intentional_own_authority_changes(
    request, settings, record_property, operation
):
    observed = {"operation": operation, "status": "not_started",
                "scope": "Native HTTP Group CRUD, minimal operation permission and exact state",
                "authentication_scope": "Native synthetic directory and session epochs; force_login",
                "timing_scope": "QA including setup and snapshots, not application latency"}
    started = perf_counter()
    try:
        _guard(request, settings)
        # Initialize directory before creating an own authority Group.
        request.getfixturevalue("directory")
        own = operation.startswith("own_")
        delete = operation in {"delete", "bulk", "own_delete", "own_bulk"}
        bulk = operation in {"bulk", "own_bulk"}
        role = "delete_group" if delete else "add_group" if operation == "add" else "change_group"
        target = _group() if operation != "add" else None
        targets = [target, _group()] if bulk else [target] if target else []
        pin = _group()
        actor, client = _actor(request, role, own_group=target if own else None)
        session_before, actor_before = _digest(dict(client.session)), _digest(_actor_state(actor))
        if operation == "add":
            path = _path()
        elif bulk:
            path = _path(action="list")
        else:
            path = _path(target, "delete" if delete else "change")
        assert _get(client, path) == 200
        # Form and native collector readiness is outside the compared mutation.
        before, files_before = _state(), _files(settings)
        updates, deletions, additions = {}, {}, {}
        new_name = "synthetic-new-group-" + uuid4().hex
        added_permission = _permission("add_group")
        data = (_bulk_data(targets) if bulk else {"post": "yes"} if delete else {
            "name": new_name if operation == "add" else target.name,
            "permissions": [str(added_permission.pk)] if operation == "permissions" else [],
            "_save": "Save",
        })
        begin = timezone.now()
        code = _post(client, path, data)
        end = timezone.now()
        after = _state()
        if operation == "add":
            new_groups = _new_ids(before, after, Group)
            observed["new_groups"] = len(new_groups)
            expected = {str(pk): new_name for pk in new_groups}
            additions[Group._meta.label] = new_groups
            flag, fields = ADDITION, None
            group_shape = len(new_groups) == 1 and all(
                row["name"] == new_name for pk, row in after[Group._meta.label].items()
                if pk in new_groups
            )
        else:
            expected = {str(group.pk): group.name for group in targets}
            flag, fields = (DELETION, None) if delete else (CHANGE, ["Permissions"])
            group_shape = True
            if delete:
                deletions = _deleted_targets(before, targets)
            elif own:
                through = Group.permissions.through
                deletions[through._meta.label] = {
                    pk for pk, row in before[through._meta.label].items()
                    if row["group_id"] == target.pk
                }
                group_shape = len(deletions[through._meta.label]) == 1
            else:
                through = Group.permissions.through
                new_through = _new_ids(before, after, through)
                additions[through._meta.label] = new_through
                group_shape = len(new_through) == 1 and all(
                    row["group_id"] == target.pk and row["permission_id"] == added_permission.pk
                    for pk, row in after[through._meta.label].items() if pk in new_through
                )
        log_ids, logs_valid = _logs(before, after, actor, expected, flag, begin, end, fields)
        additions[LogEntry._meta.label] = log_ids
        transition_valid = _transition(before, after, additions=additions,
                                       deletions=deletions, updates=updates)
        files_after = _files(settings)
        fresh = User.objects.get(pk=actor.pk)
        observed.update(
            status="observed", http_status=code, new_log_entries=len(log_ids),
            native_logs_valid=logs_valid, exact_transition_valid=transition_valid,
            requested_group_shape_valid=bool(group_shape),
            domain_before_sha256=_snapshot_digest(before), domain_after_sha256=_snapshot_digest(after),
            installed_models=len(before), files_before=files_before, files_after=files_after,
            files_unchanged=files_before == files_after,
            actor_state_unchanged=_digest(_actor_state(fresh)) == actor_before,
            session_unchanged=_digest(dict(client.session)) == session_before,
            effective_operation_permission_after=fresh.has_perm("auth." + role),
            unselected_pin_preserved=_digest(before[Group._meta.label][pin.pk]) == _digest(after[Group._meta.label].get(pin.pk)),
        )
        assert code == 302
        assert logs_valid and transition_valid and group_shape
        assert observed["files_unchanged"] and observed["unselected_pin_preserved"]
        assert observed["actor_state_unchanged"] and observed["session_unchanged"]
        assert observed["effective_operation_permission_after"] is (not own)
        if own:
            next_before, next_files = _state(), _files(settings)
            if operation == "own_change":
                # view_group permits readonly GET; only another write must fail.
                readonly_code = _get(client, _path(target))
                observed["next_readonly_get_status"] = readonly_code
                assert readonly_code == 200
                next_path = _path(target)
                next_data = {"name": target.name, "permissions": [], "_save": "Save"}
            else:
                # A vanished original target can redirect; test a surviving target.
                next_path = _path(pin, "delete")
                next_data = {"post": "yes"}
            next_code = _post(client, next_path, next_data)
            next_after, next_files_after = _state(), _files(settings)
            no_more_effect = _transition(next_before, next_after)
            observed.update(next_post_status=next_code, next_request_no_effect=no_more_effect,
                            next_request_files_unchanged=next_files == next_files_after)
            assert next_code == 403 and no_more_effect
            assert next_files == next_files_after
        observed["status"] = "passed"
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["case_seconds"] = perf_counter() - started
        record_property("owned_admin_group_crud", json.dumps(
            observed, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ))
