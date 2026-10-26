"""Finite BEFORE task.run profile: owned PostgreSQL and tiny local fixtures.

Fixture clones are not verified business executions. N=1 per phase; no p95,
provider, S3, worker, Beat or authorization claim. Previous repository S3
witnesses remain separate from this local Fernet-content measurement.
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
from test_owned_delivery_purge_profile import _clone, _digest, _evidence, _tree
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_object_delivery import staged

from apps.mediafiles.models import Photo
from apps.safety.crypto import cipher
from apps.safety.models import (
    RightsAction,
    RightsExport,
    RightsExportDownload,
    RightsExportImage,
    RightsExportPart,
)
from apps.safety.rights_object_models import RightsObjectDelivery
from apps.safety.tasks import purge_expired_exports

pytestmark = pytest.mark.django_db(transaction=True)
TARGETS = (RightsExport, RightsExportImage, RightsExportPart, RightsObjectDelivery)


def _guard(request, settings):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit serial owned PostgreSQL export purge profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _rows():
    return {model._meta.label: {str(row["id"]): row
            for row in model.objects.order_by("pk").values()} for model in TARGETS}


def _queries():
    return {model._meta.label: model.objects.all()
            for model in apps.get_models(include_auto_created=True) if model not in TARGETS}


def _prepare(request, settings, tmp_path, count):
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = False
    _, export, person, _, seed, _ = staged(request, settings, tmp_path)
    root = tmp_path / "owned-export-profile"
    root.mkdir(mode=0o700)
    assert root.is_relative_to(tmp_path) and not root.is_symlink()
    (tmp_path / seed.object_name).rename(root / seed.object_name)
    settings.RIGHTS_DELIVERY_ROOT = root
    now = timezone.now()
    future = now + timedelta(days=7)
    RightsExport.objects.filter(pk=export.pk).update(expires_at=future)
    RightsObjectDelivery.objects.filter(pk=seed.pk).update(expires_at=future)
    export.refresh_from_db()
    seed.refresh_from_db()
    photo = Photo.objects.filter(revision__listing__person=person).first()
    assert photo is not None
    token = cipher().encrypt(b"synthetic-tiny-export-profile").decode()
    assert cipher().decrypt(token.encode()) == b"synthetic-tiny-export-profile"
    # One native seed; batch rows below are fixture-only clones, never authority evidence.
    actions, exports, images, parts, downloads, deliveries = [], [], [], [], [], []
    due = set()
    for index in range(count + 2):
        action = RightsAction(**(_clone(export.action) | {"key": uuid4()}))
        actions.append(action)
        values = _clone(export) | {"action_id": action.pk, "encrypted_payload": token,
                                  "expires_at": now - timedelta(days=1) if index < count else future,
                                  "purged_at": now if index == count + 1 else None}
        # RightsAction has an integer identity, populated by bulk_create below.
        row = RightsExport(**values)
        exports.append(row)
        images.append(RightsExportImage(export=row, photo=photo, encrypted_content=token))
        parts.append(RightsExportPart(export=row, position=1, encrypted_content=token, attachments=[]))
        downloads.append(RightsExportDownload(**(_clone(seed.download) |
                         {"key": uuid4(), "export_id": row.pk, "image_id": None, "part_id": None})))
        deliveries.append(RightsObjectDelivery(**(_clone(seed) |
                          {"object_name": uuid4().hex, "download_id": None,
                           "expires_at": future, "purged_at": None})))
        if index < count:
            due.add(str(row.pk))
    RightsAction.objects.bulk_create(actions)
    for row, action in zip(exports, actions, strict=True):
        row.action_id = action.pk
    RightsExport.objects.bulk_create(exports)
    RightsExportImage.objects.bulk_create(images)
    RightsExportPart.objects.bulk_create(parts)
    RightsExportDownload.objects.bulk_create(downloads)
    content = b"synthetic-tiny-export-profile"
    for delivery, download in zip(deliveries, downloads, strict=True):
        delivery.download_id = download.pk
        delivery.content_bytes = len(content)
        delivery.content_sha256 = hashlib.sha256(content).hexdigest()
        (root / delivery.object_name).write_bytes(content)
        (root / delivery.object_name).chmod(0o600)
    RightsObjectDelivery.objects.bulk_create(deliveries)
    assert RightsExportImage.objects.filter(export__in=exports).count() == len(exports)
    assert RightsExportPart.objects.filter(export__in=exports).count() == len(exports)
    assert all(row.encrypted_payload for row in exports)
    return root, due


def _measure(name, observed, root, monkeypatch, fail_second=False):
    metric = {"phase": name, "sql_count": 0, "sql_seconds": 0.0,
              "operations": {}, "unlink_calls": 0, "unlink_seconds": 0.0}
    observed["phases"].append(metric)
    unlink = Path.unlink
    touched = []

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

    def observed_unlink(path, *args, **kwargs):
        if path.parent != root:
            return unlink(path, *args, **kwargs)
        started = perf_counter()
        metric["unlink_calls"] += 1
        touched.append(path.name)
        try:
            if fail_second and len(touched) == 2:
                raise OSError("synthetic-second-local-unlink-failure")
            return unlink(path, *args, **kwargs)
        finally:
            metric["unlink_seconds"] += perf_counter() - started

    try:
        with monkeypatch.context() as patch:
            patch.setattr(Path, "unlink", observed_unlink)
            with connection.execute_wrapper(sql_observer):
                started = perf_counter()
                try:
                    result = purge_expired_exports.run()
                finally:
                    metric["wall_seconds"] = perf_counter() - started
        metric["returned_count"] = result
        return result
    except Exception as error:
        metric.update(exception_type=type(error).__name__, returned_count=None)
        raise
    finally:
        observed["private_touched"] = touched


def _assert_rows(before, after, changed):
    downloads = dict(RightsExportDownload.objects.values_list("pk", "export_id"))
    for label, rows in before.items():
        same_identities = set(rows) == set(after[label])
        assert same_identities
        for pk, row in rows.items():
            current = after[label][pk]
            owner = pk if label == RightsExport._meta.label else str(row.get("export_id"))
            if label == RightsObjectDelivery._meta.label:
                owner = str(downloads[row["download_id"]])
            expected = dict(row)
            if owner in changed:
                if label == RightsExport._meta.label:
                    assert row["purged_at"] is None and current["purged_at"] is not None
                    expected.update(encrypted_payload="", purged_at=current["purged_at"])
                elif label == RightsObjectDelivery._meta.label:
                    assert row["purged_at"] is None and current["purged_at"] is not None
                    expected["purged_at"] = current["purged_at"]
                else:
                    expected["encrypted_content"] = ""
            assert _digest(expected) == _digest(current)


def _phase(name, expected, remaining, observed, root, monkeypatch, queries, settings, failure=False):
    before, files = _rows(), _tree(root)
    domain, media = _snapshot(queries), _tree(settings.MEDIA_ROOT, exclude=root)
    start = timezone.now()
    if failure:
        with pytest.raises(OSError):
            _measure(name, observed, root, monkeypatch, fail_second=True)
        count = None
    else:
        count = _measure(name, observed, root, monkeypatch)
    end = timezone.now()
    after = _rows()
    observed["phases"][-1].update(expected_count=expected, rows_before_sha256=_digest(before),
                                  rows_after_sha256=_digest(after))
    label = RightsExport._meta.label
    changed = {pk for pk in before[label] if before[label][pk]["purged_at"] != after[label][pk]["purged_at"]}
    observed["phases"][-1]["actual_changed_count"] = len(changed)
    allowed_changes = changed <= remaining
    assert len(changed) == expected and allowed_changes
    assert changed == set(sorted(remaining)[:expected])
    assert failure or count == expected
    assert all(start <= after[label][pk]["purged_at"] <= end for pk in changed)
    _assert_rows(before, after, changed)
    touched = observed.pop("private_touched")
    if failure:
        assert len(touched) == 2 and touched[0] != touched[1]
        deleted = {touched[0]}
        assert (root / touched[1]).is_file()
    else:
        downloads = dict(RightsExportDownload.objects.values_list("pk", "export_id"))
        deleted = {row["object_name"] for row in before[RightsObjectDelivery._meta.label].values()
                   if str(downloads[row["download_id"]]) in changed and row["purged_at"] is None}
        assert len(touched) == expected
    actual = _tree(root)
    assert _digest(actual) == _digest({key: value for key, value in files.items() if key not in deleted})
    domain_after = _snapshot(queries)
    media_after = _tree(settings.MEDIA_ROOT, exclude=root)
    assert domain_after == domain
    assert _digest(media_after) == _digest(media)
    observed["phases"][-1].update(
        other_tables_before_sha256=domain["sha256"],
        other_tables_after_sha256=domain_after["sha256"],
        media_before_sha256=_digest(media), media_after_sha256=_digest(media_after),
        native_pk_order_verified=True,
    )
    observed["phases"][-1].update(expected_count=expected, actual_changed_count=len(changed),
        changed_rows_sha256=_digest(sorted(changed)), remaining_before_count=len(remaining),
        remaining_after_count=len(remaining - changed), rows_before_sha256=_digest(before),
        rows_after_sha256=_digest(after), directory_before=_evidence(files), directory_after=_evidence(actual),
        expected_deletions=len(set(files) & deleted), actual_deletions=len(set(files) - set(actual)),
        all_sql_rolled_back=failure, first_physical_delete_retained=failure)
    return remaining - changed


def _skip(remaining, observed, root, monkeypatch, queries, settings):
    held = next(iter(remaining))
    runtime, pool, future = {}, ThreadPoolExecutor(max_workers=1), None

    def worker():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout TO '10s'")
                cursor.execute("SELECT pg_backend_pid()")
                runtime["pid"] = cursor.fetchone()[0]
                runtime["raw"] = connection.connection
            return _phase("while_holder_active", 2, remaining - {held}, observed,
                          root, monkeypatch, queries, settings)
        finally:
            connections.close_all()
            observed["worker_connections_closed"] = all(c.connection is None for c in connections.all())

    try:
        with transaction.atomic():
            RightsExport.objects.select_for_update().get(pk=held)
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
            observed.update(distinct_postgresql_pids=True, completed_while_holder_active=True)
    finally:
        if future is not None and not future.done():
            try:
                future.result(timeout=15)
            except Exception:
                observed["cleanup_worker_exception"] = True
        pool.shutdown(wait=True, cancel_futures=True)
        observed.update(thread_finished=future is None or future.done(),
                        holder_released=not connection.in_atomic_block)
    assert observed["worker_connections_closed"] and observed["thread_finished"] and observed["holder_released"]
    return _phase("after_release", 1, {held}, observed, root, monkeypatch, queries, settings)


@pytest.mark.parametrize("expired_count", [0, 1, 10, 100, 1001])
def test_owned_export_purge_volume(request, settings, tmp_path, monkeypatch, record_property, expired_count):
    _profile(request, settings, tmp_path, monkeypatch, record_property, expired_count, "volume")


def test_owned_export_purge_skip_locked(request, settings, tmp_path, monkeypatch, record_property):
    _profile(request, settings, tmp_path, monkeypatch, record_property, 3, "skip_locked")


def test_owned_export_purge_partial_failure(request, settings, tmp_path, monkeypatch, record_property):
    _profile(request, settings, tmp_path, monkeypatch, record_property, 2, "partial_failure")


def _profile(request, settings, tmp_path, monkeypatch, record_property, count, mode):
    started = perf_counter()
    observed = {"status": "not_started", "mode": mode, "eligible_count": count, "phases": [],
                "scope": "BEFORE native task.run; fixture-only clones; local Fernet and files; no S3/provider/worker/authority claim",
                "timing": "N=1 per phase; forwarding SQL/unlink timings; setup and QA outside task clock; no p95",
                "fixture_pins": "native seed and fresh clone expiry extended seven days; already-purged clone retained"}
    try:
        _guard(request, settings)
        root, eligible = _prepare(request, settings, tmp_path, count)
        queries = _queries()
        rows, files, domain = _rows(), _tree(root), _snapshot(queries)
        observed.update(setup_seconds=perf_counter() - started, target_before_sha256=_digest(rows),
                        directory_before=_evidence(files), domain_before=domain)
        remaining = set(eligible)
        if mode == "partial_failure":
            _phase("second_unlink_failure", 0, remaining, observed, root, monkeypatch, queries, settings, failure=True)
        if mode == "skip_locked":
            remaining = _skip(remaining, observed, root, monkeypatch, queries, settings)
        else:
            remaining = _phase("first_batch", min(count, 1000), remaining, observed, root, monkeypatch, queries, settings)
            if count == 1001:
                remaining = _phase("second_batch", 1, remaining, observed, root, monkeypatch, queries, settings)
        assert not remaining
        _phase("idempotent_replay", 0, set(), observed, root, monkeypatch, queries, settings)
        _assert_rows(rows, _rows(), eligible)
        assert _snapshot(queries) == domain
        observed.update(status="passed", target_after_sha256=_digest(_rows()),
                        directory_after=_evidence(_tree(root)), domain_after=_snapshot(queries))
    finally:
        observed.pop("private_touched", None)
        if sys.exc_info()[0] is not None:
            observed["failure_type"] = sys.exc_info()[0].__name__
        observed["case_seconds"] = perf_counter() - started
        observed["measured_seconds"] = sum(item.get("wall_seconds", 0) for item in observed["phases"])
        observed["non_measured_seconds"] = observed["case_seconds"] - observed["measured_seconds"]
        record_property("owned_export_purge_profile", json.dumps(observed, sort_keys=True, allow_nan=False))
