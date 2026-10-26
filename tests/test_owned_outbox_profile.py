"""Finite BEFORE profiles of native task.run and the real local simulator only.

Synthetic retained metadata supplies volume, not additional admitted user histories.
No broker, Beat, prefork worker, provider delivery, p95 or causal improvement claim.
"""

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
from django.db.models import Q
from django.utils import timezone
from test_notice_delivery import queued
from test_operational_recovery_authority_wait import _snapshot
from test_rectification_authority_wait import _files
from test_report_decisions import action as report_action
from test_report_inspection import case as report_case
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready, values

from apps.safety import notice_delivery, rights_responses
from apps.safety.crypto import seal
from apps.safety.models import (
    ComplaintNotice,
    ReportNotice,
    RightsNotice,
    SimulatedComplaintNoticeDelivery,
    SimulatedNoticeDelivery,
    SimulatedRightsNoticeDelivery,
)
from apps.safety.tasks import deliver_safety_notices

pytestmark = pytest.mark.django_db(transaction=True)
NOTICES = (ReportNotice, ComplaintNotice, RightsNotice)
DELIVERIES = (
    SimulatedNoticeDelivery, SimulatedComplaintNoticeDelivery, SimulatedRightsNoticeDelivery,
)
MUTABLE = {"status", "attempts", "error_code", "next_attempt_at", "simulated_at"}


def _guard(request, settings):
    explicit = any(
        Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
        for arg in request.config.args
    )
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL outbox profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()
    settings.SAFETY_NOTICE_BACKEND = "simulator"


def _hash(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str,
    ).encode()).hexdigest()


def _clone(seed, **changes):
    fields = {
        f.attname: getattr(seed, f.attname)
        for f in seed._meta.concrete_fields if not f.primary_key
    }
    return type(seed).objects.create(**(fields | changes))


def _eligible():
    now = timezone.now()
    return {
        model: list(model.objects.filter(status__in=["queued", "retry"], attempts__lt=5)
                    .filter(Q(next_attempt_at__isnull=True) | Q(next_attempt_at__lte=now))
                    .order_by("created_at", "pk").values_list("pk", flat=True))
        for model in NOTICES
    }


def _order(groups):
    result = []
    for index in range(max((len(ids) for ids in groups.values()), default=0)):
        for model in NOTICES:
            if index < len(groups[model]):
                result.append((model._meta.label, groups[model][index]))
    return result


def _prepare(request, settings, monkeypatch, count):
    complaint, _ = queued(request, settings)
    report = report_case(request.getfixturevalue("directory"))
    _, staff = reviewer()
    path, data = report_action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    response = staff.post(f"/en/moderation/reports/{report.pk}/", {
        "purpose": "Inspect synthetic report before native profile seed dismissal",
    })
    assert response.status_code == 200
    path, data = report_action(staff, report, "dismiss")
    assert staff.post(path, data).status_code == 302
    case, actor, _, _, _, _ = ready(request, settings, monkeypatch)
    rights_responses.issue(actor, case.pk, **values(case))
    seeds = (ReportNotice.objects.filter(report=report, kind="outcome").get(),
             complaint, RightsNotice.objects.get())
    # All producer-generated queued rows become legitimate simulated pins first.
    native_count = sum(map(len, _eligible().values()))
    consumed = 0
    while any(_eligible().values()):
        remaining_before = sum(map(len, _eligible().values()))
        result = notice_delivery.process_outbox()
        remaining_after = sum(map(len, _eligible().values()))
        assert remaining_after < remaining_before
        assert result["processed"] > 0
        assert result["simulated"] == result["processed"]
        consumed += result["processed"]
    assert consumed == native_count and not any(_eligible().values())
    for seed in seeds:
        seed.refresh_from_db()
        assert seed.status == "simulated" and seed.attempts == 1

    def synthetic(kind, status="queued", attempts=0, next_at=None):
        seed = seeds[kind]
        links = {}
        if kind == 0:
            links["event_key"] = f"synthetic-profile:{uuid4()}"
        elif kind == 1:
            resolution = seed.resolution
            parent = _clone(resolution.complaint, submission_key=uuid4(),
                            receipt_digest=_hash(str(uuid4())))
            action = _clone(resolution.action, complaint_id=parent.pk, key=uuid4())
            links["resolution_id"] = _clone(
                resolution, complaint_id=parent.pk, action_id=action.pk,
            ).pk
        else:
            source = seed.response
            # Sequence uniqueness is maintained; this is retained metadata, not admission.
            sequence = source.request.responses.order_by("-response_version").first().response_version + 1
            links["response_id"] = _clone(
                source, key=uuid4(), response_version=sequence, withdrawal_id=None,
            ).pk
        return _clone(seed, **links, status=status, attempts=attempts,
                      next_attempt_at=next_at, error_code="synthetic_prior_failure",
                      simulated_at=None)

    for kind in range(3):
        synthetic(kind, "retry", 1, timezone.now() + timedelta(days=1))
        synthetic(kind, "failed", 5)
    targets = [synthetic(index % 3, "retry" if index % 2 else "queued",
                         index % 2) for index in range(count)]
    # Deliberately reverse within-kind creation order to exercise created_at,pk ordering.
    now = timezone.now() - timedelta(hours=1)
    for index, target in enumerate(targets):
        type(target).objects.filter(pk=target.pk).update(created_at=now - timedelta(seconds=index))
    expected = _order(_eligible())
    assert len(expected) == count
    return expected, synthetic, native_count


def _rows(models):
    return {model._meta.label: {
        row["id"]: row for row in model.objects.order_by("pk").values()
    } for model in models}


def _other_queries():
    excluded = set(NOTICES + DELIVERIES)
    return {model._meta.label: model.objects.all()
            for model in apps.get_models(include_auto_created=True)
            if model not in excluded}


def _fingerprints(rows, targets):
    immutable, pins = {}, {}
    for label, items in rows.items():
        immutable[label] = {pk: {k: v for k, v in row.items() if k not in MUTABLE}
                            for pk, row in items.items()}
        pins[label] = {pk: row for pk, row in items.items() if (label, pk) not in targets}
    return {"immutable_sha256": _hash(immutable), "pins_sha256": _hash(pins),
            "pin_counts": {label: len(items) for label, items in pins.items()}}


def _effects(before, receipts_before, expected, started, ended, failure=False):
    after, receipts_after = _rows(NOTICES), _rows(DELIVERIES)
    changed = set(expected)
    for model, delivery in zip(NOTICES, DELIVERIES, strict=True):
        label, delivery_label = model._meta.label, delivery._meta.label
        old, new = before[label], after[label]
        assert set(old) == set(new)
        for pk, row in old.items():
            current = new[pk]
            immutable_equal = _hash({k: v for k, v in row.items() if k not in MUTABLE}) == _hash(
                {k: v for k, v in current.items() if k not in MUTABLE})
            assert immutable_equal
            if (label, pk) not in changed:
                same = _hash(row) == _hash(current)
                assert same
                continue
            attempt_incremented = current["attempts"] == row["attempts"] + 1
            assert attempt_incremented
            if failure:
                terminal = current["attempts"] == 5
                failure_fields_match = (
                    current["status"] == ("failed" if terminal else "retry")
                    and current["error_code"] == "adapter_failure"
                    and current["simulated_at"] is None
                )
                assert failure_fields_match
                if terminal:
                    terminal_has_no_retry_time = current["next_attempt_at"] is None
                    assert terminal_has_no_retry_time
                else:
                    bounded = started + timedelta(seconds=60) <= current["next_attempt_at"] <= ended + timedelta(seconds=60)
                    assert bounded
            else:
                simulated_fields_match = (current["status"] == "simulated"
                                          and current["error_code"] == ""
                                          and current["next_attempt_at"] is None)
                assert simulated_fields_match
                bounded = started <= current["simulated_at"] <= ended
                assert bounded
        original = receipts_before[delivery_label]
        current = receipts_after[delivery_label]
        preserved = all(_hash(row) == _hash(current.get(pk)) for pk, row in original.items())
        assert preserved
        added = [row for pk, row in current.items() if pk not in original]
        desired = [] if failure else [pk for kind, pk in expected if kind == label]
        assert sorted(row["notice_id"] for row in added) == sorted(desired)
        valid_receipt_metadata = all(
            row["procedure"] == "simulator-v1" and started <= row["created_at"] <= ended
            for row in added
        )
        assert valid_receipt_metadata


def _measure(phase, observed, monkeypatch):
    metric = {"phase": phase, "sql_count": 0, "sql_seconds": 0.0,
              "operations": {}, "adapter_seconds": 0.0, "adapter_calls": 0}
    observed["phases"].append(metric)
    order = []
    adapter = notice_delivery.simulated_adapter

    def forward(notice):
        order.append((notice._meta.label, notice.pk))
        started = perf_counter()
        try:
            return adapter(notice)
        finally:
            metric["adapter_calls"] += 1
            metric["adapter_seconds"] += perf_counter() - started

    def sql_probe(execute, sql, params, many, context):
        token = str(sql).lstrip().split(None, 1)[0].upper()
        operation = token if token in {
            "SELECT", "UPDATE", "INSERT", "DELETE", "BEGIN", "COMMIT", "ROLLBACK",
            "SAVEPOINT", "RELEASE",
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

    with monkeypatch.context() as patch:
        patch.setattr(notice_delivery, "simulated_adapter", forward)
        with connection.execute_wrapper(sql_probe):
            started = perf_counter()
            try:
                result = deliver_safety_notices.run()
            finally:
                metric["wall_seconds"] = perf_counter() - started
    metric["result"] = result
    metric["adapter_kinds"] = [kind for kind, _ in order]
    return result, order


def _pass(phase, expected, observed, monkeypatch, failure=False):
    before, receipts = _rows(NOTICES), _rows(DELIVERIES)
    started = timezone.now()
    result, order = _measure(phase, observed, monkeypatch)
    ended = timezone.now()
    assert order == expected
    assert result == {"processed": len(expected), "simulated": 0 if failure else len(expected),
                      "retry": 1 if failure else 0, "failed": 1 if failure else 0,
                      "disabled": False}
    _effects(before, receipts, expected, started, ended, failure)


def _skip_locked(expected, observed, monkeypatch):
    held = next(pk for label, pk in expected if label == ReportNotice._meta.label)
    others = [item for item in expected if item != (ReportNotice._meta.label, held)]
    runtime, pool, future = {}, ThreadPoolExecutor(max_workers=1), None

    def worker():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '10s'")
                cursor.execute("SELECT pg_backend_pid()")
                runtime["pid"] = cursor.fetchone()[0]
                runtime["raw"] = connection.connection
            _pass("skip_locked", others, observed, monkeypatch)
        finally:
            connections.close_all()
            observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

    try:
        with transaction.atomic():
            ReportNotice.objects.select_for_update().get(pk=held)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            observed["held_row_lock_acquired"] = True
            future = pool.submit(worker)
            try:
                future.result(timeout=15)
            except FutureTimeoutError:
                raw = runtime.get("raw")
                if raw is not None and not raw.closed:
                    raw.cancel()
                raise
            assert runtime["pid"] != holder
            observed.update(holder_pid=holder, worker_pid=runtime["pid"])
            observed["worker_completed_while_holder_active"] = connection.in_atomic_block
            assert observed["worker_completed_while_holder_active"]
    finally:
        if future is not None and not future.done():
            raw = runtime.get("raw")
            if raw is not None and not raw.closed:
                raw.cancel()
            try:
                future.result(timeout=15)
            except Exception:
                observed["cleanup_worker_exception"] = True
        pool.shutdown(wait=True, cancel_futures=True)
        observed["thread_finished"] = future is None or future.done()
        observed["holder_released"] = not connection.in_atomic_block
    assert observed["worker_connections_closed"] and observed["thread_finished"]
    assert observed["holder_released"]
    _pass("after_unlock", [(ReportNotice._meta.label, held)], observed, monkeypatch)
    _pass("replay", [], observed, monkeypatch)


@pytest.mark.parametrize("count", [0, 1, 10, 100, 101])
def test_owned_outbox_volume(request, settings, monkeypatch, record_property, count):
    _profile(request, settings, monkeypatch, record_property, count, "volume")


def test_owned_outbox_skip_locked(request, settings, monkeypatch, record_property):
    _profile(request, settings, monkeypatch, record_property, 3, "skip_locked")


def test_owned_outbox_real_adapter_failure(request, settings, monkeypatch, record_property):
    _profile(request, settings, monkeypatch, record_property, 0, "failure")


def _profile(request, settings, monkeypatch, record_property, count, scenario):
    started = perf_counter()
    observed = {
        "baseline": "BEFORE; no application change or causal comparison",
        "surface": "native task.run, real local simulator; no worker/provider claim",
        "volume": "native drained seeds plus synthetic retained metadata; no clone admission claim",
        "failure_fixture": "deliberately corrupted encrypted recipient; not a producer-valid history or product bug",
        "timing_scope": "N=1 per phase; SQL and adapter time overlap and must not be added; no SQL/params retained; transaction control only if exposed by wrapper",
        "scenario": scenario, "eligible_count": count, "phases": [], "status": "not_started",
    }
    try:
        _guard(request, settings)
        expected, synthetic, native_count = _prepare(request, settings, monkeypatch, count)
        if scenario == "failure":
            faults = [synthetic(0), synthetic(2, attempts=4)]
            # Real seal/unseal/validate_email path; never stub the adapter or exception.
            envelope = seal({"recipient": "invalid-address", "subject": "Synthetic", "body": "Synthetic"})
            for row in faults:
                type(row).objects.filter(pk=row.pk).update(encrypted_payload=envelope)
            del envelope
            expected = _order(_eligible())
            assert len(expected) == 2
            observed["eligible_count"] = 2
        queries = _other_queries()
        before, files_before, rows = _snapshot(queries), _files(settings), _rows(NOTICES)
        targets = set(expected)
        fingerprints = _fingerprints(rows, targets)
        receipt_queries = {model._meta.label: model.objects.all() for model in DELIVERIES}
        observed.update(native_seed_count=native_count, other_tables_before=before,
                        files_before=files_before, notice_before=fingerprints,
                        deliveries_before=_snapshot(receipt_queries),
                        eligible_order_sha256=_hash(expected),
                        pre_measurement_seconds=perf_counter() - started)
        if scenario == "skip_locked":
            _skip_locked(expected, observed, monkeypatch)
        elif scenario == "failure":
            _pass("adapter_failure", expected, observed, monkeypatch, failure=True)
            _pass("immediate_followup", [], observed, monkeypatch)
        else:
            _pass("first_batch", expected[:100], observed, monkeypatch)
            if count == 101:
                _pass("continuation", expected[100:], observed, monkeypatch)
            _pass("replay", [], observed, monkeypatch)
        after, files_after = _snapshot(queries), _files(settings)
        assert before == after and files_before == files_after
        after_fingerprints = _fingerprints(_rows(NOTICES), targets)
        assert fingerprints == after_fingerprints
        observed.update(other_tables_after=after, files_after=files_after,
                        notice_after=after_fingerprints,
                        deliveries_after=_snapshot(receipt_queries), status="passed")
    finally:
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["case_body_seconds"] = perf_counter() - started
        observed["measured_task_seconds"] = sum(p.get("wall_seconds", 0) for p in observed["phases"])
        observed["non_measured_case_seconds"] = observed["case_body_seconds"] - observed["measured_task_seconds"]
        record_property("owned_outbox_profile", json.dumps(observed, sort_keys=True, allow_nan=False))
