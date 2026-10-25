"""Explicit real queued upload reference, reusing the complete original oracle."""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import redis
from capacity_runtime_role import _owned_database, runtime_role_environment
from celery.signals import before_task_publish
from django.db import connection
from django.test import Client, override_settings
from test_listing_start_queued_baseline import REFRESH, TASKS, identity_gone, read_events
from test_photos import photo_environment, scenario  # noqa: F401
from test_photos import (
    test_valid_photo_private_derivative_retries_exif_and_remove as upload_oracle,
)
from test_worker_capacity_comparison import process_tree, terminate_owned, wait_for_log

from apps.listings.models import PublicationDirty
from apps.mediafiles.models import Photo
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)
MEDIA = "apps.mediafiles.tasks.process_blob"


def test_photo_upload_real_queue_reference(request, settings, tmp_path, monkeypatch, record_property):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned serial media queue reference only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert request.config.pluginmanager.hasplugin("scripts.local_ci_broker")
    generation = request.getfixturevalue("isolated_test_broker")
    run = os.environ["LOCAL_CI_ISOLATED_BROKER_RUN"]
    assert re.fullmatch(r"\d{8}-\d{6}-[a-f0-9]{8}", run)
    assert os.environ["LOCAL_CI_POSTGRES_CONTAINER"] == "web-modelos-ci-pg-" + run
    assert generation == os.environ["LOCAL_CI_TEST_QUEUE_GENERATION"] == settings.TASK_QUEUE_GENERATION
    _owned_database()
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    endpoint = urlsplit(settings.CELERY_BROKER_URL)
    assert endpoint.hostname == "127.0.0.1" and endpoint.path == "/0"
    broker = redis.Redis.from_url(settings.CELERY_BROKER_URL)
    prefix = f"clasificados:{generation}:".encode()
    assert not list(broker.scan_iter(match=prefix + b"*"))
    foreign = {k: hashlib.sha256(broker.dump(k)).hexdigest()
               for k in broker.scan_iter() if broker.exists(k)}
    request.getfixturevalue("photo_environment")
    request.getfixturevalue("scenario")  # Native preparation, before worker/request clocks.
    out = Path(request.config.getoption("--gate-timings-output")).parent
    events = out / "n03a-events"
    events.mkdir()
    module = "n03a_worker_settings"
    (tmp_path / (module + ".py")).write_text(
        "from local_ci_settings import *\n"
        + f"MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n"
        + f"RIGHTS_DELIVERY_ROOT = Path({str(tmp_path / 'delivery')!r})\n"
        + "CELERY_TASK_ALWAYS_EAGER = False\nCELERY_TASK_EAGER_PROPAGATES = False\n"
        + "import scripts.benchmark_celery_observer\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    publishes, samples, identities = [], [], {}
    process = None
    report = {"scope": "Original JPEG upload and exact retry with own PG/Redis/prefork2 restricted worker; Client backend phase, task execution and readiness observation separate. No TCP/Beat/load/provider or upload transport latency claim."}

    def published_task(sender=None, headers=None, **kwargs):
        publishes.append({"task": sender, "id": (headers or {}).get("id"),
                          "monotonic": time.monotonic()})

    def drain():
        deadline = time.monotonic() + 45
        while True:
            assert process.poll() is None, "Owned worker exited"
            rows = read_events(events)
            starts = {r["id"] for r in publishes}
            starts.update(r["id"] for r in rows if r["event"] == "publish")
            executions = {r["id"]: r for r in rows if r["event"] == "execution"}
            assert all(r["task"] in TASKS for r in publishes)
            assert all(r["state"] == "SUCCESS" and r["eager"] is False
                       and "snapshot_error" not in r for r in executions.values())
            if starts <= executions.keys():
                return executions
            assert time.monotonic() < deadline, "Owned queue observation expired"
            time.sleep(.05)

    def prepare_current_state():
        drain()
        celery_app.send_task(REFRESH)
        drain()
        assert not PublicationDirty.objects.exists()

    original = Client.request

    def measured(client, **http_request):
        path = http_request.get("PATH_INFO", "")
        if (http_request.get("REQUEST_METHOD") != "POST"
                or not re.fullmatch(r"/(es|en)/draft/[a-f0-9-]+/photos/upload/", path)):
            return original(client, **http_request)
        prepare_current_state()  # Explicit quiescent setup outside all measured intervals.
        first_publish = len(publishes)
        totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

        def observe(execute, sql, params, many, context):
            totals["sql_queries"] += 1
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                totals["sql_execute_seconds"] += time.perf_counter() - started

        entry = time.monotonic()
        cpu = time.thread_time()
        with connection.execute_wrapper(observe):
            response = original(client, **http_request)
        request_end = time.monotonic()
        used_cpu = time.thread_time() - cpu
        targets = publishes[first_publish:]
        media = [p for p in targets if p["task"] == MEDIA]
        assert response.status_code == 302
        assert len(media) == (1 if not samples else 0)
        executions = drain()
        photo = Photo.objects.select_related("blob").get()
        assert photo.blob.status == "ready" and photo.comparison_complete and not photo.approved
        observed = time.monotonic()
        ledger = []
        for pub in targets:
            event = executions[pub["id"]]
            assert event["role"] == "worker" and event["start_monotonic"] >= pub["monotonic"]
            assert event["pid"] in identities and event["pid"] != process.pid
            ledger.append({"task": pub["task"], "task_id": pub["id"],
                           "publish_monotonic": pub["monotonic"],
                           "worker_start_monotonic": event["start_monotonic"],
                           "worker_end_monotonic": event["end_monotonic"],
                           "worker_pid": event["pid"], "eager": event["eager"],
                           "state": event["state"],
                           "publish_to_start_seconds": event["start_monotonic"] - pub["monotonic"],
                           "worker_wall_seconds": event["wall"],
                           "worker_thread_cpu_seconds": event["thread_cpu"]})
        samples.append({"ordinal": len(samples) + 1, "status": 302,
                        "kind": "new_upload" if not samples else "exact_duplicate_retry",
                        "task_always_eager": False, "entry_monotonic": entry,
                        "request_end_monotonic": request_end, "ready_observed_monotonic": observed,
                        "request_seconds": request_end - entry, "request_thread_cpu_seconds": used_cpu,
                        "after_request_ready_observed_seconds": observed - request_end,
                        "entry_to_ready_observed_seconds": observed - entry,
                        "media_task_count": len(media), "ledger": ledger, **totals})
        return response

    before_task_publish.connect(published_task, weak=False)
    try:
        with override_settings(CELERY_TASK_ALWAYS_EAGER=False):
            assert celery_app.conf.task_always_eager is False
            with runtime_role_environment(module) as runtime:
                role = runtime["POSTGRES_USER"]
                private_path = Path(runtime["RIGHTS_EVIDENCE_RUNTIME_CONFIG"])
                env = {**os.environ, **runtime, "POSTGRES_DB": connection.settings_dict["NAME"],
                       "WEB_MODELOS_CELERY_OBSERVER_DIR": str(events), "WEB_MODELOS_PROCESS_ROLE": "worker"}
                try:
                    log = out / "n03a-worker.log"
                    with log.open("w") as stream:
                        process = subprocess.Popen(
                            [sys.executable, "-m", "celery", "-A", "config", "worker", "--loglevel=INFO", "--concurrency=2"],
                            env=env, stdout=stream, stderr=stream, start_new_session=True)
                    wait_for_log(log, " ready.", process, time.monotonic() + 60)
                    for pid in process_tree(process.pid):
                        identities[pid] = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])
                    assert len(identities) >= 3
                    report["pid_start_ticks"] = identities
                    with monkeypatch.context() as patch:
                        patch.setattr(Client, "request", measured)
                        upload_oracle(request, None)
                    assert len(samples) == 2
                    prepare_current_state()
                    report["samples"] = samples
                finally:
                    terminate_owned(process)
                    deadline = time.monotonic() + 5
                    while True:
                        absent = {str(pid): identity_gone(pid, ticks) for pid, ticks in identities.items()}
                        if all(absent.values()) or time.monotonic() >= deadline:
                            break
                        time.sleep(.05)
                    report.update(processes_absent=absent, worker_root_exited=process is None or process.poll() is not None,
                                  worker_exit_code=None if process is None else process.returncode)
                    assert all(absent.values()) and report["worker_root_exited"]
                    if "samples" in report:
                        assert report["worker_exit_code"] == 0
            with connection.cursor() as cursor:
                cursor.execute("SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)", [role])
                report["runtime_role_removed"] = cursor.fetchone()[0]
            report["private_credentials_removed"] = not private_path.exists()
            assert report["runtime_role_removed"] and report["private_credentials_removed"]
    finally:
        before_task_publish.disconnect(published_task)
        remaining = set(broker.scan_iter())
        report["foreign_keys_preserved"] = set(foreign) <= remaining and all(
            hashlib.sha256(broker.dump(k)).hexdigest() == digest for k, digest in foreign.items()
        )
        report["unexpected_unscoped_keys"] = len([k for k in remaining - foreign.keys() if not k.startswith(prefix)])
        (out / "n03a-publishes.json").write_text(json.dumps(publishes, indent=2) + "\n")
        (out / "n03a-runtime.json").write_text(json.dumps(report, indent=2) + "\n")
    assert report["foreign_keys_preserved"] and report["unexpected_unscoped_keys"] == 0
    record_property("n03a_upload_queued_reference", json.dumps(report, sort_keys=True))
