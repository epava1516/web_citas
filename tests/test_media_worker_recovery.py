"""Explicit serial, owned PG/Redis/prefork/Beat recovery evidence; no app patches."""

import hashlib
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import redis
from capacity_runtime_role import _owned_database, runtime_role_environment
from celery.signals import before_task_publish
from django.core.files.base import ContentFile
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from test_listing_start_queued_baseline import REFRESH, identity_gone, read_events
from test_photos import raw_image
from test_worker_capacity_comparison import process_tree, terminate_owned, wait_for_log

from apps.core.models import Person, User
from apps.listings.models import Listing, Revision
from apps.mediafiles.models import Blob, Photo
from apps.mediafiles.services import process as process_media
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)
MEDIA = "apps.mediafiles.tasks.process_blob"
RECOVER = "apps.mediafiles.tasks.recover_media_jobs"
ALLOWED = {MEDIA, RECOVER, REFRESH}


def test_media_worker_retry_and_real_beat_recovery(
    request, settings, tmp_path, monkeypatch, record_property
):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned serial real worker and Beat instrument only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert request.config.pluginmanager.hasplugin("scripts.local_ci_broker")
    generation = request.getfixturevalue("isolated_test_broker")
    run = os.environ["LOCAL_CI_ISOLATED_BROKER_RUN"]
    assert re.fullmatch(r"\d{8}-\d{6}-[a-f0-9]{8}", run)
    assert os.environ["LOCAL_CI_POSTGRES_CONTAINER"] == "web-modelos-ci-pg-" + run
    assert generation == os.environ["LOCAL_CI_TEST_QUEUE_GENERATION"] == settings.TASK_QUEUE_GENERATION
    _owned_database()  # Independently checks PG container labels, port, role and database.
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    endpoint = urlsplit(settings.CELERY_BROKER_URL)
    assert endpoint.hostname == "127.0.0.1" and endpoint.path == "/0" and endpoint.port
    entry = settings.CELERY_BEAT_SCHEDULE["recover-private-media"]
    assert entry["task"] == RECOVER and entry["schedule"] == 60.0
    broker = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    prefix = f"clasificados:{generation}:".encode()
    assert not list(broker.scan_iter(match=prefix + b"*"))
    foreign = {key: hashlib.sha256(broker.dump(key)).hexdigest()
               for key in broker.scan_iter() if broker.exists(key)}
    out = Path(request.config.getoption("--gate-timings-output")).parent
    events = out / "n03e-events"
    events.mkdir()
    work = tmp_path / "n03e-private-runtime"
    work.mkdir(mode=0o700)
    settings.MEDIA_ROOT = work / "media"
    module = "n03e_worker_settings"
    module_path = work / (module + ".py")
    module_path.write_text(
        "from local_ci_settings import *\nfrom pathlib import Path\n"
        + f"MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n"
        + f"RIGHTS_DELIVERY_ROOT = Path({str(work / 'delivery')!r})\n"
        + "CELERY_TASK_ALWAYS_EAGER = False\nCELERY_TASK_EAGER_PROPAGATES = False\n"
        + "CELERY_RESULT_EXPIRES = None\n"
        + "CELERY_BEAT_SCHEDULE = {'recover-private-media': dict(CELERY_BEAT_SCHEDULE['recover-private-media'])}\n"
        + "import scripts.benchmark_media_recovery_observer\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(work) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    worker = beat = None
    identities = {}
    publishes = []
    expected_failures = set()
    role = private_path = None
    report = {"scope": "Owned serial synthetic real worker retries and unchanged 60s media Beat cadence. No HTTP/TCP, capacity, provider or SLA claim.",
              "phases": {}, "fixture_manifest": {}, "schedule_seconds": 60.0, "complete": False,
              "measurement_note": "Task wall and thread CPU include observer SELECT current_user and signal bookkeeping. First tick is one observation, not an interval distribution. Retry scope is one Celery message, not a global attempt limit."}

    def capture(sender=None, headers=None, **kwargs):
        headers = headers or {}
        publishes.append({"event": "publish", "task": sender, "id": headers.get("id"),
                          "retries": headers.get("retries", 0), "role": "harness",
                          "monotonic": time.monotonic()})

    def rows():
        observed = read_events(events)
        assert len(observed) <= 2000
        assert not any("snapshot_error" in row for row in observed)
        assert all(row["task"] in ALLOWED for row in observed)
        return observed

    def track(child):
        for pid in process_tree(child.pid):
            try:
                ticks = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])
            except FileNotFoundError:
                continue
            if pid in identities:
                assert identities[pid] == ticks, "Owned PID was unexpectedly replaced"
            identities[pid] = ticks

    def wait_until(predicate, seconds, description):
        deadline = time.monotonic() + seconds
        while True:
            assert worker is not None and worker.poll() is None, "Owned worker exited"
            track(worker)
            if beat is not None and beat.poll() is None:
                track(beat)
            observed = rows()
            if predicate(observed):
                return observed
            assert time.monotonic() < deadline, description
            time.sleep(.05)

    def execution_rows(observed, task_id):
        return sorted([row for row in observed
                       if row["event"] == "execution" and row["id"] == task_id],
                      key=lambda row: row["retries"])

    def drain():
        def finished(observed):
            sent = publishes + [row for row in observed if row["event"] == "publish"]
            assert all(row["task"] in ALLOWED for row in sent)
            completed = [row for row in observed if row["event"] == "execution"]
            for row in completed:
                assert row["eager"] is False and row["sql_role"] == role
                assert row["pid"] in identities and row["pid"] != worker.pid
                assert row["state"] in ({"RETRY", "FAILURE"} if row["id"] in expected_failures else {"SUCCESS"})
            return {(row["id"], row["retries"]) for row in sent} <= {
                (row["id"], row["retries"]) for row in completed}
        return wait_until(finished, 45, "Owned queue drain expired")

    def send(blob):
        result = celery_app.send_task(MEDIA, args=[str(blob.pk)])
        return result.id

    def fixture_blob(seed, **values):
        raw = raw_image(seed)
        assert str(seed) not in report["fixture_manifest"]
        report["fixture_manifest"][str(seed)] = {
            "canonical_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_bytes": len(raw), "width": 640, "height": 480,
        }
        blob = Blob(sha256=hashlib.sha256(raw).hexdigest(), width=640, height=480, **values)
        blob.original.save(f"n03e-{seed}.jpg", ContentFile(raw), save=False)
        blob.save()
        return blob, raw

    def snapshot(blob):
        blob.refresh_from_db()
        return {"status": blob.status, "attempts": blob.attempts, "error_code": blob.error_code,
                "started_at": blob.started_at.isoformat() if blob.started_at else None}

    before_task_publish.connect(capture, weak=False)
    try:
        with override_settings(CELERY_TASK_ALWAYS_EAGER=False):
            assert celery_app.conf.task_always_eager is False
            with runtime_role_environment(module) as runtime:
                role = runtime["POSTGRES_USER"]
                report["runtime_role"] = role
                private_path = Path(runtime["RIGHTS_EVIDENCE_RUNTIME_CONFIG"])
                env = {**os.environ, **runtime, "POSTGRES_DB": connection.settings_dict["NAME"],
                       "WEB_MODELOS_CELERY_OBSERVER_DIR": str(events),
                       "WEB_MODELOS_PROCESS_ROLE": "worker"}
                try:
                    log = out / "n03e-worker.log"
                    with log.open("w") as stream:
                        worker = subprocess.Popen(
                            [sys.executable, "-m", "celery", "-A", "config", "worker", "--loglevel=INFO", "--concurrency=2"],
                            env=env, stdout=stream, stderr=stream, start_new_session=True)
                    report["worker_root_pid"] = worker.pid
                    track(worker)
                    wait_for_log(log, " ready.", worker, time.monotonic() + 60)
                    track(worker)
                    assert len(identities) >= 3
                    drain()
                    # A: physical absence, with no retry/backoff/clock/task patch.
                    exhausted, original_a = fixture_blob(7101)
                    original_path = Path(exhausted.original.path)
                    original_path.unlink()
                    a_id = send(exhausted)
                    expected_failures.add(a_id)
                    observed = wait_until(lambda data: any(
                        row["state"] == "FAILURE" for row in execution_rows(data, a_id)),
                        45, "Real storage autoretry sequence expired")
                    attempts = execution_rows(observed, a_id)
                    assert [row["retries"] for row in attempts] == [0, 1, 2, 3]
                    assert [row["state"] for row in attempts] == ["RETRY"] * 3 + ["FAILURE"]
                    retries = sorted([row for row in observed if row["event"] == "retry" and row["id"] == a_id],
                                     key=lambda row: row["retries"])
                    assert [row["retries"] for row in retries] == [0, 1, 2]
                    assert all(0 <= row["countdown"] <= limit for row, limit in zip(retries, [1, 2, 4]))
                    a_failures = [row for row in observed if row["event"] == "failure" and row["id"] == a_id]
                    assert len(a_failures) == 1 and a_failures[0]["exception_type"] == "FileNotFoundError"
                    assert a_failures[0]["retries"] == 3
                    assert all(row["exception_type"] == "FileNotFoundError" for row in retries)
                    assert snapshot(exhausted)["status"] == "failed" and exhausted.attempts == 4
                    assert exhausted.error_code == "decode_or_storage_failed"
                    original_path.write_bytes(original_a)
                    report["phases"]["storage_retry"] = {"task_id": a_id, "attempts": attempts, "retries": retries}
                    drain()
                    # B: supported Pillow decode but forbidden media format -> ValidationError,
                    # rather than UnidentifiedImageError, which is also an OSError.
                    failed, canonical = fixture_blob(7102)
                    gif = io.BytesIO()
                    Image.new("RGB", (24, 24), "blue").save(gif, format="GIF")
                    Path(failed.original.path).write_bytes(gif.getvalue())
                    b_id = send(failed)
                    expected_failures.add(b_id)
                    observed = wait_until(lambda data: bool(execution_rows(data, b_id)), 45,
                                          "Real validation failure expired")
                    b_attempts = execution_rows(observed, b_id)
                    assert len(b_attempts) == 1 and b_attempts[0]["state"] == "FAILURE"
                    assert b_attempts[0]["retries"] == 0
                    assert not [row for row in observed if row["event"] == "retry" and row["id"] == b_id]
                    b_failures = [row for row in observed if row["event"] == "failure" and row["id"] == b_id]
                    assert len(b_failures) == 1 and b_failures[0]["exception_type"] == "ValidationError"
                    assert b_failures[0]["retries"] == 0
                    assert snapshot(failed)["status"] == "failed" and failed.attempts == 1
                    assert failed.error_code == "decode_or_storage_failed"
                    Path(failed.original.path).write_bytes(canonical)
                    assert hashlib.sha256(Path(failed.original.path).read_bytes()).hexdigest() == failed.sha256
                    report["phases"]["validation_failure"] = {"task_id": b_id, "attempts": b_attempts}
                    drain()
                    # C: direct native service prepares only the declared ready fixture.
                    queued, _ = fixture_blob(7103)
                    stale, _ = fixture_blob(7104, status="processing", attempts=1,
                                            started_at=timezone.now() - timedelta(seconds=181))
                    ready, _ = fixture_blob(7105)
                    process_media(ready.pk)
                    ready.refresh_from_db()
                    assert ready.status == "ready" and ready.attempts == 1 and ready.signature
                    owner = User.objects.create_user(username="n03e-synthetic-owner")
                    person = Person.objects.create(individual=owner, subject=owner, alias="Synthetic")
                    revision = Revision.objects.create(listing=Listing.objects.create(person=person), manager_version=1)
                    photo = Photo.objects.create(blob=ready, revision=revision, position=0)
                    fresh, _ = fixture_blob(7106, status="processing", attempts=1, started_at=timezone.now())
                    terminal = [fixture_blob(7110 + index, status=status)[0]
                                for index, status in enumerate(["erasing", "erased", "purging", "purged"])]
                    drain()
                    # Align only this fixture's declared lease with Beat start, without patching time.
                    Blob.objects.filter(pk=fresh.pk).update(started_at=timezone.now())
                    controls = {"exhausted": exhausted, "fresh": fresh,
                                **{f"terminal_{index}": blob for index, blob in enumerate(terminal)}}
                    before = {name: snapshot(blob) for name, blob in controls.items()}
                    positives = {"queued": queued, "stale": stale, "failed": failed, "ready": ready}
                    media_before = {row["id"] for row in rows() if row["event"] == "publish" and row["task"] == MEDIA}
                    beat_started = time.monotonic()
                    beat_env = dict(env, WEB_MODELOS_PROCESS_ROLE="beat")
                    beat_log = out / "n03e-beat.log"
                    with beat_log.open("w") as stream:
                        beat = subprocess.Popen(
                            [sys.executable, "-m", "celery", "-A", "config", "beat", "--loglevel=INFO",
                             "--schedule", str(work / "beat-schedule")],
                            env=beat_env, stdout=stream, stderr=stream, start_new_session=True)
                    report["beat_root_pid"] = beat.pid
                    track(beat)

                    def recovered(data):
                        assert beat.poll() is None, "Owned Beat exited"
                        ticks = [row for row in data if row["event"] == "publish" and row["task"] == RECOVER]
                        assert len(ticks) <= 1, "Second production tick exceeded bounded protocol"
                        if not ticks:
                            return False
                        assert ticks[0]["role"] == "beat"
                        done = execution_rows(data, ticks[0]["id"])
                        if not done:
                            return False
                        assert len(done) == 1 and done[0]["state"] == "SUCCESS"
                        for blob in positives.values():
                            blob.refresh_from_db()
                        photo.refresh_from_db()
                        return all(blob.status == "ready" for blob in positives.values()) and photo.comparison_complete

                    observed = wait_until(recovered, 90, "Production media Beat tick or recovery expired")
                    ready_observed = time.monotonic()
                    terminate_owned(beat)  # Stop scheduling before draining worker publications.
                    observed = drain()
                    ticks = [row for row in observed if row["event"] == "publish" and row["task"] == RECOVER]
                    assert len(ticks) == 1
                    tick = ticks[0]
                    assert 0 <= tick["monotonic"] - beat_started <= 90
                    recovery = execution_rows(observed, tick["id"])
                    assert len(recovery) == 1 and recovery[0]["state"] == "SUCCESS"
                    assert recovery[0]["start_monotonic"] >= tick["monotonic"]
                    new_media = [row for row in observed if row["event"] == "publish" and row["task"] == MEDIA
                                 and row["id"] not in media_before]
                    assert len(new_media) == 4 and len({row["id"] for row in new_media}) == 4
                    assert all(row["role"] == "worker" and row["retries"] == 0 for row in new_media)
                    assert all(len(execution_rows(observed, row["id"])) == 1
                               and execution_rows(observed, row["id"])[0]["state"] == "SUCCESS" for row in new_media)
                    assert {name: snapshot(blob) for name, blob in controls.items()} == before
                    assert (timezone.now() - fresh.started_at).total_seconds() < 180
                    expected_attempts = {"queued": 1, "stale": 2, "failed": 2, "ready": 1}
                    assert all(snapshot(blob)["status"] == "ready" and blob.attempts == expected_attempts[name]
                               for name, blob in positives.items())
                    assert all(blob.signature and blob.derivative for blob in positives.values())
                    photo.refresh_from_db()
                    assert photo.comparison_complete and not photo.approved
                    report["phases"]["beat_recovery"] = {
                        "beat_start_monotonic": beat_started, "tick": tick,
                        "first_tick_observed_seconds": tick["monotonic"] - beat_started,
                        "recovery": recovery, "media_publishes": new_media,
                        "publish_to_recovery_start_seconds": recovery[0]["start_monotonic"] - tick["monotonic"],
                        "ready_observed_monotonic": ready_observed,
                        "tick_to_ready_observed_seconds": ready_observed - tick["monotonic"],
                        "positive_attempts": expected_attempts,
                        "positive_snapshots": {name: snapshot(blob) for name, blob in positives.items()},
                        "positive_distinct_blob_count": len({blob.pk for blob in positives.values()}),
                        "excluded_controls_before": before,
                        "excluded_controls_after": {name: snapshot(blob) for name, blob in controls.items()},
                        "excluded_controls_unchanged": True,
                        "fixture_note": "Native direct process before Beat prepares only ready blob; Photo then attached incomplete. No approval assertion."}
                    assert report["phases"]["beat_recovery"]["positive_distinct_blob_count"] == 4
                    report["complete"] = True
                finally:
                    # Never remove SQL credentials while worker/Beat can still use them.
                    cleanup_errors = []
                    for name, child in [("beat", beat), ("worker", worker)]:
                        try:
                            if name == "worker" and worker is not None and worker.poll() is None:
                                drain()
                        except Exception as exc:
                            cleanup_errors.append(type(exc).__name__)
                        try:
                            if child is not None:
                                track(child)
                            terminate_owned(child)
                        except Exception as exc:
                            cleanup_errors.append(type(exc).__name__)
                    report["cleanup_errors"] = cleanup_errors
                    report["pid_start_ticks"] = identities
                    deadline = time.monotonic() + 5
                    while True:
                        absent = {str(pid): identity_gone(pid, ticks) for pid, ticks in identities.items()}
                        if all(absent.values()) or time.monotonic() >= deadline:
                            break
                        time.sleep(.05)
                    report["processes_absent"] = absent
                    report["worker_exit_code"] = None if worker is None else worker.poll()
                    report["beat_exit_code"] = None if beat is None else beat.poll()
                    assert all(absent.values()) and not cleanup_errors
                    assert worker is None or worker.poll() is not None
                    assert beat is None or beat.poll() is not None
            if role:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)", [role])
                    report["runtime_role_removed"] = cursor.fetchone()[0]
                report["private_credentials_removed"] = not private_path.exists()
                assert report["runtime_role_removed"] and report["private_credentials_removed"]
    finally:
        before_task_publish.disconnect(capture)
        report["harness_publishes"] = list(publishes)
        report["namespace_generation"] = generation
        if role:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)", [role])
                    report["runtime_role_removed"] = cursor.fetchone()[0]
                report["private_credentials_removed"] = not private_path.exists()
            except Exception as exc:
                report["role_cleanup_snapshot_error"] = type(exc).__name__
        try:
            remaining = set(broker.scan_iter())
            report["foreign_keys_preserved"] = set(foreign) <= remaining and all(
                hashlib.sha256(broker.dump(key)).hexdigest() == digest for key, digest in foreign.items())
            report["unexpected_unscoped_keys"] = sum(not key.startswith(prefix) for key in remaining - foreign.keys())
            report["events"] = rows()
        except Exception as exc:
            report["final_snapshot_error"] = type(exc).__name__
        if all(identity_gone(pid, ticks) for pid, ticks in identities.items()):
            shutil.rmtree(work)
        report["private_runtime_removed"] = not work.exists()
        (out / "n03e-runtime.json").write_text(json.dumps(report, allow_nan=False, indent=2) + "\n")
        record_property("n03e_media_worker_recovery", json.dumps(report, allow_nan=False, sort_keys=True))
    assert report["complete"] and report["foreign_keys_preserved"]
    assert report["unexpected_unscoped_keys"] == 0 and "final_snapshot_error" not in report
    assert report["private_runtime_removed"] and report["worker_exit_code"] == 0
    assert report["beat_exit_code"] in (0, -15), "Beat required forced termination"
    # All quantitative event clocks/durations must be finite; no p95 or sums of overlap.
    for row in report["events"]:
        for field in ("monotonic", "wall_epoch", "start_monotonic", "end_monotonic", "wall", "thread_cpu", "countdown"):
            if field in row:
                assert isinstance(row[field], (int, float)) and math.isfinite(row[field]) and row[field] >= 0
