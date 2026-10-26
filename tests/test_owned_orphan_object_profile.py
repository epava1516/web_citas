"""Finite owned PostgreSQL/RustFS profiles of the native orphan task body.

One sample per phase. Synthetic application time proves eligibility, not a
natural 24-hour wait, worker execution, cadence, admission or provider failure.
"""

import hashlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from time import perf_counter
from urllib.parse import urlsplit
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from capacity_runtime_role import _owned_database
from django.apps import apps
from django.db import connection
from django.utils import timezone
from test_operational_recovery_authority_wait import _snapshot
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, prepared
from test_rights_object_store import object_store as real_object_store

from apps.mediafiles.models import Photo
from apps.safety import rights_object_content
from apps.safety.models import RightsExportImage, RightsExportPart
from apps.safety.object_storage.repository import PREFIX, ObjectRepository
from scripts.local_ci_requirements import OBJECT_STORE_TEST_IMAGE

object_store = real_object_store
pytestmark = pytest.mark.django_db(transaction=True)
BUCKET_PREFIX = "n09n-orphan-owned-"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str,
                                    separators=(",", ":")).encode()).hexdigest()


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned PostgreSQL orphan profile only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_")
    _owned_database()


def _container(client):
    """Inspect only allowlisted Docker fields; never fetch Config.Env."""
    endpoint = urlsplit(client.meta.endpoint_url)
    assert endpoint.scheme == "http" and endpoint.hostname == "127.0.0.1"
    assert endpoint.port and not endpoint.username and not endpoint.password
    identifiers = subprocess.run(
        ["docker", "ps", "-q", "--filter", "label=web-modelos-object-tests"],
        capture_output=True, text=True, check=True, timeout=10).stdout.split()
    matches = []
    template = ('{"id":{{json .Id}},"name":{{json .Name}},'
                '"image":{{json .Config.Image}},"labels":{{json .Config.Labels}},'
                '"host":{ "NanoCpus":{{json .HostConfig.NanoCpus}},"Memory":{{json .HostConfig.Memory}},"MemorySwap":{{json .HostConfig.MemorySwap}},"Tmpfs":{{json .HostConfig.Tmpfs}},"Privileged":{{json .HostConfig.Privileged}},"Binds":{{json .HostConfig.Binds}},"LogDriver":{{json .HostConfig.LogConfig.Type}}},"running":{{json .State.Running}},'
                '"ports":{{json .NetworkSettings.Ports}}}')
    for identifier in identifiers:
        assert re.fullmatch(r"[0-9a-f]{12,64}", identifier)
        item = json.loads(subprocess.run(
            ["docker", "inspect", "--format", template, identifier],
            capture_output=True, text=True, check=True, timeout=10).stdout)
        ports = item["ports"].get("9000/tcp") or []
        if not any(port["HostIp"] == "127.0.0.1"
                   and port["HostPort"] == str(endpoint.port) for port in ports):
            continue
        assert item["name"].startswith("/web-modelos-object-test-")
        assert "web-modelos-object-tests" in item["labels"]
        assert item["image"] == OBJECT_STORE_TEST_IMAGE
        assert item["running"]
        host = item["host"]
        assert host["NanoCpus"] == 500000000
        assert host["Memory"] == host["MemorySwap"] == 512 * 1024 * 1024
        assert "size=128m" in host["Tmpfs"]["/data"]
        assert not host["Privileged"] and not host.get("Binds")
        assert host["LogDriver"] == "none"
        matches.append(item["id"])
    assert len(matches) == 1
    return {"container_id": matches[0], "cpu_limit": 0.5,
            "memory_bytes": 512 * 1024 * 1024, "data_tmpfs_bytes": 128 * 1024 * 1024}


def _owned(repo, fixture):
    same_client_private_bucket = repo.client is fixture.client and repo.bucket != fixture.bucket
    assert same_client_private_bucket
    private_bucket_shape = bool(re.fullmatch(BUCKET_PREFIX + r"[0-9a-f]{32}", repo.bucket))
    assert private_bucket_shape


def _media(root):
    root = Path(root)
    root_safe = not root.is_symlink()
    assert root_safe
    entries = {}
    if root.exists():
        stat = root.stat()
        entries["."] = (stat.st_mtime_ns, stat.st_mode)
        for path in root.rglob("*"):
            entry_safe = not path.is_symlink()
            assert entry_safe
            stat = path.stat()
            value = (stat.st_mtime_ns, stat.st_mode)
            if path.is_file():
                value += (stat.st_size, hashlib.sha256(path.read_bytes()).hexdigest())
            entries[str(path.relative_to(root))] = value
    return {"count": len(entries), "sha256": _digest(entries)}


def _inventory(repo):
    """Private key-indexed physical bytes and metadata oracle, outside timing."""
    objects = {}
    for page in repo.client.get_paginator("list_objects_v2").paginate(Bucket=repo.bucket):
        for item in page.get("Contents", []):
            response = repo.client.get_object(Bucket=repo.bucket, Key=item["Key"])
            body = response.pop("Body")
            try:
                content = body.read()
            finally:
                body.close()
            # ResponseMetadata contains request IDs, outside the retained-object oracle.
            response.pop("ResponseMetadata", None)
            objects[item["Key"]] = {"listing": item, "metadata": response,
                                    "sha256": hashlib.sha256(content).hexdigest(),
                                    "bytes": len(content)}
    return objects


def _read_pins(repo, pins):
    for reference, context, body in pins:
        output = io.BytesIO()
        repo.read(reference, output, context)
        matches = output.getvalue() == body
        assert matches


def _seed(repo, request, settings, count):
    settings.RIGHTS_OBJECT_STORAGE_ENABLED = False
    case, actor, _, _, _, _ = prepared(request, settings)
    export = make_copy(case, actor)
    pins = []
    image = RightsExportImage.objects.filter(export=export).first()
    photo = image.photo if image is not None else Photo.objects.order_by("pk").first()
    assert photo is not None
    context = rights_object_content.context(export.pk, "image", photo.pk)
    body = b"synthetic image metadata pin"
    reference = repo.write(io.BytesIO(body), context)
    if image is None:
        RightsExportImage.objects.create(export=export, photo=photo, encrypted_content=reference)
    else:
        RightsExportImage.objects.filter(pk=image.pk).update(encrypted_content=reference)
    pins.append((reference, context, body))
    for index in range(count + 1):
        position = 1000000 + index
        assert not RightsExportPart.objects.filter(export=export, position=position).exists()
        context = rights_object_content.context(export.pk, "part", position)
        body = b"synthetic part metadata pin"
        reference = repo.write(io.BytesIO(body), context)
        RightsExportPart.objects.create(export=export, position=position, encrypted_content=reference)
        pins.append((reference, context, body))
    orphans = set()
    for _ in range(count):
        reference = repo.write(io.BytesIO(b"synthetic aborted generation"), b"synthetic orphan")
        orphans.add(repo.descriptor(reference)["key"])
    purged = repo.write(io.BytesIO(b"synthetic already purged"), b"synthetic purged")
    repo.purge(purged)
    repo.client.put_object(Bucket=repo.bucket, Key="unrelated/synthetic-pin",
                           Body=b"synthetic unrelated prefix", IfNoneMatch="*")
    _read_pins(repo, pins)
    live_count = sum(model.objects.filter(encrypted_content__startswith=PREFIX).count()
                     for model in (RightsExportImage, RightsExportPart))
    assert live_count == count + 2
    return pins, orphans


def _measure(repo, name, observed, monkeypatch, future=None, inject=False):
    metric = {"phase": name, "result": None, "sql_count": 0, "sql_seconds": 0.0,
              "descriptor_count": 0, "descriptor_seconds": 0.0,
              "listing_pages": 0, "listing_items": 0, "listing_next_seconds": 0.0,
              "delete_attempts": 0, "delete_successes": 0, "delete_seconds": 0.0}
    observed["phases"].append(metric)
    descriptor, delete = repo.descriptor, repo.delete_unreferenced
    get_paginator = repo.client.get_paginator

    def sql_observer(execute, sql, params, many, context):
        started = perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            metric["sql_count"] += 1
            metric["sql_seconds"] += perf_counter() - started

    def describe(reference):
        started = perf_counter()
        try:
            return descriptor(reference)
        finally:
            metric["descriptor_count"] += 1
            metric["descriptor_seconds"] += perf_counter() - started

    def remove(key):
        started = perf_counter()
        metric["delete_attempts"] += 1
        try:
            if inject and metric["delete_attempts"] == 2:
                raise OSError("synthetic pre-delete interruption")
            result = delete(key)
            metric["delete_successes"] += 1
            return result
        finally:
            metric["delete_seconds"] += perf_counter() - started

    class ForwardPaginator:
        def __init__(self, paginator):
            self.paginator = paginator

        def paginate(self, *args, **kwargs):
            iterator = iter(self.paginator.paginate(*args, **kwargs))
            try:
                while True:
                    started = perf_counter()
                    try:
                        page = next(iterator)
                    except StopIteration:
                        return
                    finally:
                        metric["listing_next_seconds"] += perf_counter() - started
                    metric["listing_pages"] += 1
                    # Returned-page item count, not loop candidates visited.
                    metric["listing_items"] += len(page.get("Contents", []))
                    yield page
            finally:
                close = getattr(iterator, "close", None)
                if close is not None:
                    close()

    def paginator(operation):
        actual = get_paginator(operation)
        return ForwardPaginator(actual) if operation == "list_objects_v2" else actual

    with monkeypatch.context() as patch:
        patch.setattr(repo, "descriptor", describe)
        patch.setattr(repo, "delete_unreferenced", remove)
        patch.setattr(repo.client, "get_paginator", paginator)
        if future is not None:
            patch.setattr(timezone, "now", lambda: future)
        with connection.execute_wrapper(sql_observer):
            started = perf_counter()
            try:
                metric["result"] = rights_object_content.purge_orphan_export_objects.run()
            except Exception as error:
                metric["failure_class"] = type(error).__name__
                raise
            finally:
                metric["wall_seconds"] = perf_counter() - started
    return metric


def _phase(repo, fixture, pins, orphans, baseline, queries, media, settings,
           observed, monkeypatch, name, expected, future=None, inject=False):
    _owned(repo, fixture)
    before = _inventory(repo)
    _read_pins(repo, pins)
    row_before, media_before = _snapshot(queries), _media(settings.MEDIA_ROOT)
    assert row_before == baseline and media_before == media
    if inject:
        with pytest.raises(OSError):
            _measure(repo, name, observed, monkeypatch, future, inject=True)
    else:
        _measure(repo, name, observed, monkeypatch, future)
    metric = observed["phases"][-1]
    after = _inventory(repo)
    removed = set(before) - set(after)
    exact = (not (set(after) - set(before)) and removed <= orphans
             and len(removed) == expected
             and all(after[key] == before[key] for key in after))
    assert exact
    for key in removed:
        with pytest.raises(ClientError) as absent:
            repo.client.head_object(Bucket=repo.bucket, Key=key)
        assert absent.value.response["ResponseMetadata"]["HTTPStatusCode"] == 404
    if inject:
        assert metric["result"] is None and metric["failure_class"] == "OSError"
        assert metric["delete_attempts"] == 2 and metric["delete_successes"] == 1
        assert len(orphans & set(after)) == 1
    else:
        assert metric["result"] == expected
        assert metric["delete_attempts"] == metric["delete_successes"] == expected
    assert metric["descriptor_count"] == len(pins)
    row_after, media_after = _snapshot(queries), _media(settings.MEDIA_ROOT)
    assert row_after == baseline and media_after == media
    _read_pins(repo, pins)
    metric.update(bucket_before_count=len(before), bucket_after_count=len(after),
                  row_before_sha256=row_before["sha256"], row_after_sha256=row_after["sha256"],
                  media_before=media_before, media_after=media_after,
                  survivors_before_sha256=_digest({key: before[key] for key in after}),
                  removed_keys_sha256=_digest(sorted(removed)),
                  remaining_orphans_count=len(orphans & set(after)),
                  bucket_before_sha256=_digest(before), bucket_after_sha256=_digest(after),
                  removed_count=len(removed), retained_objects_exact=True,
                  sql_rows_preserved=True, media_preserved=True, live_readback=True)


def _cleanup(repo, fixture):
    _owned(repo, fixture)
    for page in repo.client.get_paginator("list_objects_v2").paginate(Bucket=repo.bucket):
        for item in page.get("Contents", []):
            repo.client.delete_object(Bucket=repo.bucket, Key=item["Key"])
    assert not repo.client.list_objects_v2(Bucket=repo.bucket).get("Contents", [])
    repo.client.delete_bucket(Bucket=repo.bucket)
    with pytest.raises(ClientError) as absent:
        repo.client.head_bucket(Bucket=repo.bucket)
    assert absent.value.response["ResponseMetadata"]["HTTPStatusCode"] == 404


@pytest.mark.parametrize("count,fault", [(0, False), (1, False), (10, False),
                                         (100, False), (2, True)])
def test_owned_orphan_object_profile(request, settings, monkeypatch, record_property, count, fault):
    observed = {"status": "not_started", "mode": "interrupted" if fault else "volume",
                "N": count, "live_references": count + 2, "phases": [],
                "cleanup": "not_created", "clock": "real fresh then synthetic application plus two days",
                "scope": "native Task.run; real RustFS; synthetic metadata; no worker or natural grace wait",
                "timing": "one sample per phase; overlapping forwarding metrics are not additive; SQL fetch may be excluded"}
    started = perf_counter()
    repo = fixture = None
    created = False
    try:
        _guard(request, settings)
        # Dynamic acquisition ensures the owned PG guard precedes any fixture operation.
        fixture = request.getfixturevalue("object_store")
        observed.update(_container(fixture.client))
        repo = ObjectRepository(fixture.client, BUCKET_PREFIX + uuid4().hex,
                                fixture.ring, fixture.reference_cipher)
        _owned(repo, fixture)
        repo.client.create_bucket(Bucket=repo.bucket)
        created = True
        observed["cleanup"] = "pending"
        pins, orphans = _seed(repo, request, settings, count)
        monkeypatch.setattr(rights_object_content, "repository", lambda: repo)
        settings.RIGHTS_OBJECT_STORAGE_ENABLED = True
        settings.RECOVERY_MODE = False
        queries = {model._meta.label: model.objects.all()
                   for model in apps.get_models(include_auto_created=True)}
        baseline, media = _snapshot(queries), _media(settings.MEDIA_ROOT)
        observed.update(row_state_sha256=baseline["sha256"], media=media,
                        bucket_initial_count=len(_inventory(repo)))
        assert observed["bucket_initial_count"] == 2 * count + 4
        _phase(repo, fixture, pins, orphans, baseline, queries, media, settings,
               observed, monkeypatch, "fresh", 0)
        future = timezone.now() + timedelta(days=2)
        _phase(repo, fixture, pins, orphans, baseline, queries, media, settings,
               observed, monkeypatch, "aged_interrupted" if fault else "aged",
               1 if fault else count, future, fault)
        if fault:
            _phase(repo, fixture, pins, orphans, baseline, queries, media, settings,
                   observed, monkeypatch, "aged_recovery", 1, future)
        _phase(repo, fixture, pins, orphans, baseline, queries, media, settings,
               observed, monkeypatch, "aged_replay", 0, future)
        observed["bucket_final_count"] = len(_inventory(repo))
        assert observed["bucket_final_count"] == count + 4
        observed["status"] = "passed"
    finally:
        error = sys.exc_info()[0]
        if error is not None:
            observed.update(status="failed", failure_class=error.__name__)
        try:
            if created:
                _cleanup(repo, fixture)
                observed["cleanup"] = "owned_bucket_absent_404"
        except Exception as error:
            observed.update(status="failed", cleanup="failed",
                            cleanup_failure_class=type(error).__name__)
            raise
        finally:
            observed["case_seconds"] = perf_counter() - started
            observed["measured_seconds"] = sum(p.get("wall_seconds", 0)
                                                for p in observed["phases"])
            observed["outside_task_seconds"] = observed["case_seconds"] - observed["measured_seconds"]
            record_property("owned_orphan_object_profile",
                            json.dumps(observed, sort_keys=True, allow_nan=False))
