"""Finite BEFORE Task.run profiles; real owned Redis publications, no worker.

Synthetic retained jobs are not admission/TTL evidence. Each phase has N=1;
SQL, dispatch and broker clocks overlap and must not be added. The two native
100-row bounds govern separate expiry and dispatch selections.
"""

import base64
import hashlib
import json
import os
import re
import sys
from datetime import timedelta
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.db import connection
from django.utils import timezone
from redis import Redis
from test_operational_recovery_authority_wait import _snapshot
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_jobs import enqueue, prepared

from apps.safety import rights_portability_jobs as jobs
from apps.safety.models import RightsPortabilityExportJob as Job
from apps.safety.tasks import generate_portability_export, reconcile_portability_export_jobs
from config.celery import app

pytestmark = pytest.mark.django_db(transaction=True)
PRIORITIES = ("", "\x06\x163", "\x06\x166", "\x06\x169")
TERMINAL_COLUMNS = {"state", "finished_at", "encrypted_reason", "lease_until"}


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str,
                                    separators=(",", ":")).encode()).hexdigest()


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL/Redis reconciliation profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()
    endpoint = urlparse(settings.CELERY_BROKER_URL)
    assert endpoint.scheme == "redis" and endpoint.hostname == "127.0.0.1"
    assert endpoint.path == "/0" and endpoint.port and endpoint.port != 6379
    run = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN", "")
    generation = os.environ.get("LOCAL_CI_TEST_QUEUE_GENERATION", "")
    assert re.fullmatch(r"\d{8}-\d{6}-[a-f0-9]{8}", run)
    assert re.fullmatch(r"t[a-f0-9]{31}", generation)
    prefix = settings.CELERY_BROKER_TRANSPORT_OPTIONS["global_keyprefix"]
    prefix_matches = prefix == f"clasificados:{generation}:"
    assert prefix_matches
    broker_matches = app.conf.broker_url == settings.CELERY_BROKER_URL
    assert broker_matches
    transport_matches = app.conf.broker_transport_options == settings.CELERY_BROKER_TRANSPORT_OPTIONS
    assert transport_matches
    assert generate_portability_export.app is app
    return prefix


def _tree(root):
    result = {}
    root = Path(root)
    if root.exists():
        for path in root.rglob("*"):
            safe_entry = not path.is_symlink()
            assert safe_entry
            relative = str(path.relative_to(root))
            result[relative] = (("file", path.stat().st_size,
                                 hashlib.sha256(path.read_bytes()).hexdigest(),
                                 path.stat().st_mtime_ns, path.stat().st_mode & 0o777)
                                if path.is_file() else ("directory",))
    return {"count": len(result), "sha256": _digest(result)}


def _rows():
    return {str(row["id"]): row for row in Job.objects.order_by("pk").values()}


def _queries():
    return {model._meta.label: model.objects.all()
            for model in apps.get_models(include_auto_created=True) if model is not Job}


def _prepare(request, settings, monkeypatch, count, mode):
    native_dispatch = jobs.dispatch
    # prepared disables dispatch only while constructing a native admitted seed.
    with monkeypatch.context() as patch:
        case, actor, selection, review, *_ = prepared(request, settings, patch)
        seed = enqueue(case, actor, selection, review)
    assert jobs.dispatch is native_dispatch
    # photo_environment activates eager while preparing the native seed.
    # Set broker mode only after all imported fixture preparation has finished.
    settings.CELERY_TASK_ALWAYS_EAGER = False
    assert not app.conf.task_always_eager
    now = timezone.now()
    future, past = now + timedelta(days=7), now - timedelta(days=1)
    # Fixture pins only: no freshness or seven-day TTL admission claim.
    type(selection).objects.filter(pk=selection.pk).update(expires_at=future)
    type(seed.proof).objects.filter(pk=seed.proof_id).update(expires_at=future)
    Job.objects.filter(pk=seed.pk).update(expires_at=future, available_at=future)
    seed.refresh_from_db()
    template = {f.attname: getattr(seed, f.attname)
                for f in Job._meta.concrete_fields if not f.primary_key}
    index = 0

    def clone(**changes):
        nonlocal index
        values = dict(template, key=uuid4(), **changes)
        row = Job.objects.create(**values)
        # Unique timestamps exercise native created_at order, without a PK tie promise.
        Job.objects.filter(pk=row.pk).update(created_at=past + timedelta(seconds=index))
        index += 1
        return str(row.pk)

    targets = []
    for number in range(count):
        values = {"available_at": past, "dispatched_at": None}
        if mode == "expiry":
            values.update(expires_at=past, available_at=future,
                          state="running" if number % 2 else "queued", lease_until=future)
        targets.append(clone(**values))
    if mode == "mixed":
        targets = [clone(available_at=past),
                   clone(available_at=past, dispatched_at=past),
                   clone(state="running", available_at=past, lease_until=past,
                         attempts=1, attempt_token=uuid4(), dispatched_at=past)]
    clone(available_at=past, dispatched_at=future)  # recent queued dispatch pin
    clone(state="running", available_at=past, lease_until=future, attempts=1,
          attempt_token=uuid4())
    for state in ("failed", "rejected"):
        clone(state=state, finished_at=past, encrypted_reason="", lease_until=None)
    return targets


def _envelopes(redis, keys):
    ids = []
    for key in keys:
        for raw in redis.lrange(key, 0, -1):
            wire = json.loads(raw)
            body = json.loads(base64.b64decode(wire["body"], validate=True))
            valid = (wire["headers"]["task"] == generate_portability_export.name
                     and isinstance(body, list) and len(body) == 3
                     and isinstance(body[0], list) and len(body[0]) == 1
                     and isinstance(body[0][0], str) and body[1] == {})
            assert valid
            ids.append(body[0][0])
    return sorted(ids)


def _measure(name, observed, monkeypatch, producer, queue, failure):
    metric = {"phase": name, "sql_count": 0, "sql_seconds": 0.0,
              "operations": {}, "dispatch_calls": 0, "dispatch_success": 0,
              "dispatch_seconds": 0.0, "broker_calls": 0, "broker_publications": 0,
              "broker_seconds": 0.0, "injected_failures": 0}
    observed["phases"].append(metric)
    metric["eager_disabled_before_call"] = not app.conf.task_always_eager
    assert metric["eager_disabled_before_call"]
    dispatch, reconcile = jobs.dispatch, jobs.reconcile
    apply_async = generate_portability_export.apply_async
    order, results = [], []

    def publish(*args, **kwargs):
        valid = (not args and set(kwargs) == {"args", "ignore_result"}
                 and kwargs["ignore_result"] is True
                 and isinstance(kwargs["args"], list) and len(kwargs["args"]) == 1
                 and isinstance(kwargs["args"][0], str))
        assert valid
        broker_mode = not app.conf.task_always_eager
        assert broker_mode
        if failure:
            metric["injected_failures"] += 1
            metric["injected_failure_type"] = "ConnectionError"
            raise ConnectionError("synthetic owned broker failure")
        started = perf_counter()
        metric["broker_calls"] += 1
        try:
            result = apply_async(**kwargs, queue=queue, producer=producer, retry=False)
            metric["broker_publications"] += 1
            return result
        finally:
            metric["broker_seconds"] += perf_counter() - started

    def forward_dispatch(job_id):
        order.append(str(job_id))
        metric["dispatch_calls"] += 1
        started = perf_counter()
        try:
            result = dispatch(job_id)
            metric["dispatch_success"] += int(result)
            return result
        finally:
            metric["dispatch_seconds"] += perf_counter() - started

    def forward_reconcile():
        result = reconcile()
        results.append(result)
        return result

    def sql_observer(execute, sql, params, many, context):
        token = str(sql).lstrip().split(None, 1)[0].upper()
        operation = token if token in {"SELECT", "UPDATE", "INSERT", "DELETE",
                                      "SAVEPOINT", "RELEASE", "ROLLBACK"} else "OTHER"
        started = perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed = perf_counter() - started
            metric["sql_count"] += 1
            metric["sql_seconds"] += elapsed
            item = metric["operations"].setdefault(operation, {"count": 0, "seconds": 0.0})
            item["count"] += 1
            item["seconds"] += elapsed

    with monkeypatch.context() as patch:
        patch.setattr(jobs, "dispatch", forward_dispatch)
        patch.setattr(jobs, "reconcile", forward_reconcile)
        patch.setattr(generate_portability_export, "apply_async", publish)
        with connection.execute_wrapper(sql_observer):
            started = perf_counter()
            try:
                result = reconcile_portability_export_jobs.run()
            finally:
                metric["wall_seconds"] = perf_counter() - started
    metric["eager_disabled_after_call"] = not app.conf.task_always_eager
    assert metric["eager_disabled_after_call"]
    assert result is None and len(results) == 1
    metric.update(task_return_none=result is None, reconcile_result=results[0],
                  dispatch_order_sha256=_digest(order))
    return order, results[0]


def _phase(name, selected, expired, observed, monkeypatch, producer, queue,
           redis, keys, queries, settings, failure=False):
    assert not app.conf.task_always_eager
    before, domain, media = _rows(), _snapshot(queries), _tree(settings.MEDIA_ROOT)
    messages_before = _envelopes(redis, keys)
    start = timezone.now()
    order, result = _measure(name, observed, monkeypatch, producer, queue, failure)
    end = timezone.now()
    after, messages_after = _rows(), _envelopes(redis, keys)
    correct_order = order == selected
    assert correct_order
    expected_count = 0 if failure else len(selected)
    assert result == expected_count
    expected_messages = sorted(messages_before + ([] if failure else selected))
    messages_match = messages_after == expected_messages
    assert messages_match
    row_keys_match = set(before) == set(after)
    assert row_keys_match
    immutable_before, immutable_after = {}, {}
    for pk, old in before.items():
        new = after[pk]
        allowed = TERMINAL_COLUMNS if pk in expired else (
            {"dispatched_at"} if pk in selected and old["state"] == "queued" and not failure else set())
        immutable_before[pk] = {k: v for k, v in old.items() if k not in allowed}
        immutable_after[pk] = {k: v for k, v in new.items() if k not in allowed}
        immutable_equal = _digest(immutable_before[pk]) == _digest(immutable_after[pk])
        assert immutable_equal
        if pk in expired:
            terminal_valid = (new["state"] == "rejected" and new["encrypted_reason"] == ""
                              and new["lease_until"] is None
                              and start <= new["finished_at"] <= end)
            assert terminal_valid
        elif allowed:
            dispatch_bounded = start <= new["dispatched_at"] <= end
            assert dispatch_bounded
    domain_after, media_after = _snapshot(queries), _tree(settings.MEDIA_ROOT)
    assert domain == domain_after and media == media_after
    metric = observed["phases"][-1]
    assert metric["dispatch_calls"] == len(selected)
    assert metric["dispatch_success"] == metric["broker_publications"] == expected_count
    assert metric["injected_failures"] == (len(selected) if failure else 0)
    changed = {pk for pk in before if _digest(before[pk]) != _digest(after[pk])}
    expected_changed = set(expired) | {pk for pk in selected if before[pk]["state"] == "queued" and not failure}
    changes_match = changed == expected_changed
    assert changes_match
    metric.update(expired_rows=len(expired), selected_rows=len(selected),
                  actual_changed_rows=len(changed),
                  actual_changed_ids_sha256=_digest(sorted(changed)),
                  rows_before_count=len(before), rows_after_count=len(after),
                  actual_messages_before=len(messages_before), actual_messages_after=len(messages_after),
                  actual_message_ids_sha256=_digest(messages_after),
                  expired_ids_sha256=_digest(sorted(expired)),
                  target_before_sha256=_digest(before), target_after_sha256=_digest(after),
                  immutable_before_sha256=_digest(immutable_before),
                  immutable_after_sha256=_digest(immutable_after),
                  phase_pins_sha256=_digest({pk: row for pk, row in before.items()
                                            if pk not in selected and pk not in expired}),
                  domain_before=domain, domain_after=domain_after,
                  media_before=media, media_after=media_after)


@pytest.mark.parametrize("count", [0, 1, 10, 100, 101])
def test_owned_job_dispatch_volume(request, settings, monkeypatch, record_property, count):
    _profile(request, settings, monkeypatch, record_property, count, "dispatch")


@pytest.mark.parametrize("count", [0, 1, 10, 100, 101])
def test_owned_job_expiry_volume(request, settings, monkeypatch, record_property, count):
    _profile(request, settings, monkeypatch, record_property, count, "expiry")


def test_owned_job_mixed_repeated_running(request, settings, monkeypatch, record_property):
    _profile(request, settings, monkeypatch, record_property, 0, "mixed")


def test_owned_job_broker_failure_recovery(request, settings, monkeypatch, record_property):
    _profile(request, settings, monkeypatch, record_property, 2, "failure")


def _profile(request, settings, monkeypatch, record_property, count, mode):
    started = perf_counter()
    observed = {"status": "not_started", "mode": mode, "volume": count, "phases": [],
                "scope": "BEFORE native Task.run; owned Redis only; no worker/generation/Beat",
                "timing": "N=1 per phase; broker subset of dispatch; SQL overlaps; no p95/throughput",
                "limits": "separate native 100 expiry rows and 100 dispatch IDs",
                "fixture": "FK-valid synthetic clones; seven-day fixture pins; no admission/TTL claim"}
    try:
        prefix = _guard(request, settings)
        targets = _prepare(request, settings, monkeypatch, count, mode)
        queries = _queries()
        queue = "owned-job-profile-" + uuid4().hex
        keys = [prefix + queue + suffix for suffix in PRIORITIES]
        initial = _rows()
        pins = {pk: row for pk, row in initial.items() if pk not in targets}
        observed.update(setup_seconds=perf_counter() - started,
                        rows_before_count=len(initial),
                        pins_before_sha256=_digest(pins), pins_count=len(pins),
                        target_count=len(targets))
        with Redis.from_url(settings.CELERY_BROKER_URL,
                            socket_timeout=5, socket_connect_timeout=5) as redis:
            assert all(redis.exists(key) == 0 for key in keys)
            try:
                with app.connection_for_write() as broker:
                    with app.amqp.Producer(broker) as producer:
                        def phase(name, selected=(), expired=(), failure=False):
                            _phase(name, list(selected), set(expired), observed, monkeypatch,
                                   producer, queue, redis, keys, queries, settings, failure)

                        if mode == "expiry":
                            phase("first_expiry", expired=targets[:100])
                            if count == 101:
                                phase("expiry_continuation", expired=targets[100:])
                            phase("expiry_replay")
                        elif mode == "mixed":
                            phase("mixed_first", targets)
                            # Running leases are unchanged by dispatch: at-least-once resend.
                            phase("mixed_running_repeat", targets[-1:])
                        else:
                            if mode == "failure":
                                phase("broker_failure", targets, failure=True)
                            phase("first_dispatch", targets[:100])
                            if count == 101:
                                phase("dispatch_continuation", targets[100:])
                            phase("queued_immediate_replay")
                observed["broker_context_exited"] = True
                after = _rows()
                final_pins = {pk: row for pk, row in after.items() if pk not in targets}
                observed["rows_after_count"] = len(after)
                observed["pins_after_sha256"] = _digest(final_pins)
                assert observed["pins_before_sha256"] == observed["pins_after_sha256"]
            finally:
                cleanup_start = perf_counter()
                # Never FLUSH/SCAN/purge a shared generation or the global app.
                redis.delete(*keys)
                observed["owned_queue_keys_removed"] = all(redis.exists(key) == 0 for key in keys)
                observed["cleanup_seconds"] = perf_counter() - cleanup_start
                assert observed["owned_queue_keys_removed"]
        observed["redis_context_exited"] = True
        observed["status"] = "passed"
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["case_seconds"] = perf_counter() - started
        observed["measured_seconds"] = sum(p.get("wall_seconds", 0) for p in observed["phases"])
        observed["non_measured_seconds"] = observed["case_seconds"] - observed["measured_seconds"]
        record_property("owned_job_reconcile_profile", json.dumps(
            observed, sort_keys=True, allow_nan=False))
