"""Finite owned PostgreSQL BEFORE profiles; synthetic metadata, native task bodies.

Fixture intake/plan preparation is outside measurement and retains its original
simulators. These cases claim no worker, human review, delivery or erasure proof.
"""

import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import date, timedelta
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import pytest
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, connections, transaction
from django.utils import timezone
from test_account_erasure_execution import prepared_erasure
from test_operational_recovery_authority_wait import _snapshot
from test_report_inspection import case
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety import retention_reviews
from apps.safety.models import ErasurePlan, Report, RetentionReview, RightsAction, UrgentReportAlert
from apps.safety.tasks import reconcile_retention_reviews, reconcile_urgent_report_alerts

pytestmark = pytest.mark.django_db(transaction=True)


def _digest(value):
    return hashlib.sha256(json.dumps(value, default=str, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL reconciler profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _clone(row):
    return {field.attname: getattr(row, field.attname)
            for field in row._meta.concrete_fields if not field.primary_key}


def _rows(model):
    return {str(row[model._meta.pk.attname]): row
            for row in model.objects.order_by("pk").values()}


def _tree(root):
    root = Path(root)
    root_safe = not root.is_symlink()
    assert root_safe
    found = {}
    if root.exists():
        for path in root.rglob("*"):
            entry_safe = not path.is_symlink()
            assert entry_safe
            stat = path.stat()
            value = (stat.st_mtime_ns, stat.st_mode)
            if path.is_file():
                value += (stat.st_size, hashlib.sha256(path.read_bytes()).hexdigest())
            found[str(path.relative_to(root))] = value
    return {"count": len(found), "sha256": _digest(found)}


def _queries(kind):
    excluded = {UrgentReportAlert} if kind == "urgent" else {ErasurePlan, RetentionReview}
    return {model._meta.label: model.objects.all()
            for model in apps.get_models(include_auto_created=True) if model not in excluded}


def _ordered(model, ids):
    return [str(pk) for pk in model.objects.filter(pk__in=ids)
            .order_by("created_at", "pk").values_list("pk", flat=True)]


def _prepare(kind, count, mixed, request, settings, monkeypatch):
    if kind == "urgent":
        seed = case(request.getfixturevalue("directory"))
        assert UrgentReportAlert.objects.filter(report=seed).exists()
        targets = []
        for index in range(count + 1):
            values = _clone(seed)
            values.update(submission_key=uuid4(), priority=0 if index < count else 1)
            row = Report.objects.create(**values)
            Report.objects.filter(pk=row.pk).update(
                created_at=seed.created_at + timedelta(microseconds=index + 1))
            if index < count:
                targets.append(str(row.pk))
        return {"ids": _ordered(Report, targets), "decisions": {}, "invalid": set(), "k": 0}

    _, _, _, _, _, _, seed, _, _, _ = prepared_erasure(request, settings, monkeypatch)
    seed.refresh_from_db()
    decisions = retention_reviews.plan_decisions(seed)
    retained = {row["purpose"]: row for row in decisions if row["operation"] in {"retain", "review"}}
    assert len(retained) >= 2, "Native fixture needs at least two retained purposes"
    assert seed.retention_purpose_count == len(retained)
    assert RetentionReview.objects.filter(plan=seed).count() == len(retained)
    targets, plans, invalid = [], {}, set()
    for index in range(count):
        action_values = _clone(seed.action)
        action_values["key"] = uuid4()
        action = RightsAction.objects.create(**action_values)
        values = _clone(seed)
        values.update(action_id=action.pk, retention_purpose_count=None)
        row = ErasurePlan.objects.create(**values)
        ErasurePlan.objects.filter(pk=row.pk).update(
            created_at=seed.created_at + timedelta(microseconds=index + 1))
        # Authentication binds inventory/version/decisions, not the new action key.
        assert _digest(retention_reviews.plan_decisions(row)) == _digest(decisions)
        targets.append(str(row.pk))
        plans[str(row.pk)] = {"decisions": retained, "actor": action.actor_id}
        if mixed and index == 1:
            ErasurePlan.objects.filter(pk=row.pk).update(retention_purpose_count=len(retained))
            pin = RetentionReview.objects.filter(plan=seed).order_by("pk").first()
            review_values = _clone(pin)
            review_values.update(plan_id=row.pk, version=7,
                                 next_review_on=pin.next_review_on + timedelta(days=2),
                                 last_reviewed_at=timezone.now())
            # Established synthetic follow-up pin; no review event or human claim.
            RetentionReview.objects.create(**review_values)
        if mixed and index == 2:
            ErasurePlan.objects.filter(pk=row.pk).update(encrypted_decisions="synthetic-tampered")
            row.refresh_from_db()
            with pytest.raises(ValidationError):
                retention_reviews.plan_decisions(row)
            invalid.add(str(row.pk))
    return {"ids": _ordered(ErasurePlan, targets), "decisions": plans,
            "invalid": invalid, "k": len(retained)}


def _measure(kind, name, observed):
    metric = {"phase": name, "sql_count": 0, "sql_seconds": 0.0, "operations": {}}
    observed["phases"].append(metric)

    def observe(execute, sql, params, many, context):
        token = str(sql).lstrip().split(None, 1)[0].upper()
        operation = token if token in {"SELECT", "UPDATE", "INSERT", "DELETE", "SAVEPOINT",
                                      "RELEASE", "ROLLBACK", "BEGIN", "COMMIT"} else "OTHER"
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

    task = reconcile_urgent_report_alerts if kind == "urgent" else reconcile_retention_reviews
    with connection.execute_wrapper(observe):
        started = perf_counter()
        try:
            result = task.run()
        finally:
            metric["wall_seconds"] = perf_counter() - started
    metric["result"] = result
    return result, metric


def _phase(kind, name, selected, prepared, observed, settings):
    selected = set(selected)
    target = UrgentReportAlert if kind == "urgent" else RetentionReview
    before = _rows(target)
    plan_immutable_before = None
    plan_immutable_after = None
    plans_before = _rows(ErasurePlan) if kind == "retention" else {}
    reports_before = _rows(Report) if kind == "urgent" else {}
    queries = _queries(kind)
    domain, media = _snapshot(queries), _tree(settings.MEDIA_ROOT)
    lower = timezone.now()
    result, metric = _measure(kind, name, observed)
    upper = timezone.now()
    after = _rows(target)
    # Every pre-existing row, including seed and synthetic follow-up pins, is exact.
    preserved = all(pk in after and _digest(row) == _digest(after[pk])
                    for pk, row in before.items())
    assert preserved
    added = {pk: row for pk, row in after.items() if pk not in before}
    assert all(lower <= row["created_at"] <= upper for row in added.values())
    if kind == "urgent":
        assert result == {"reconciled": len(selected)}
        actual = {str(row["report_id"]) for row in added.values()}
        assert len(added) == len(selected) and _digest(sorted(actual)) == _digest(sorted(selected))
        assert all(row["acknowledged_at"] is None and row["acknowledged_by_id"] is None
                   for row in added.values())
        assert _digest(_rows(Report)) == _digest(reports_before)
        changed = set()
    else:
        valid = selected - prepared["invalid"]
        expected = {}
        for pk in valid:
            info = prepared["decisions"][pk]
            for purpose, decision in info["decisions"].items():
                if any(str(row["plan_id"]) == pk and row["purpose"] == purpose
                       for row in before.values()):
                    continue
                expected[(pk, purpose)] = (decision, info["actor"])
        actual = {(str(row["plan_id"]), row["purpose"]) for row in added.values()}
        assert _digest(sorted(actual)) == _digest(sorted(expected)) and len(added) == len(expected)
        for row in added.values():
            decision, actor = expected[(str(row["plan_id"]), row["purpose"])]
            valid_row = (row["operation"] == decision["operation"]
                         and row["initial_review_on"] == date.fromisoformat(decision["review_on"])
                         and row["next_review_on"] == row["initial_review_on"]
                         and row["responsible_id"] == actor and row["version"] == 1
                         and row["last_reviewed_at"] is None)
            assert valid_row
        assert result == {"plans": len(selected), "scheduled": len(expected),
                          "failed": len(selected & prepared["invalid"])}
        plans_after = _rows(ErasurePlan)
        plan_immutable_before = _digest({pk: {k: v for k, v in row.items() if k != "retention_purpose_count"} for pk, row in plans_before.items()})
        plan_immutable_after = _digest({pk: {k: v for k, v in row.items() if k != "retention_purpose_count"} for pk, row in plans_after.items()})
        assert plan_immutable_before == plan_immutable_after
        assert _digest(sorted(plans_before)) == _digest(sorted(plans_after))
        changed = {pk for pk in plans_before if _digest(plans_before[pk]) != _digest(plans_after[pk])}
        expected_changed = {pk for pk in valid
                            if plans_before[pk]["retention_purpose_count"] != prepared["k"]}
        assert _digest(sorted(changed)) == _digest(sorted(expected_changed))
        for pk, original in plans_before.items():
            expected_plan = dict(original)
            if pk in valid:
                expected_plan["retention_purpose_count"] = prepared["k"]
            assert _digest(expected_plan) == _digest(plans_after[pk])
    after_domain, after_media = _snapshot(queries), _tree(settings.MEDIA_ROOT)
    assert after_domain == domain and after_media == media
    preserved_target_sha256 = _digest({pk: after[pk] for pk in before})
    assert preserved_target_sha256 == _digest(before)
    metric.update(inserted_rows=len(added), inserted_sha256=_digest(added),
                  selected_count=len(selected), invalid_selected_count=len(selected & prepared["invalid"]),
                  inserted_parent_count=len({str(row["report_id"] if kind == "urgent" else row["plan_id"]) for row in added.values()}),
                  preserved_target_sha256=preserved_target_sha256,
                  plan_immutable_before_sha256=plan_immutable_before,
                  plan_immutable_after_sha256=plan_immutable_after,
                  plan_rows_count=len(plans_before), report_rows_count=len(reports_before),
                  changed_plan_rows=len(changed), changed_plan_sha256=_digest(sorted(changed)),
                  target_before_count=len(before), target_after_count=len(after),
                  target_before_sha256=_digest(before), target_after_sha256=_digest(after),
                  domain_before=domain, domain_after=after_domain,
                  media_before=media, media_after=after_media)


def _skip(kind, prepared, observed, settings):
    model = Report if kind == "urgent" else ErasurePlan
    held, *others = prepared["ids"]
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
            _phase(kind, "while_holder_active", others, prepared, observed, settings)
        finally:
            connections.close_all()
            observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

    try:
        with transaction.atomic():
            model.objects.select_for_update().get(pk=held)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder_pid = cursor.fetchone()[0]
            future = pool.submit(worker)
            try:
                future.result(timeout=15)
            except FutureTimeoutError:
                raw = runtime.get("raw")
                if raw is not None and not raw.closed:
                    raw.cancel()
                raise
            assert holder_pid != runtime["pid"] and connection.in_atomic_block
            observed.update(holder_pid=holder_pid, worker_pid=runtime["pid"],
                            completed_while_holder_active=True)
    finally:
        if future is not None and not future.done():
            raw = runtime.get("raw")
            if raw is not None and not raw.closed:
                raw.cancel()
            try:
                future.result(timeout=15)
            except Exception as error:
                observed["cleanup_exception_type"] = type(error).__name__
        pool.shutdown(wait=True, cancel_futures=True)
        observed.update(thread_finished=future is None or future.done(),
                        holder_released=not connection.in_atomic_block)
    assert observed["thread_finished"] and observed["worker_connections_closed"]
    assert observed["holder_released"]
    _phase(kind, "after_release", [held], prepared, observed, settings)


def _profile(kind, count, mode, request, settings, monkeypatch, record_property):
    started = perf_counter()
    observed = {"status": "not_started", "kind": kind, "mode": mode,
                "volume": count, "phases": [],
                "scope": "BEFORE native task.run; synthetic authenticated metadata; no worker/human/erasure claim",
                "timing": "N=1 per phase; SQL forwarding inclusive; setup/snapshots/assertions outside task wall; no p95/CPU/SLA",
                "cleanup": "pytest transaction database and native fixture teardown; no broker or service started"}
    try:
        _guard(request, settings)
        prepared = _prepare(kind, count, mode == "mixed", request, settings, monkeypatch)
        observed.update(status="prepared", setup_seconds=perf_counter() - started,
                        target_ids_sha256=_digest(prepared["ids"]), retained_purpose_count=prepared["k"])
        if mode == "skip_locked":
            _skip(kind, prepared, observed, settings)
        else:
            _phase(kind, "first_batch", prepared["ids"][:100], prepared, observed, settings)
            if count > 100:
                _phase(kind, "second_batch", prepared["ids"][100:], prepared, observed, settings)
        # An invalid plan remains eligible and fails again, unlike a valid replay.
        _phase(kind, "invalid_retry" if mode == "mixed" else "idempotent_replay",
               prepared["invalid"], prepared, observed, settings)
        observed["status"] = "passed"
    finally:
        error = sys.exc_info()[0]
        if error is not None:
            observed.update(status="failed", failure_class=error.__name__)
        observed["case_seconds"] = perf_counter() - started
        observed["measured_seconds"] = sum(p.get("wall_seconds", 0) for p in observed["phases"])
        observed["setup_and_qa_seconds"] = observed["case_seconds"] - observed["measured_seconds"]
        record_property("owned_alert_retention_reconcile_profile",
                        json.dumps(observed, sort_keys=True, allow_nan=False))


@pytest.mark.parametrize("count", [0, 1, 10, 100, 101])
def test_owned_urgent_alert_volume(request, settings, monkeypatch, record_property, count):
    _profile("urgent", count, "volume", request, settings, monkeypatch, record_property)


@pytest.mark.parametrize("count", [0, 1, 10, 100, 101])
def test_owned_retention_calendar_volume(request, settings, monkeypatch, record_property, count):
    _profile("retention", count, "volume", request, settings, monkeypatch, record_property)


def test_owned_urgent_alert_skip_locked(request, settings, monkeypatch, record_property):
    _profile("urgent", 3, "skip_locked", request, settings, monkeypatch, record_property)


def test_owned_retention_calendar_skip_locked(request, settings, monkeypatch, record_property):
    _profile("retention", 3, "skip_locked", request, settings, monkeypatch, record_property)


def test_owned_retention_calendar_mixed(request, settings, monkeypatch, record_property):
    _profile("retention", 3, "mixed", request, settings, monkeypatch, record_property)
