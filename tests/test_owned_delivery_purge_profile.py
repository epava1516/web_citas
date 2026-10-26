"""Finite BEFORE baseline of real task.run, owned PG and synthetic local files.

One sample per phase, no p95/causal comparison, worker/provider/Beat/authorization
claim. 1000 bounds selected grants, not retained metadata or directory scanning.
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
from django.utils import timezone
from test_operational_recovery_authority_wait import _snapshot
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_object_delivery import staged

from apps.safety.models import RightsAction, RightsExport, RightsExportDownload
from apps.safety.rights_object_delivery import purge_object_deliveries
from apps.safety.rights_object_models import RightsObjectDelivery

pytestmark = pytest.mark.django_db(transaction=True)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str,
                                    separators=(",", ":")).encode()).hexdigest()


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL delivery purge profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _clone(row):
    return {field.attname: getattr(row, field.attname)
            for field in row._meta.concrete_fields if not field.primary_key}


def _rows():
    return {str(row["id"]): row
            for row in RightsObjectDelivery.objects.order_by("pk").values()}


def _queries():
    return {model._meta.label: model.objects.all()
            for model in apps.get_models(include_auto_created=True)
            if model is not RightsObjectDelivery}


def _tree(root, exclude=None):
    """Local oracle retains names privately; emitted evidence is only count/hash."""
    root = Path(root)
    found = {}
    if root.exists():
        for path in root.rglob("*"):
            if exclude is not None and (path == exclude or exclude in path.parents):
                continue
            safe_entry = not path.is_symlink()
            assert safe_entry
            relative = str(path.relative_to(root))
            if path.is_file():
                found[relative] = ("file", path.stat().st_size,
                                   hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mtime_ns,
                                   path.stat().st_mode & 0o777)
            else:
                found[relative] = ("directory",)
    return found


def _evidence(tree):
    return {"entries": len(tree), "sha256": _digest(tree)}


def _prepare(request, settings, tmp_path, count, matrix=False):
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = False
    _, export, _, _, seed, _ = staged(request, settings, tmp_path)
    root = tmp_path / "owned-delivery-profile"
    root.mkdir()
    assert root.is_relative_to(tmp_path) and not root.is_symlink()
    (tmp_path / seed.object_name).rename(root / seed.object_name)
    settings.RIGHTS_DELIVERY_ROOT = root
    now = timezone.now()
    future = now + timedelta(days=7)
    # Fixture-only expiry extension keeps the native seed referenced throughout
    # expensive setup/snapshots. This does not exercise TTL admission/authority.
    RightsExport.objects.filter(pk=export.pk).update(expires_at=future)
    RightsObjectDelivery.objects.filter(pk=seed.pk).update(expires_at=future)
    seed.refresh_from_db()
    export.refresh_from_db()
    aged = now.timestamp() - 3600
    os.utime(root / seed.object_name, (aged, aged))
    due = set()
    for index in range(count + 1):
        parent = export
        branch = index if matrix and index < count else 0
        if branch in (2, 3):
            action = _clone(export.action)
            action["key"] = uuid4()
            action = RightsAction.objects.create(**action)
            values = _clone(export)
            values.update(action_id=action.pk)
            values.update(purged_at=now if branch == 2 else None,
                          expires_at=now - timedelta(days=1) if branch == 3 else future)
            parent = RightsExport.objects.create(**values)
        download_values = _clone(seed.download)
        download_values.update(key=uuid4(), export_id=parent.pk)
        download = RightsExportDownload.objects.create(**download_values)
        content = b"synthetic-delivery-purge-profile"
        values = _clone(seed)
        values.update(download_id=download.pk, object_name=uuid4().hex,
                      content_sha256=hashlib.sha256(content).hexdigest(),
                      content_bytes=len(content), generation=seed.generation,
                      expires_at=now - timedelta(days=1) if branch == 0 else future)
        if branch == 1:
            values["generation"] = "synthetic-obsolete"
        if index == count:
            values["purged_at"] = now
        row = RightsObjectDelivery.objects.create(**values)
        if index < count:
            due.add(str(row.pk))
            (root / row.object_name).write_bytes(content)
            os.utime(root / row.object_name, (aged, aged))
    orphan = root / uuid4().hex
    orphan.write_bytes(b"synthetic-aged-orphan")
    os.utime(orphan, (aged, aged))
    fresh = root / uuid4().hex
    fresh.write_bytes(b"synthetic-fresh-orphan")
    # Future mtime is a fixture pin, not a global clock override or TTL claim.
    os.utime(fresh, (future.timestamp(), future.timestamp()))
    (root / "unrelated.txt").write_bytes(b"synthetic-unrelated")
    return root, due, orphan.name


def _measure(phase, observed, root, monkeypatch, fault_names=()):
    metric = {"phase": phase, "sql_count": 0, "sql_seconds": 0.0,
              "operations": {}, "unlink_calls": 0, "unlink_seconds": 0.0,
              "directory_iterators": 0, "directory_next_calls": 0,
              "directory_next_seconds": 0.0}
    observed["phases"].append(metric)
    unlink, iterdir = Path.unlink, Path.iterdir
    targets = []

    def sql_observer(execute, sql, params, many, context):
        token = str(sql).lstrip().split(None, 1)[0].upper()
        operation = token if token in {"SELECT", "UPDATE", "INSERT", "DELETE",
                                      "SAVEPOINT", "RELEASE", "ROLLBACK"} else "OTHER"
        start = perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed = perf_counter() - start
            metric["sql_count"] += 1
            metric["sql_seconds"] += elapsed
            item = metric["operations"].setdefault(operation, {"count": 0, "seconds": 0.0})
            item["count"] += 1
            item["seconds"] += elapsed

    def observed_unlink(path, *args, **kwargs):
        if path.parent != root:
            return unlink(path, *args, **kwargs)
        start = perf_counter()
        metric["unlink_calls"] += 1
        try:
            if path.name in fault_names:
                targets.append(path.name)
                if len(targets) == 2:
                    raise OSError("synthetic-owned-unlink-failure")
            return unlink(path, *args, **kwargs)
        finally:
            metric["unlink_seconds"] += perf_counter() - start

    def observed_iterdir(path):
        source = iterdir(path)
        if path != root:
            yield from source
            return
        metric["directory_iterators"] += 1
        try:
            while True:
                start = perf_counter()
                try:
                    item = next(source)
                except StopIteration:
                    return
                finally:
                    metric["directory_next_calls"] += 1
                    metric["directory_next_seconds"] += perf_counter() - start
                yield item
        finally:
            source.close()

    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path, "unlink", observed_unlink)
            patch.setattr(Path, "iterdir", observed_iterdir)
            with connection.execute_wrapper(sql_observer):
                call_started = perf_counter()
                try:
                    result = purge_object_deliveries.run()
                finally:
                    metric["wall_seconds"] = perf_counter() - call_started
        metric["returned_count"] = result
        return result
    finally:
        # Private local identity only; never include names in emitted properties.
        observed["fault_targets"] = targets


def _assert_rows(before, after, changed):
    assert set(before) == set(after)
    for pk, original in before.items():
        current = after[pk]
        if pk in changed:
            markers_valid = original["purged_at"] is None and current["purged_at"] is not None
            assert markers_valid
            before_hash = _digest({k: v for k, v in original.items() if k != "purged_at"})
            after_hash = _digest({k: v for k, v in current.items() if k != "purged_at"})
            assert before_hash == after_hash
        else:
            before_hash, after_hash = _digest(original), _digest(current)
            assert before_hash == after_hash


def _phase(name, expected, remaining, observed, root, orphan, monkeypatch, queries, settings):
    before, files = _rows(), _tree(root)
    domain = _snapshot(queries)
    media = _tree(settings.MEDIA_ROOT, exclude=root)
    start = timezone.now()
    count = _measure(name, observed, root, monkeypatch)
    end = timezone.now()
    after = _rows()
    changed = {pk for pk in before if before[pk]["purged_at"] != after[pk]["purged_at"]}
    assert count == expected == len(changed) and changed <= remaining
    timestamp_bounds = all(start <= after[pk]["purged_at"] <= end for pk in changed)
    assert timestamp_bounds
    _assert_rows(before, after, changed)
    deleted = {before[pk]["object_name"] for pk in changed} | {orphan}
    actual_tree = _tree(root)
    actual_hash = _digest(actual_tree)
    expected_hash = _digest({key: value for key, value in files.items() if key not in deleted})
    assert actual_hash == expected_hash
    after_domain = _snapshot(queries)
    assert after_domain == domain
    after_media_hash, before_media_hash = _digest(_tree(settings.MEDIA_ROOT, exclude=root)), _digest(media)
    assert after_media_hash == before_media_hash
    observed["phases"][-1].update(changed_rows_sha256=_digest(sorted(changed)),
                                  changed_rows_count=len(changed),
                                  remaining_before_count=len(remaining),
                                  remaining_after_count=len(remaining - changed),
                                  physical_files_removed=len(set(files) - set(actual_tree)),
                                  directory_before=_evidence(files),
                                  directory_after=_evidence(actual_tree))
    return remaining - changed


def _skip(remaining, observed, root, orphan, monkeypatch, queries, settings):
    held = next(iter(remaining))
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
            return _phase("while_holder_active", 2, remaining - {held}, observed,
                          root, orphan, monkeypatch, queries, settings)
        finally:
            connections.close_all()
            observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

    try:
        with transaction.atomic():
            RightsObjectDelivery.objects.select_for_update().get(pk=held)
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                holder = cursor.fetchone()[0]
            future = pool.submit(worker)
            try:
                assert future.result(timeout=15) == set()
            except FutureTimeoutError:
                raw = runtime.get("raw")
                if raw is not None and not raw.closed:
                    raw.cancel()
                raise
            assert holder != runtime["pid"] and connection.in_atomic_block
            observed.update(holder_pid=holder, worker_pid=runtime["pid"],
                            completed_while_holder_active=True)
    finally:
        if future is not None and not future.done():
            try:
                future.result(timeout=15)
            except Exception:
                observed["cleanup_worker_exception"] = True
        pool.shutdown(wait=True, cancel_futures=True)
        observed.update(thread_finished=future is None or future.done(),
                        holder_released=not connection.in_atomic_block)
    assert observed["worker_connections_closed"] and observed["thread_finished"]
    assert observed["holder_released"]
    return _phase("after_release", 1, {held}, observed, root, orphan, monkeypatch, queries, settings)


def _failure(remaining, observed, root, monkeypatch, queries, settings):
    before, files = _rows(), _tree(root)
    domain, media = _snapshot(queries), _tree(settings.MEDIA_ROOT, exclude=root)
    names = {before[pk]["object_name"] for pk in remaining}
    with pytest.raises(OSError):
        _measure("second_unlink_failure", observed, root, monkeypatch, names)
    targets = observed.pop("fault_targets")
    assert len(targets) == 2 and targets[0] != targets[1]
    _assert_rows(before, _rows(), set())
    actual_tree = _tree(root)
    actual_hash = _digest(actual_tree)
    expected_hash = _digest({key: value for key, value in files.items() if key != targets[0]})
    assert actual_hash == expected_hash
    assert observed["phases"][-1]["directory_iterators"] == 0
    after_domain = _snapshot(queries)
    assert after_domain == domain
    after_media_hash, before_media_hash = _digest(_tree(settings.MEDIA_ROOT, exclude=root)), _digest(media)
    assert after_media_hash == before_media_hash
    observed["failure_order_sha256"] = _digest(targets)
    observed["sql_rollback_physical_first_delete_retained"] = True
    observed["phases"][-1].update(exception_type="OSError", returned_count=None,
                                  changed_rows_count=0, remaining_before_count=len(remaining),
                                  remaining_after_count=len(remaining), physical_files_removed=1,
                                  directory_before=_evidence(files), directory_after=_evidence(actual_tree))


@pytest.mark.parametrize("expired_count", [0, 1, 10, 100, 1001])
def test_owned_delivery_purge_volume(request, settings, tmp_path, monkeypatch, record_property, expired_count):
    _profile(request, settings, tmp_path, monkeypatch, record_property, expired_count, "volume")


def test_owned_delivery_purge_eligibility(request, settings, tmp_path, monkeypatch, record_property):
    _profile(request, settings, tmp_path, monkeypatch, record_property, 4, "eligibility")


def test_owned_delivery_purge_skip_locked(request, settings, tmp_path, monkeypatch, record_property):
    _profile(request, settings, tmp_path, monkeypatch, record_property, 3, "skip_locked")


def test_owned_delivery_purge_partial_failure(request, settings, tmp_path, monkeypatch, record_property):
    _profile(request, settings, tmp_path, monkeypatch, record_property, 2, "partial_failure")


def _profile(request, settings, tmp_path, monkeypatch, record_property, count, mode):
    started = perf_counter()
    observed = {"status": "not_started", "mode": mode, "eligible_count": count, "phases": [],
                "scope": "BEFORE native task.run only; synthetic fixture metadata; no authorization/provider/worker claim",
                "timing": "N=1 per phase; SQL/unlink/iterator-next forwarding time; setup and QA outside call clock; no p95",
                "limit": "1000 selected SQL rows; retained set and directory scan have no global 1000 limit",
                "fixture_pins": "seed grant/export expiry and fresh orphan mtime extended seven days for profile only"}
    try:
        _guard(request, settings)
        root, eligible, orphan = _prepare(request, settings, tmp_path, count, mode == "eligibility")
        queries = _queries()
        rows, files = _rows(), _tree(root)
        domain, media = _snapshot(queries), _tree(settings.MEDIA_ROOT, exclude=root)
        def fingerprints(values):
            return {
                "immutable_sha256": _digest({pk: {k: v for k, v in row.items() if k != "purged_at"}
                                             for pk, row in values.items()}),
                "pins_sha256": _digest({pk: row for pk, row in values.items() if pk not in eligible}),
                "row_count": len(values), "pin_count": len(values) - len(eligible),
            }

        observed.update(row_before=fingerprints(rows),
                        directory_before=_evidence(files), target_before_sha256=_digest(rows),
                        domain_before=domain, media_before=_evidence(media),
                        setup_seconds=perf_counter() - started)
        remaining = set(eligible)
        if mode == "partial_failure":
            _failure(remaining, observed, root, monkeypatch, queries, settings)
        if mode == "skip_locked":
            remaining = _skip(remaining, observed, root, orphan, monkeypatch, queries, settings)
        else:
            remaining = _phase("first_batch", min(count, 1000), remaining, observed,
                               root, orphan, monkeypatch, queries, settings)
            if count == 1001:
                remaining = _phase("second_batch", 1, remaining, observed,
                                   root, orphan, monkeypatch, queries, settings)
        assert not remaining
        _phase("idempotent_replay", 0, set(), observed, root, orphan, monkeypatch, queries, settings)
        _assert_rows(rows, _rows(), eligible)
        deleted = {rows[pk]["object_name"] for pk in eligible} | {orphan}
        actual_hash = _digest(_tree(root))
        expected_hash = _digest({key: value for key, value in files.items() if key not in deleted})
        assert actual_hash == expected_hash
        after_domain = _snapshot(queries)
        assert after_domain == domain
        after_media_hash, before_media_hash = _digest(_tree(settings.MEDIA_ROOT, exclude=root)), _digest(media)
        assert after_media_hash == before_media_hash
        after_rows = _rows()
        observed.update(status="passed", directory_after=_evidence(_tree(root)),
                        target_after_sha256=_digest(after_rows), row_after=fingerprints(after_rows),
                        domain_after=after_domain, media_after=_evidence(_tree(settings.MEDIA_ROOT, exclude=root)))
        assert observed["row_before"] == observed["row_after"]
    finally:
        observed.pop("fault_targets", None)
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["case_seconds"] = perf_counter() - started
        observed["measured_seconds"] = sum(item.get("wall_seconds", 0) for item in observed["phases"])
        observed["non_measured_seconds"] = observed["case_seconds"] - observed["measured_seconds"]
        record_property("owned_delivery_purge_profile", json.dumps(observed, sort_keys=True, allow_nan=False))
