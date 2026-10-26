"""N09H candidate variants, separate from the immutable eight baseline cases.

Four genuine completed replays wait on owned PostgreSQL rows; four stale actor
variants make no wait claim. Synthetic native services only, no provider claim.
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from threading import Event
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import close_old_connections, connection, connections, transaction
from test_operational_recovery_authority_wait import _snapshot
from test_recipient_assessment_authority_wait import (
    REASON,
    _invoke,
    _observe,
    _prepare,
)
from test_rectification_authority_wait import _files, _queries, _state
from test_rectification_final_authority_wait import ROLES
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety import recipient_assessments, recipient_review

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL recipient variants only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _domain(actor, permission, *, exclude_grant):
    queries = _queries(actor, permission)
    if not exclude_grant:
        through = User.user_permissions.through
        queries[through._meta.label] = through.objects.all()
    for model in apps.get_app_config("auth").get_models(include_auto_created=True):
        queries[model._meta.label] = model.objects.all()
    return queries


def _metrics(label, *, wait):
    return dict(label=label, surface="native_service", status="not_started",
                actual_wait_claimed=wait, actual_wait=False, blocker_pids=[],
                permission_revoked=False, target_calls=0, target_returns=0,
                target_calls_after_revocation=0, target_returns_after_revocation=0,
                connections_closed=True, holder_released=True, thread_finished=True,
                projection_oracle="exact selected ciphertext unseal only")


def _permission(p):
    return Permission.objects.get(content_type__app_label="safety",
                                   codename=p["permission"].split(".")[1])


def _completed(p, family, actor, key, version):
    if family == "assessment_propose":
        return recipient_assessments.propose(actor, p["case"].pk, p["inventory"].pk,
                                             key, version, p["decisions"])
    return recipient_review.review(actor, p["case"].pk, p["assessment"].pk,
                                    key, version, "accepted", REASON)


def _run_replay(p, family, change, settings, monkeypatch, observed):
    actor, key, version = p["actor"], uuid4(), p["case"].version
    permission = _permission(p)
    assert all(actor.has_perm("safety." + role) for role in ROLES)
    completed = _completed(p, family, actor, key, version)
    held = p["inventory"] if family == "assessment_propose" else p["case"]
    queries = _domain(actor, permission, exclude_grant=True)
    before, files_before = _snapshot(queries), _files(settings)
    # _state refreshes the case; replay must retain the original payload version.
    minimal_before = _state(p["case"], p["person"])
    observed.update(domain_before=before, files_before=files_before,
                    minimal_before=minimal_before, held_model=held._meta.label,
                    boundary=("Inventory_before_assessment_replay" if family == "assessment_propose"
                              else "canonical_RightsRequest_before_review_replay"),
                    original_argument_version=version)
    revoked, statement = Event(), Event()
    _observe(monkeypatch, p, revoked, observed)
    runtime, pool, future = {}, ThreadPoolExecutor(max_workers=1), None

    def worker():
        close_old_connections()

        def observe_statement(execute, sql, params, many, context):
            text = str(sql).upper()
            target = 'FROM "' + held._meta.db_table.upper() + '"'
            if "FOR UPDATE" in text and target in text and not statement.is_set():
                raw = context["connection"].connection
                runtime.update(pid=raw.info.backend_pid, raw=raw)
                observed["first_matching_statement_for_update"] = True
                statement.set()
            return execute(sql, params, many, context)

        try:
            fresh_actor = User.objects.get(pk=actor.pk)
            assert all(fresh_actor.has_perm("safety." + role) for role in ROLES)
            assert fresh_actor.is_active and fresh_actor.mfa_enabled
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '35s'")
            with connection.execute_wrapper(observe_statement):
                try:
                    result = _completed(p, family, fresh_actor, key, version)
                except PermissionDenied:
                    observed["status"] = "PermissionDenied"
                else:
                    observed["same_completed_pk"] = result.pk == completed.pk
                    observed["status"] = "success"
        except Exception as error:
            observed["status"] = "unexpected:" + type(error).__name__
            raise
        finally:
            connections.close_all()
            observed["connections_closed"] = all(alias.connection is None for alias in connections.all())

    try:
        try:
            with transaction.atomic():
                type(held).objects.select_for_update().get(pk=held.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                observed["holder_pid"] = holder
                future = pool.submit(worker)
                deadline = time.monotonic() + 15
                while True:
                    assert not future.done(), "Replay finished before actual owned PostgreSQL wait"
                    if statement.is_set():
                        assert runtime["pid"] != holder
                        with connection.cursor() as cursor:
                            cursor.execute("SELECT pg_stat_clear_snapshot()")
                            cursor.execute("SELECT wait_event_type, pg_blocking_pids(pid) "
                                           "FROM pg_stat_activity WHERE pid=%s", [runtime["pid"]])
                            waiting = cursor.fetchone()
                        if waiting and waiting[0] == "Lock" and holder in waiting[1]:
                            observed.update(actual_wait=True, worker_pid=runtime["pid"],
                                            blocker_pids=list(waiting[1]))
                            break
                    assert time.monotonic() < deadline, "Owned PostgreSQL wait absent after15s"
                    time.sleep(.02)
                if change == "permission":
                    actor.user_permissions.remove(permission)
                    current_actor = User.objects.get(pk=actor.pk)
                    assert not current_actor.has_perm(p["permission"])
                    preserved = ["safety." + role for role in ROLES
                                 if "safety." + role != p["permission"]]
                    observed["other_roles_preserved"] = all(current_actor.has_perm(role) for role in preserved)
                    assert observed["other_roles_preserved"]
                    observed["permission_revoked"] = True
                    revoked.set()
        finally:
            observed["holder_released"] = not connection.in_atomic_block
            if future is not None:
                try:
                    future.result(timeout=45)
                except FutureTimeoutError:
                    observed["worker_timeout"] = True
                    raw = runtime.get("raw")
                    if raw is not None and not raw.closed and raw.info.backend_pid == runtime.get("pid"):
                        raw.cancel()
                    try:
                        future.result(timeout=5)
                    except Exception as error:
                        observed["cleanup_exception_type"] = type(error).__name__
                    raise
        after = _snapshot(queries)
        observed.update(domain_after=after, files_after=_files(settings),
                        minimal_after=_state(p["case"], p["person"]))
        assert observed["actual_wait"]
        if change == "permission":
            assert observed["status"] == "PermissionDenied"
            assert observed["target_calls_after_revocation"] == 0
            assert observed["target_returns_after_revocation"] == 0
        else:
            assert observed["status"] == "success" and observed["same_completed_pk"]
        assert after == before
        assert observed["files_after"] == files_before
        assert observed["minimal_after"] == minimal_before
        # A genuine historical replay needs no active private decode.
        assert observed["target_calls"] == 0 and observed["target_returns"] == 0
    finally:
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        try:
            observed.update(domain_after=_snapshot(queries), files_after=_files(settings),
                            minimal_after=_state(p["case"], p["person"]))
        except Exception as error:
            observed["final_snapshot_exception_type"] = type(error).__name__
    assert observed["thread_finished"] and observed["connections_closed"] and observed["holder_released"]


@pytest.mark.parametrize("family", ["assessment_propose", "review_review"])
@pytest.mark.parametrize("change", ["valid", "permission"])
def test_completed_recipient_replay_after_owned_wait(
    request, settings, monkeypatch, record_property, family, change,
):
    observed = _metrics("replay:" + family + ":" + change, wait=True)
    started = time.monotonic()
    try:
        _owned_serial(request, settings)
        p = _prepare(request, settings, monkeypatch, family)
        _run_replay(p, family, change, settings, monkeypatch, observed)
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["elapsed_seconds_including_setup_wait_cleanup"] = time.monotonic() - started
        record_property("recipient_authority_variant", json.dumps(observed, allow_nan=False, sort_keys=True))


STALE = (("assessment_inspect", "session"), ("review_inspect", "mfa"),
         ("assessment_inspect", "inactive"), ("review_inspect", "mfa_disabled"))


@pytest.mark.parametrize("family,change", STALE,
                         ids=[family + "-" + change for family, change in STALE])
def test_stale_native_recipient_actor_is_denied(
    request, settings, monkeypatch, record_property, family, change,
):
    observed = _metrics("stale:" + family + ":" + change, wait=False)
    started = time.monotonic()
    try:
        _owned_serial(request, settings)
        p = _prepare(request, settings, monkeypatch, family)
        actor, permission = p["actor"], _permission(p)
        # Cache every role on the original admitted instance before DB mutation.
        assert actor.is_active and actor.mfa_enabled
        assert all(actor.has_perm("safety." + role) for role in ROLES)
        changes = {
            "session": {"session_version": actor.session_version + 1},
            "mfa": {"mfa_version": actor.mfa_version + 1},
            "inactive": {"is_active": False},
            "mfa_disabled": {"mfa_enabled": False},
        }[change]
        assert User.objects.filter(pk=actor.pk).update(**changes) == 1
        current_actor = User.objects.get(pk=actor.pk)
        confirmed = all(getattr(current_actor, name) == value for name, value in changes.items())
        assert confirmed
        observed["persisted_change_confirmed"] = True
        # Include the intentional identity mutation and every grant in baseline.
        queries = _domain(actor, permission, exclude_grant=False)
        before, files_before = _snapshot(queries), _files(settings)
        minimal_before = _state(p["case"], p["person"])
        observed.update(domain_before=before, files_before=files_before,
                        minimal_before=minimal_before, boundary=p["boundary"])
        revoked = Event()
        revoked.set()
        _observe(monkeypatch, p, revoked, observed)
        try:
            _invoke(p, family, actor, uuid4())
        except PermissionDenied:
            observed["status"] = "PermissionDenied"
        else:
            observed["status"] = "success"
        after = _snapshot(queries)
        observed.update(domain_after=after, files_after=_files(settings),
                        minimal_after=_state(p["case"], p["person"]))
        assert observed["status"] == "PermissionDenied"
        assert after == before
        assert observed["files_after"] == files_before
        assert observed["minimal_after"] == minimal_before
        assert observed["target_calls"] == 0 and observed["target_returns"] == 0
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["elapsed_seconds_including_setup_cleanup"] = time.monotonic() - started
        record_property("recipient_authority_variant", json.dumps(observed, allow_nan=False, sort_keys=True))
