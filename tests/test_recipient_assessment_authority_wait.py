"""Immutable N09H baseline candidate: eight native recipient authority scenarios.

Explicit serial owned PostgreSQL only. Exact ciphertext forwarding observers do
not claim exhaustive projection coverage or provider/HTTP/worker verification.
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
from test_privacy_release import fresh
from test_rectification_authority_wait import _client, _files, _queries, _state
from test_rectification_final_authority_wait import _executed, _roles
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety import recipient_assessments, recipient_review, rectification_recipients
from apps.safety.models import (
    RightsAction,
    RightsRectificationRecipientAssessment,
    RightsRectificationRecipientReview,
)
from apps.safety.rights_actions import act

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independent synthetic recipient assessment evidence after owned row wait"
PURPOSE = "Inspect current synthetic recipient inventory and assessment evidence"
FAMILIES = ("assessment_inspect", "assessment_propose", "review_inspect", "review_review")
CASES = tuple((family, change) for change in ("valid", "permission") for family in FAMILIES)


def _owned_serial(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL recipient assessment diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _prepare(request, settings, monkeypatch, family):
    p = _executed(request, settings, monkeypatch, "prepare_review")
    case = p["case"]
    author = _roles(p["actor"])
    inventory = rectification_recipients.prepare(
        author, case.pk, p["execution"].pk, uuid4(), case.version, PURPOSE)
    p.update(actor=author, inventory=inventory, held=inventory,
             target=inventory.encrypted_inventory, module=recipient_assessments,
             permission="safety.review_rectification",
             boundary="Inventory_select_for_update_before_exact_encrypted_inventory_unseal")
    # Fixture oracle uses the native read, before admission and instrumentation.
    data = recipient_assessments.inspect(author, case.pk, inventory.pk, case.version, PURPOSE)
    decisions = {token: {"outcome": "not_disclosed", "reason": REASON, "evidence": REASON}
                 for token in recipient_assessments.targets(data)}
    p.update(data=data, decisions=decisions)
    if family.startswith("review_"):
        assessment = recipient_assessments.propose(
            author, case.pk, inventory.pk, uuid4(), case.version, decisions)
        case.refresh_from_db()
        act(author, case.pk, uuid4(), case.version, "unassign", REASON)
        case.refresh_from_db()
        reviewer = _roles(User.objects.get(pk=p["proposal"].action.actor_id))
        assert reviewer.pk != author.pk
        act(reviewer, case.pk, uuid4(), case.version, "claim", REASON)
        fresh(case, reviewer, _client(reviewer), author, _client(author))
        p.update(actor=reviewer, assessment=assessment, held=assessment,
                 target=assessment.encrypted_decisions, module=recipient_review,
                 permission="safety.review_recipient_assessment",
                 boundary="Assessment_select_for_update_in_current_before_exact_encrypted_decisions_unseal")
        if family == "review_review":
            native_data, native_decisions = recipient_review.inspect(
                reviewer, case.pk, assessment.pk, case.version, PURPOSE)
            matches = native_data == data and native_decisions == decisions
            assert matches
    return p


def _invoke(p, family, actor, key):
    case = p["case"]
    if family == "assessment_inspect":
        result = recipient_assessments.inspect(actor, case.pk, p["inventory"].pk,
                                               case.version, PURPOSE)
        matches = result == p["data"]
    elif family == "assessment_propose":
        result = recipient_assessments.propose(actor, case.pk, p["inventory"].pk,
                                               key, case.version, p["decisions"])
        matches = (result.action.key == key and result.inventory_id == p["inventory"].pk
                   and result.source_digest == p["inventory"].source_digest
                   and result.proof_id == p["inventory"].proof_id)
        stored = recipient_assessments.unseal(result.encrypted_decisions)
        matches = matches and stored == p["decisions"]
    elif family == "review_inspect":
        data, decisions = recipient_review.inspect(actor, case.pk, p["assessment"].pk,
                                                  case.version, PURPOSE)
        matches = data == p["data"] and decisions == p["decisions"]
    else:
        result = recipient_review.review(actor, case.pk, p["assessment"].pk, key,
                                          case.version, "accepted", REASON)
        matches = (result.action.key == key and result.assessment_id == p["assessment"].pk
                   and result.outcome == "accepted"
                   and result.source_digest == p["assessment"].source_digest
                   and result.proof_id != p["assessment"].proof_id)
    assert matches


def _observe(monkeypatch, p, revoked, observed):
    original = p["module"].unseal

    def forward(*args, **kwargs):
        selected = bool(args) and args[0] == p["target"]
        if selected:
            observed["target_calls"] += 1
            if revoked.is_set():
                observed["target_calls_after_revocation"] += 1
        result = original(*args, **kwargs)
        if selected:
            observed["target_returns"] += 1
            if revoked.is_set():
                observed["target_returns_after_revocation"] += 1
        return result

    monkeypatch.setattr(p["module"], "unseal", forward)


def _positive(p, family, key, before, after, observed):
    operation = {"assessment_inspect": "recipients_read", "assessment_propose": "recipients_plan",
                 "review_inspect": "recipient_check_read", "review_review": "recipients_review"}[family]
    query = RightsAction.objects.filter(request=p["case"], actor=p["actor"], operation=operation)
    writes = family in {"assessment_propose", "review_review"}
    if writes:
        query = query.filter(key=key)
    assert query.exists()
    changed = {name for name in before["tables"] if before["tables"][name] != after["tables"][name]}
    expected = {"safety.RightsAction"}
    model = None
    if writes:
        model = (RightsRectificationRecipientAssessment if family == "assessment_propose"
                 else RightsRectificationRecipientReview)
        expected.update({"safety.RightsRequest", model._meta.label})
        assert model.objects.filter(action__key=key).count() == 1
    assert changed == expected
    for label in {"safety.RightsAction"} | ({model._meta.label} if model else set()):
        assert after["tables"][label]["count"] == before["tables"][label]["count"] + 1
    old, new = observed["minimal_before"], observed["minimal_after"]
    if writes:
        assert new["case_version"] == old["case_version"] + 1
        assert new["scope_status"] == "unverified"
        unchanged = set(old) - {"case_version", "scope_status"}
        assert {name: old[name] for name in unchanged} == {name: new[name] for name in unchanged}
    else:
        assert new == old


def _exercise(p, family, change, monkeypatch, settings, observed):
    actor, held = p["actor"], p["held"]
    permission = Permission.objects.get(content_type__app_label="safety",
                                        codename=p["permission"].split(".")[1])
    assert actor.user_permissions.filter(pk=permission.pk).exists()
    queries = _queries(actor, permission)
    for model in apps.get_app_config("auth").get_models(include_auto_created=True):
        queries[model._meta.label] = model.objects.all()
    before, files_before = _snapshot(queries), _files(settings)
    observed.update(domain_before=before, files_before=files_before,
                    minimal_before=_state(p["case"], p["person"]), boundary=p["boundary"],
                    held_model=held._meta.label, permission=p["permission"])
    key, revoked, statement = uuid4(), Event(), Event()
    _observe(monkeypatch, p, revoked, observed)
    runtime = {}
    pool = ThreadPoolExecutor(max_workers=1)
    future = None

    def worker():
        close_old_connections()

        def observe_statement(execute, sql, params, many, context):
            text = str(sql).upper()
            target = 'FROM "' + held._meta.db_table.upper() + '"'
            if "FOR UPDATE" in text and target in text and not statement.is_set():
                raw = context["connection"].connection
                runtime.update(pid=raw.info.backend_pid, raw=raw)
                observed["first_matching_statement_for_update"] = True
                observed["target_statement_seconds"] = time.monotonic() - observed["_started"]
                statement.set()
            return execute(sql, params, many, context)

        try:
            fresh_actor = User.objects.get(pk=actor.pk)
            assert fresh_actor.mfa_enabled and fresh_actor.is_active
            assert fresh_actor.has_perm(p["permission"])
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '35s'")
            with connection.execute_wrapper(observe_statement):
                try:
                    _invoke(p, family, fresh_actor, key)
                except PermissionDenied:
                    observed["status"] = "PermissionDenied"
                else:
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
                    assert not future.done(), "Operation finished before observed PostgreSQL wait"
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
                    fresh_actor = User.objects.get(pk=actor.pk)
                    assert not fresh_actor.has_perm(p["permission"])
                    observed["other_roles_preserved"] = all(
                        fresh_actor.has_perm("safety." + role) for role in (
                            "review_rights_request", "execute_rights_request", "respond_rights_request",
                            "manage_rights_assignment", "verify_rights_scope",
                            ("review_rectification" if family.startswith("review_")
                             else "review_recipient_assessment"))
                    )
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
            assert after == before
            assert observed["minimal_after"] == observed["minimal_before"]
            assert observed["target_calls_after_revocation"] == 0
            assert observed["target_returns_after_revocation"] == 0
        else:
            assert observed["status"] == "success"
            _positive(p, family, key, before, after, observed)
            assert observed["target_returns"] > 0
        assert observed["files_after"] == files_before
    finally:
        pool.shutdown(wait=future is None or future.done(), cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        try:
            observed.update(domain_after=_snapshot(queries), files_after=_files(settings),
                            minimal_after=_state(p["case"], p["person"]))
        except Exception as error:
            observed["final_snapshot_exception_type"] = type(error).__name__
    assert observed["thread_finished"] and observed["connections_closed"] and observed["holder_released"]


@pytest.mark.parametrize("family,change", CASES,
                         ids=[change + "-" + family for family, change in CASES])
def test_native_recipient_assessment_authority_after_owned_wait(
    request, settings, monkeypatch, record_property, family, change,
):
    observed = dict(label=family + ":" + change, status="not_started", actual_wait=False,
                    blocker_pids=[], permission_revoked=False, thread_finished=True,
                    connections_closed=True, holder_released=True, target_calls=0,
                    target_returns=0, target_calls_after_revocation=0,
                    target_returns_after_revocation=0, surface="native_service",
                    projection_oracle="exact selected ciphertext unseal only",
                    timing_scope="induced owned PostgreSQL wait; not application latency",
                    _started=time.monotonic())
    try:
        _owned_serial(request, settings)
        p = _prepare(request, settings, monkeypatch, family)
        _exercise(p, family, change, monkeypatch, settings, observed)
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["elapsed_seconds_including_setup_wait_cleanup"] = time.monotonic() - observed.pop("_started")
        record_property("recipient_assessment_authority_wait",
                        json.dumps(observed, allow_nan=False, sort_keys=True))
