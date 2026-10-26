"""Finite BEFORE baseline: native task.run on owned PostgreSQL, no worker claim."""

import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import timedelta
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.db import close_old_connections, connection, connections, transaction
from django.utils import timezone
from test_operational_recovery_authority_wait import _snapshot
from test_rectification_authority_wait import _files
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_information import draft
from test_rights_exports import prepared

from apps.safety.models import RightsAction, RightsCopyInformation
from apps.safety.rights_copy_information import record
from apps.safety.tasks import purge_expired_copy_information

pytestmark = pytest.mark.django_db(transaction=True)


def _owned_serial(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL logical purge profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _digest(value):
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _rows():
    return {row["id"]: row for row in RightsCopyInformation.objects.order_by("pk").values()}


def _unchanged(before, after, changed):
    assert set(before) == set(after)
    for pk, original in before.items():
        current = after[pk]
        if pk in changed:
            cleared = current["encrypted_information"] == ""
            has_marker = current["purged_at"] is not None
            was_unpurged = original["purged_at"] is None
            assert cleared and has_marker and was_unpurged
            immutable = set(original) - {"encrypted_information", "purged_at"}
            before_hash = _digest({k: original[k] for k in immutable})
            after_hash = _digest({k: current[k] for k in immutable})
            assert before_hash == after_hash
        else:
            before_hash, after_hash = _digest(original), _digest(current)
            assert before_hash == after_hash


def _clone_values(row):
    return {
        field.attname: getattr(row, field.attname)
        for field in row._meta.concrete_fields
        if not field.primary_key
    }


def _prepare(request, settings, count):
    case, actor, _, _, _, _ = prepared(request, settings)
    seed = record(
        actor, case.pk, case.version, uuid4(), 0, "synthetic-policy-v1",
        "Synthetic logical purge baseline seed", draft(),
    )
    now = timezone.now()
    RightsCopyInformation.objects.filter(pk=seed.pk).update(expires_at=now + timedelta(days=1))
    seed.refresh_from_db()
    expired = []
    for offset in range(count + 1):
        action_values = _clone_values(seed.action)
        action_values["key"] = uuid4()
        action = RightsAction.objects.create(**action_values)
        values = _clone_values(seed)
        values.update(action_id=action.pk, version=seed.version + offset + 1,
                      expires_at=now - timedelta(days=1))
        if offset == count:
            values.update(encrypted_information="", purged_at=now - timedelta(hours=1))
        row = RightsCopyInformation.objects.create(**values)
        if offset < count:
            expired.append(row.pk)
    assert len(expired) == count
    assert RightsCopyInformation.objects.filter(purged_at__isnull=True, expires_at__lte=now).count() == count
    return sorted(expired)


def _other_queries():
    return {
        model._meta.label: model.objects.all()
        for label in ("core", "listings", "mediafiles", "safety", "auth")
        for model in apps.get_app_config(label).get_models(include_auto_created=True)
        if model is not RightsCopyInformation
    }


def _measure(phase, observed):
    metric = {"phase": phase, "sql_count": 0, "sql_seconds": 0.0, "operations": {}}
    observed["phases"].append(metric)

    def instrument(execute, sql, params, many, context):
        # Inspect only the operation token; never retain SQL, params or payloads.
        token = str(sql).lstrip().split(None, 1)[0].upper()
        operation = token if token in {
            "SELECT", "UPDATE", "INSERT", "DELETE", "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"
        } else "OTHER"
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

    started = perf_counter()
    try:
        with connection.execute_wrapper(instrument):
            result = purge_expired_copy_information.run()
        metric["returned_count"] = result
        return result
    finally:
        metric["wall_seconds"] = perf_counter() - started


def _pass(phase, expected_ids, observed):
    before = _rows()
    start = timezone.now()
    count = _measure(phase, observed)
    end = timezone.now()
    assert count == len(expected_ids)
    after = _rows()
    _unchanged(before, after, set(expected_ids))
    timestamp_bounds = all(start <= after[pk]["purged_at"] <= end for pk in expected_ids)
    assert timestamp_bounds


def _skip_locked(expired, observed):
    held, others = expired[0], expired[1:]
    runtime = {}
    pool = ThreadPoolExecutor(max_workers=1)
    future = None

    def worker():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '10s'")
                cursor.execute("SELECT pg_backend_pid()")
                runtime["pid"] = cursor.fetchone()[0]
                runtime["raw"] = connection.connection
            return _measure("skip_locked_first_batch", observed)
        finally:
            connections.close_all()
            observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

    before = _rows()
    try:
        with transaction.atomic():
            RightsCopyInformation.objects.select_for_update().get(pk=held)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            observed["held_row_lock_acquired"] = True
            future = pool.submit(worker)
            try:
                count = future.result(timeout=15)
            except FutureTimeoutError:
                raw = runtime.get("raw")
                if raw is not None and not raw.closed:
                    raw.cancel()
                raise
            assert count == len(others)
            assert runtime["pid"] != holder
            observed.update(holder_pid=holder, worker_pid=runtime["pid"],
                            worker_completed_while_holder_active=connection.in_atomic_block)
            assert observed["worker_completed_while_holder_active"]
            _unchanged(before, _rows(), set(others))
        observed["holder_released"] = not connection.in_atomic_block
    finally:
        # Statement timeout bounds the worker even on assertion/timeout failures.
        if future is not None and not future.done():
            try:
                future.result(timeout=15)
            except Exception:
                observed["cleanup_worker_exception"] = True
        pool.shutdown(wait=True, cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        observed["holder_released"] = not connection.in_atomic_block
    assert observed["worker_connections_closed"] and observed["thread_finished"]
    assert observed["holder_released"]
    _pass("after_holder_release", [held], observed)
    _pass("idempotent_replay", [], observed)


@pytest.mark.parametrize("expired_count", [0, 1, 10, 100, 101])
def test_owned_logical_purge_volume(request, settings, record_property, expired_count):
    _profile(request, settings, record_property, expired_count, False)


def test_owned_logical_purge_skip_locked(request, settings, record_property):
    _profile(request, settings, record_property, 3, True)


def _profile(request, settings, record_property, count, skip_locked):
    profile_started = perf_counter()
    observed = {
        "baseline": "BEFORE only; no application changes or optimization comparison",
        "surface": "native task.run; no Beat, broker, worker or delivery verification",
        "volume": "one native seed plus synthetic retained-metadata/action clones; not additional verified user executions",
        "timing_scope": "one sample per named phase; SQL wrapper time excludes Python processing; transaction control counted only when wrapper observes it",
        "expired_count": count, "phases": [], "status": "not_started",
    }
    try:
        _owned_serial(request, settings)
        expired = _prepare(request, settings, count)
        queries = _other_queries()
        before, files_before, rows_before = _snapshot(queries), _files(settings), _rows()
        def immutable(rows):
            return _digest({pk: {k: v for k, v in row.items()
                                 if k not in {"encrypted_information", "purged_at"}}
                            for pk, row in rows.items()})

        def pins(rows):
            return _digest({pk: row for pk, row in rows.items() if pk not in expired})

        observed.update(other_tables_before=before, files_before=files_before,
                        target_rows_before_sha256=_digest(rows_before),
                        target_row_count=len(rows_before), expired_count_confirmed=len(expired),
                        immutable_before_sha256=immutable(rows_before),
                        pins_before_sha256=pins(rows_before),
                        pre_measurement_seconds=perf_counter() - profile_started)
        if skip_locked:
            _skip_locked(expired, observed)
        else:
            _pass("first_batch", expired[:100], observed)
            if count == 101:
                _pass("second_batch", expired[100:], observed)
            _pass("idempotent_replay", [], observed)
        after, files_after = _snapshot(queries), _files(settings)
        assert before == after
        assert files_before == files_after
        _unchanged(rows_before, _rows(), set(expired))
        rows_after = _rows()
        observed.update(other_tables_after=after, files_after=files_after,
                        target_rows_after_sha256=_digest(rows_after),
                        immutable_after_sha256=immutable(rows_after),
                        pins_after_sha256=pins(rows_after), status="passed")
        assert observed["immutable_before_sha256"] == observed["immutable_after_sha256"]
        assert observed["pins_before_sha256"] == observed["pins_after_sha256"]
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["case_body_seconds"] = perf_counter() - profile_started
        observed["measured_purge_seconds"] = sum(p.get("wall_seconds", 0) for p in observed["phases"])
        observed["non_measured_case_seconds"] = observed["case_body_seconds"] - observed["measured_purge_seconds"]
        record_property("owned_logical_purge_profile", json.dumps(observed, sort_keys=True, allow_nan=False))
