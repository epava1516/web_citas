"""Four finite native PostgreSQL appeal authority wait diagnostics.

Hypothesis only until executed: control302 versus revoked403. QA timing includes
setup, induced wait and snapshots; it is not application latency or global QA.
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from queue import Queue
from time import perf_counter

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.contrib.auth.models import Permission
from django.db import connection, connections, transaction
from django.utils import timezone
from test_appeals import rejected  # noqa: F401
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_match_review import conflict  # noqa: F401
from test_operational_recovery_authority_wait import _snapshot
from test_owned_delivery_purge_profile import _digest, _tree
from test_photo_appeals import photo_case  # noqa: F401
from test_photo_restrictions import restricted  # noqa: F401
from test_photo_reuse_races import observe_blocked
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import User
from apps.listings import appeals, photo_appeals
from apps.listings.models import Appeal

pytestmark = pytest.mark.django_db(transaction=True)
ALLOWED_FIELDS = {"status", "result", "reason", "reviewer_id", "resolved_at"}
REASON = "Independent synthetic appeal review maintains the existing decision"


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL appeal authority diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()


def _prepare(request, operation):
    if operation == "publication":
        _, owner, revision, _, actor, client = request.getfixturevalue("rejected")
        response = owner.post(
            f"/es/draft/decisions/{revision.decisions.get().pk}/appeal/",
            {"explanation": "Please reconsider this synthetic publication decision"},
        )
        try:
            assert response.status_code == 302
        finally:
            response.close()
        appeal = Appeal.objects.get(decision__revision=revision)
        path = f"/es/moderation/appeals/{appeal.pk}/"
        module = appeals
    else:
        _, _, appeal, actor, client = request.getfixturevalue("photo_case")
        path = f"/es/moderation/photo-appeals/{appeal.pk}/"
        module = photo_appeals
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session["account_version"] = actor.session_version
    session.save()
    return appeal, actor, client, path, module


def _target(appeal):
    return type(appeal).objects.values().get(pk=appeal.pk)


def _queries(appeal, revoke):
    queries = {}
    for model in apps.get_models(include_auto_created=True):
        query = model.objects.all()
        # Control permits only the exact target's five resolution fields.
        # Negative includes the target and requires every persisted row unchanged.
        if model is type(appeal) and not revoke:
            query = query.exclude(pk=appeal.pk)
        queries[model._meta.label] = query
    return queries


@pytest.mark.parametrize("operation", ["publication", "photo"])
@pytest.mark.parametrize("revoke", [False, True], ids=["control", "permission_revoked"])
def test_review_revalidates_operator_after_appeal_wait(
    request, settings, monkeypatch, record_property, operation, revoke
):
    _profile(request, settings, monkeypatch, record_property, operation, revoke)


@pytest.mark.parametrize("change", ["session", "mfa", "inactive", "mfa_disabled", "erased"])
def test_publication_appeal_revalidates_operator_state_after_wait(
    request, settings, monkeypatch, record_property, change
):
    _profile(request, settings, monkeypatch, record_property, "publication", True, change)


def _profile(request, settings, monkeypatch, record_property, operation, revoke, change="permission"):
    observed = {"operation": operation, "revoked": revoke, "state_change": change if revoke else "none", "status": "not_started",
                "actual_wait": False, "surface": "native HTTP Client POST and PostgreSQL final appeal row lock",
                "timing_scope": "QA setup, induced wait and snapshots; not application latency"}
    started = perf_counter()
    runtime, pool, future = {}, None, None
    try:
        _guard(request, settings)
        appeal, actor, client, path, module = _prepare(request, operation)
        permission = Permission.objects.get(content_type__app_label="listings", codename="review_listing")
        assert actor.user_permissions.filter(pk=permission.pk).exists()
        assert User.objects.get(pk=actor.pk).has_perm("listings.review_listing")
        queries = _queries(appeal, revoke)
        media_before = _digest(_tree(settings.MEDIA_ROOT))
        pids = Queue()
        original_allowed = module.reviewer_allowed

        def observed_allowed(req):
            permitted = original_allowed(req)
            if "initial_allowed_observed" not in runtime:
                runtime["initial_allowed_observed"] = True
                observed["permission_cache_warmed"] = req.user.has_perm("listings.review_listing")
                observed["initial_gate_allowed"] = bool(permitted)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    pids.put(cursor.fetchone()[0])
            return permitted

        def worker():
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                response = client.post(path, {"result": "upheld", "reason": REASON})
                try:
                    # Consume any response stream before closure without emitting its bytes.
                    if response.streaming:
                        for _ in response.streaming_content:
                            pass
                    observed["http_status"] = response.status_code
                    return response.status_code
                finally:
                    response.close()
                    observed["response_closed"] = response.closed
            finally:
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        observed["setup_seconds"] = perf_counter() - started
        pool = ThreadPoolExecutor(max_workers=1)
        with monkeypatch.context() as patch:
            patch.setattr(module, "reviewer_allowed", observed_allowed)
            with transaction.atomic():
                type(appeal).objects.select_for_update().get(pk=appeal.pk)
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
                assert observed["initial_gate_allowed"] and observed["permission_cache_warmed"]
                if revoke:
                    if change == "permission":
                        actor.user_permissions.remove(permission)
                        effective_revoked = not User.objects.get(pk=actor.pk).has_perm("listings.review_listing")
                        assert effective_revoked
                        observed["effective_permission_revoked"] = effective_revoked
                    else:
                        values = {
                            "session": {"session_version": actor.session_version + 1},
                            "mfa": {"mfa_version": actor.mfa_version + 1},
                            "inactive": {"is_active": False},
                            "mfa_disabled": {"mfa_enabled": False},
                            "erased": {"account_erased_at": timezone.now()},
                        }[change]
                        User.objects.filter(pk=actor.pk).update(**values)
                        fresh = User.objects.get(pk=actor.pk)
                        assert all(getattr(fresh, key) == value for key, value in values.items())
                        observed["state_change_confirmed"] = True
                before = _snapshot(queries)
                other_before = _snapshot(_queries(appeal, False))
                target_before = _target(appeal)
                resolved_start = timezone.now()
            observed["revocation_committed_with_holder_release"] = revoke
            result = future.result(timeout=15)
        resolved_end = timezone.now()
        after, target_after = _snapshot(queries), _target(appeal)
        other_after = _snapshot(_queries(appeal, False))
        media_after = _digest(_tree(settings.MEDIA_ROOT))
        changed = sorted(key for key in target_before if target_before[key] != target_after[key])
        observed.update(domain_before_sha256=before["sha256"], domain_after_sha256=after["sha256"],
                        target_before_sha256=_digest(target_before), target_after_sha256=_digest(target_after),
                        target_changed_fields=changed, expected_changed_fields=[] if revoke else sorted(ALLOWED_FIELDS),
                        media_before_sha256=media_before, media_after_sha256=media_after,
                        expected_http_status=403 if revoke else 302,
                        other_models_before_sha256=other_before["sha256"],
                        other_models_after_sha256=other_after["sha256"],
                        observed_resolution_status=target_after["status"],
                        observed_resolution_result=target_after["result"],
                        reviewer_matches_actor=target_after["reviewer_id"] == actor.pk,
                        reason_matches_request=target_after["reason"] == REASON)
        # Emit the actual outcome before these deliberate security expectations fail
        # on an affected baseline; no xfail or conversion to a product PASS.
        assert other_before == other_after
        assert before == after
        assert media_before == media_after
        if revoke:
            assert _digest(target_before) == _digest(target_after)
        else:
            assert changed == sorted(ALLOWED_FIELDS)
            expected = dict(target_before)
            expected.update(status="resolved", result="upheld", reason=REASON,
                            reviewer_id=actor.pk, resolved_at=target_after["resolved_at"])
            assert _digest(expected) == _digest(target_after)
            timestamp_valid = resolved_start <= target_after["resolved_at"] <= resolved_end
            assert timestamp_valid
        assert result == (403 if revoke else 302)
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
        observed["cleanup_valid"] = cleanup_valid
        record_property("owned_appeal_operator_wait", json.dumps(observed, sort_keys=True, allow_nan=False))
        assert cleanup_valid
