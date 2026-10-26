"""Four finite native processing inspection waits; no HTTP/latency claim."""

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
from django.apps import apps
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.db import connection, connections, transaction
from django.utils import timezone
from test_operational_recovery_authority_wait import _snapshot
from test_owned_delivery_purge_profile import _digest, _tree
from test_photo_reuse_races import observe_blocked
from test_processing_review import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety import processing_review
from apps.safety.crypto import unseal
from apps.safety.erasure_inventory import canonical
from apps.safety.models import ProcessingPlanRead, ProcessingPurposePlan, RightsAction
from apps.safety.rights import fingerprint

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Independently inspect the current synthetic processing purpose plan"


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL processing authority diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()


def _queries(key, new_control):
    queries = {}
    for model in apps.get_models(include_auto_created=True):
        query = model.objects.all()
        if new_control and model is RightsAction:
            query = query.exclude(key=key)
        elif new_control and model is ProcessingPlanRead:
            query = query.exclude(action__key=key)
        queries[model._meta.label] = query
    return queries


def _counts():
    return {"actions": RightsAction.objects.count(), "reads": ProcessingPlanRead.objects.count()}


def _assert_new(case, plan, actor, key, version, started, ended):
    action = RightsAction.objects.get(key=key)
    read = ProcessingPlanRead.objects.get(action=action)
    signature = fingerprint(canonical({"plan": str(plan.pk), "version": version,
        "operation": "inspect", "reason": REASON, "outcome": "",
        "plan_digest": fingerprint(plan.encrypted_plan)}))
    action_valid = (action.request_id == case.pk and action.actor_id == actor.pk
                    and action.expected_version == version and action.operation == "processing_inspect"
                    and action.payload_digest == signature and action.purged_at is None
                    and action.final_response_id is None and action.clarification_prompt == ""
                    and started <= action.created_at <= ended
                    and unseal(action.encrypted_reason) == {"reason": REASON})
    read_valid = (read.plan_id == plan.pk and read.proof_id == plan.proof_id
                  and read.plan_digest == fingerprint(plan.encrypted_plan)
                  and read.source_digest == plan.source_digest
                  and started <= read.created_at <= ended)
    assert action_valid and read_valid
    return read.pk


@pytest.mark.parametrize("mode", ["new", "replay"])
@pytest.mark.parametrize("revoke", [False, True], ids=["control", "permission_revoked"])
def test_inspection_revalidates_operator_after_plan_wait(
    request, settings, monkeypatch, record_property, mode, revoke
):
    observed = {"mode": mode, "revoked": revoke, "status": "not_started", "actual_wait": False,
                "contents_calls": 0, "contents_returns": 0, "private_return": False,
                "permission_denied": False, "surface": "native record inspect; PostgreSQL plan row wait",
                "timing_scope": "QA setup, induced wait and snapshots; not app latency; no HTTP"}
    started = perf_counter()
    runtime, pool, future = {}, None, None
    try:
        _guard(request, settings)
        case, _, _, plan, actor, client = prepared(request, settings, monkeypatch)
        session = client.session
        session["mfa_version"] = actor.mfa_version
        session["account_version"] = actor.session_version
        session.save()
        version, key = case.version, uuid4()
        assert plan.account_subject_id is not None
        permission = Permission.objects.get(content_type__app_label="safety", codename="review_processing_plan")
        assert actor.user_permissions.filter(pk=permission.pk).exists()
        # Setup oracle uses the native canonical transaction/locks, before observers.
        with transaction.atomic():
            _, _, checked_plan, _, manifest = processing_review.current(actor, case.pk, plan.pk, version)
            expected_body = processing_review.contents(checked_plan, manifest)
        expected_body_digest = _digest(expected_body)
        expected_read = None
        if mode == "replay":
            seed_read, seed_body = processing_review.record(actor, case.pk, plan.pk, key, version, "inspect", REASON)
            expected_read = seed_read.pk
            assert _digest(seed_body) == expected_body_digest
        queries = _queries(key, mode == "new" and not revoke)
        media_before = _digest(_tree(settings.MEDIA_ROOT))
        pids = Queue()
        original_authorize, original_contents = processing_review.authorize, processing_review.contents

        def observed_authorize(user, current_case, *args, **kwargs):
            fresh = original_authorize(user, current_case, *args, **kwargs)
            if "first_authorize" not in runtime:
                runtime["first_authorize"] = True
                observed["permission_cache_warmed"] = user.has_perm("safety.review_processing_plan")
                observed["fresh_authorize_allowed"] = fresh.has_perm("safety.review_processing_plan")
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
            return fresh

        def observed_contents(current_plan, manifest):
            observed["contents_calls"] += 1
            observed["contents_calls_after_revocation"] = observed.get("contents_calls_after_revocation", 0) + int(runtime.get("revocation_committed", False))
            body = original_contents(current_plan, manifest)
            observed["contents_returns"] += 1
            observed["contents_returns_after_revocation"] = observed.get("contents_returns_after_revocation", 0) + int(runtime.get("revocation_committed", False))
            observed["contents_body_sha256"] = _digest(body)
            return body

        def worker():
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                user = User.objects.get(pk=actor.pk)
                assert user.has_perm("safety.review_processing_plan")
                try:
                    row, body = processing_review.record(user, case.pk, plan.pk, key, version, "inspect", REASON)
                except PermissionDenied:
                    observed.update(permission_denied=True, actual_outcome="PermissionDenied")
                    return None
                observed.update(actual_outcome="returned", private_return=body is not None,
                                returned_body_sha256=_digest(body),
                                returned_existing_read=mode == "replay" and row.pk == expected_read)
                runtime["returned_read_pk"] = row.pk
                return row.pk
            except Exception as error:
                observed["worker_exception_type"] = type(error).__name__
                raise
            finally:
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        observed["setup_seconds"] = perf_counter() - started
        pool = ThreadPoolExecutor(max_workers=1)
        with monkeypatch.context() as patch:
            patch.setattr(processing_review, "authorize", observed_authorize)
            patch.setattr(processing_review, "contents", observed_contents)
            with transaction.atomic():
                ProcessingPurposePlan.objects.select_for_update().get(pk=plan.pk)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                future = pool.submit(worker)
                worker_pid = pids.get(timeout=5)
                distinct = worker_pid != holder
                assert distinct
                observe_blocked(worker_pid, holder)
                assert not future.done()
                observed.update(actual_wait=True, distinct_postgresql_pids=distinct)
                assert observed["permission_cache_warmed"] and observed["fresh_authorize_allowed"]
                if revoke:
                    actor.user_permissions.remove(permission)
                    effective_revoked = not User.objects.get(pk=actor.pk).has_perm("safety.review_processing_plan")
                    assert effective_revoked
                    observed["effective_permission_revoked"] = effective_revoked
                before, counts_before = _snapshot(queries), _counts()
                case_before = type(case).objects.values().get(pk=case.pk)
                resolved_start = timezone.now()
                # This private flag precedes commit; the worker cannot pass the
                # held plan lock until commit. It avoids a post-commit thread race.
                runtime["revocation_committed"] = revoke
            observed["revocation_committed_with_holder_release"] = revoke
            returned_read = future.result(timeout=15)
        ended = timezone.now()
        after, counts_after = _snapshot(queries), _counts()
        case_after = type(case).objects.values().get(pk=case.pk)
        media_after = _digest(_tree(settings.MEDIA_ROOT))
        observed.update(domain_before_sha256=before["sha256"], domain_after_sha256=after["sha256"],
                        counts_before=counts_before, counts_after=counts_after,
                        case_before_sha256=_digest(case_before), case_after_sha256=_digest(case_after),
                        case_version_unchanged=case_before["version"] == case_after["version"],
                        case_unchanged=_digest(case_before) == _digest(case_after),
                        media_before_sha256=media_before, media_after_sha256=media_after,
                        expected_body_sha256=expected_body_digest)
        # Outcomes are recorded before deliberate security expectations on the baseline.
        assert before == after and media_before == media_after
        assert observed["case_unchanged"] and observed["case_version_unchanged"]
        if revoke:
            assert counts_before == counts_after
            assert observed["permission_denied"] and not observed["private_return"]
            assert observed["contents_calls"] == 0 and observed["contents_returns"] == 0
        else:
            assert not observed["permission_denied"] and observed["private_return"]
            assert observed["returned_body_sha256"] == expected_body_digest
            assert observed["contents_calls"] == 1 and observed["contents_returns"] == 1
            if mode == "new":
                assert counts_after == {name: count + 1 for name, count in counts_before.items()}
                exact_read = _assert_new(case, plan, actor, key, version, resolved_start, ended)
                observed["new_read_action_link_valid"] = returned_read == exact_read
                assert observed["new_read_action_link_valid"]
            else:
                assert counts_before == counts_after and observed["returned_existing_read"]
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
                         and observed.get("worker_connections_closed", future is None))
        observed["cleanup_valid"] = cleanup_valid
        record_property("owned_processing_operator_wait", json.dumps(observed, sort_keys=True, allow_nan=False))
        assert cleanup_valid
