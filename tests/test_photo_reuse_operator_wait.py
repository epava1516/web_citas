"""Finite native PostgreSQL wait diagnostic, not a latency benchmark."""

import hashlib
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
from django.test import Client
from test_operational_recovery_authority_wait import _snapshot
from test_owned_delivery_purge_profile import _digest, _tree
from test_photo_reuse_races import observe_blocked, setup_review
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.mediafiles.models import Blob
from apps.safety import photo_reintroduction_views

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("revoke", [False, True], ids=["control", "permission_revoked"])
def test_image_revalidates_operator_after_blob_wait(
    request, settings, monkeypatch, record_property, revoke
):
    observed = {"revoked": revoke, "status": "not_started", "actual_wait": False,
                "surface": "HTTP Django Client image; native PostgreSQL Blob lock",
                "timing_scope": "QA setup/induced wait/oracles; not application latency"}
    started = perf_counter()
    runtime, pool, future = {}, None, None
    try:
        if not any(Path(str(a).split("::")[0]).resolve() == Path(__file__).resolve()
                   for a in request.config.args):
            pytest.skip("Explicit serial owned PostgreSQL photo reuse operator diagnostic")
        assert not os.environ.get("PYTEST_XDIST_WORKER")
        assert not settings.PRODUCTION and not settings.RECOVERY_MODE
        assert connection.vendor == "postgresql"
        _owned_database()
        _, actor, _, _, _, _, _, candidate, read = setup_review(request, settings, monkeypatch)
        client = Client()
        client.force_login(actor)
        session = client.session
        session["mfa_version"] = actor.mfa_version
        session["account_version"] = actor.session_version
        session.save()
        root = settings.MEDIA_ROOT
        expected = candidate.uploaded_blob.derivative.read()
        candidate.uploaded_blob.derivative.close()
        assert expected
        permission = Permission.objects.get(codename="review_photo_reintroduction")
        assert actor.user_permissions.filter(pk=permission.pk).exists()
        models = {m._meta.label: m.objects.all()
                  for m in apps.get_models(include_auto_created=True)}
        media_before = _digest(_tree(root))
        path = f"/en/moderation/photo-reuse/{candidate.pk}/reads/{read.pk}/uploaded/"
        pids = Queue()
        original_allowed = photo_reintroduction_views.allowed

        def allowed(req):
            original_allowed(req)
            observed["permission_cache_warmed"] = req.user.has_perm("safety.review_photo_reintroduction")
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                pids.put(cursor.fetchone()[0])

        def worker():
            connections.close_all()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout TO '10s'")
                    runtime["raw"] = connection.connection
                response = client.get(path)
                try:
                    content = b"".join(response.streaming_content) if response.streaming else response.content
                    observed["http_status"] = response.status_code
                    observed["private_bytes"] = len(content) if response.status_code == 200 else 0
                    observed["content_matches_original"] = response.status_code == 200 and content == expected
                    observed["content_sha256"] = hashlib.sha256(content).hexdigest()
                    return response.status_code
                finally:
                    response.close()
                    observed["response_closed"] = response.closed
            finally:
                connections.close_all()
                observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

        pool = ThreadPoolExecutor(max_workers=1)
        with monkeypatch.context() as patch:
            patch.setattr(photo_reintroduction_views, "allowed", allowed)
            with transaction.atomic():
                held = max(candidate.uploaded_blob_id, candidate.disposition.blob_id)
                Blob.objects.select_for_update().get(pk=held)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid()")
                    holder = cursor.fetchone()[0]
                future = pool.submit(worker)
                worker_pid = pids.get(timeout=5)
                assert worker_pid != holder
                observe_blocked(worker_pid, holder)
                assert not future.done()
                observed["distinct_postgresql_pids"] = True
                observed["actual_wait"] = True
                if revoke:
                    actor.user_permissions.remove(permission)
                    assert not actor.user_permissions.filter(pk=permission.pk).exists()
                    assert not User.objects.get(pk=actor.pk).has_perm("safety.review_photo_reintroduction")
                    observed["effective_permission_revoked"] = True
                before = _snapshot(models)
            result = future.result(timeout=15)
            observed["revocation_committed_with_holder_release"] = revoke
        after = _snapshot(models)
        observed.update(domain_before_sha256=before["sha256"], domain_after_sha256=after["sha256"],
                        media_before_sha256=media_before, media_after_sha256=_digest(_tree(root)))
        assert before == after
        assert observed["media_before_sha256"] == observed["media_after_sha256"]
        assert observed["permission_cache_warmed"] and observed["actual_wait"]
        assert result == (403 if revoke else 200)
        assert observed["private_bytes"] == (0 if revoke else len(expected))
        assert revoke or observed["content_matches_original"]
        observed["status"] = "passed"
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        if future is not None and not future.done():
            raw = runtime.get("raw")
            if raw is not None and not raw.closed:
                raw.cancel()
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
        record_property("owned_photo_reuse_operator_wait", json.dumps(observed, sort_keys=True, allow_nan=False))
        assert cleanup_valid


@pytest.mark.parametrize("change", ["permission", "session", "mfa", "inactive", "mfa_disabled", "erased"])
def test_stale_operator_cannot_record_private_reuse_audit(
    request, settings, monkeypatch, record_property, change
):
    from uuid import uuid4

    from django.core.exceptions import PermissionDenied
    from django.utils import timezone

    from apps.safety.photo_reintroduction_review import inspect

    _service_guard(request, settings)
    _, actor, _, _, _, _, _, candidate, _ = setup_review(request, settings, monkeypatch)
    assert actor.has_perm("safety.review_photo_reintroduction")
    if change == "permission":
        actor.user_permissions.remove(Permission.objects.get(codename="review_photo_reintroduction"))
        assert not User.objects.get(pk=actor.pk).has_perm("safety.review_photo_reintroduction")
    else:
        values = {
            "session": {"session_version": actor.session_version + 1},
            "mfa": {"mfa_version": actor.mfa_version + 1},
            "inactive": {"is_active": False},
            "mfa_disabled": {"mfa_enabled": False},
            "erased": {"account_erased_at": timezone.now()},
        }
        User.objects.filter(pk=actor.pk).update(**values[change])
    queries = {m._meta.label: m.objects.all() for m in apps.get_models(include_auto_created=True)}
    before, media = _snapshot(queries), _digest(_tree(settings.MEDIA_ROOT))
    with pytest.raises(PermissionDenied):
        inspect(actor, candidate.pk, uuid4(), candidate.review_version,
                "Inspect private reuse after a stale operator authority change")
    after = _snapshot(queries)
    assert before == after and media == _digest(_tree(settings.MEDIA_ROOT))
    record_property("owned_photo_reuse_stale_operator", json.dumps({
        "change": change, "outcome": "PermissionDenied", "domain_before": before["sha256"],
        "domain_after": after["sha256"], "media_before": media,
        "media_after": _digest(_tree(settings.MEDIA_ROOT)),
        "scope": "Native inspect with original cached actor; no new wait or HTTP claim",
    }, sort_keys=True))


def test_revoked_operator_cannot_replay_private_reuse_decision(request, settings, monkeypatch, record_property):
    from uuid import uuid4

    from django.core.exceptions import PermissionDenied

    from apps.safety.photo_reintroduction_review import decide

    _service_guard(request, settings)
    _, actor, _, _, _, _, _, candidate, read = setup_review(request, settings, monkeypatch)
    assert actor.has_perm("safety.review_photo_reintroduction")
    key, reason, reference = uuid4(), "Independent current reuse evidence assessed before revocation", "synthetic-current-reference"
    first = decide(actor, candidate.pk, read.pk, key, 1, "authorize", reason, reference)
    assert first.pk
    actor.user_permissions.remove(Permission.objects.get(codename="review_photo_reintroduction"))
    assert not User.objects.get(pk=actor.pk).has_perm("safety.review_photo_reintroduction")
    queries = {m._meta.label: m.objects.all() for m in apps.get_models(include_auto_created=True)}
    before, media = _snapshot(queries), _digest(_tree(settings.MEDIA_ROOT))
    with pytest.raises(PermissionDenied):
        decide(actor, candidate.pk, read.pk, key, 1, "authorize", reason, reference)
    after = _snapshot(queries)
    assert before == after and media == _digest(_tree(settings.MEDIA_ROOT))
    record_property("owned_photo_reuse_revoked_decision", json.dumps({
        "outcome": "PermissionDenied", "first_decision_recorded": True,
        "domain_before": before["sha256"], "domain_after": after["sha256"],
        "media_before": media, "media_after": _digest(_tree(settings.MEDIA_ROOT)),
        "scope": "Native decide exact replay with original cached actor; no new wait/HTTP claim",
    }, sort_keys=True))


def _service_guard(request, settings):
    if not any(Path(str(a).split("::")[0]).resolve() == Path(__file__).resolve()
               for a in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL photo reuse operator diagnostic")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    _owned_database()
