"""Finite real queued revision-start baseline; no eager/queue speedup claim."""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit

import pytest
import redis
from capacity_runtime_role import _owned_database, runtime_role_environment
from celery.signals import before_task_publish
from django.db import connection
from django.test import Client, override_settings
from test_listing_start_cost_baseline import sql_stage
from test_revised_listings import (
    pending,  # noqa: F401
    photo_environment,  # noqa: F401
    prepared,  # noqa: F401
    published,  # noqa: F401
    scenario,  # noqa: F401
)
from test_revised_listings import (
    test_rejection_preserves_public_version_and_rate_ids_are_isolated as _rejection_oracle,
)
from test_revised_listings import (
    test_revised_version_keeps_approved_snapshot_and_reuses_bytes as _approved_oracle,
)
from test_worker_capacity_comparison import process_tree, terminate_owned, wait_for_log

from apps.listings.models import PublicationDirty
from apps.mediafiles.models import Photo
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)
TASKS = {"apps.mediafiles.tasks.process_blob", "apps.listings.tasks.refresh_publication_state"}
REFRESH = "apps.listings.tasks.refresh_publication_state"


def read_events(folder):
    rows = []
    for path in folder.glob("*.jsonl"):
        assert path.stat().st_size <= 2 * 1024 * 1024
        for line in path.read_bytes().splitlines(keepends=True):
            if line.endswith(b"\n"):
                rows.append(json.loads(line))
    return rows


def identity_gone(pid, ticks):
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except FileNotFoundError:
        return True
    return int(stat.rsplit(")", 1)[1].split()[19]) != ticks


@pytest.mark.parametrize("case", ["approved", "rejected_correction"])
def test_listing_start_real_queue_baseline(request, settings, tmp_path, monkeypatch,
                                          record_property, case):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit serial owned queue diagnostic only; not a default functional gate")
    assert not os.environ.get("PYTEST_XDIST_WORKER"), "Queued diagnostic requires serial execution"
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
    foreign = {key: hashlib.sha256(broker.dump(key)).hexdigest()
               for key in broker.scan_iter() if broker.exists(key)}
    fixture = request.getfixturevalue("published")  # Original eager preparation only.
    out = Path(request.config.getoption("--gate-timings-output")).parent
    events = out / ("n06b-events-" + case)
    events.mkdir()
    base_module = "n06b_worker_settings"
    (tmp_path / (base_module + ".py")).write_text(
        "from local_ci_settings import *\n"
        + f"MEDIA_ROOT = Path({str(settings.MEDIA_ROOT)!r})\n"
        + f"RIGHTS_DELIVERY_ROOT = Path({str(tmp_path / 'delivery')!r})\n"
        + "CELERY_TASK_ALWAYS_EAGER = False\nCELERY_TASK_EAGER_PROPAGATES = False\n"
        + "import scripts.benchmark_celery_observer\n"
    )
    monkeypatch.setenv("PYTHONPATH", str(tmp_path) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    publishes, samples = [], []
    process = None
    identities = {}
    report = {"case": case, "scope": "Owned PostgreSQL/Redis, prefork2 restricted runtime worker; Client request and asynchronous readiness separate. No Beat/TCP/load/provider or causal code speedup claim."}

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
                       for r in executions.values())
            if starts <= executions.keys():
                return executions
            assert time.monotonic() < deadline, "Owned queue observation deadline exceeded"
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
                or not re.fullmatch(r"/(es|en)/person/[a-f0-9-]+/listing/start/", path)):
            return original(client, **http_request)
        prepare_current_state()  # Outside both request and readiness clocks.
        first_publish = len(publishes)
        stages = defaultdict(lambda: {"sql_queries": 0, "sql_execute_seconds": 0.0})

        def observe(execute, sql, params, many, context):
            stage = stages[sql_stage()]
            stage["sql_queries"] += 1
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                stage["sql_execute_seconds"] += time.perf_counter() - started

        started = time.perf_counter()
        with connection.execute_wrapper(observe):
            response = original(client, **http_request)
        request_seconds = time.perf_counter() - started
        request_end = time.monotonic()
        targets = publishes[first_publish:]
        assert response.status_code == 302 and targets
        assert {r["task"] for r in targets} == TASKS
        executions = drain()  # Explicit harness wait after server request clock stopped.
        revision_id = response.url.split("/")[3]
        photos = Photo.objects.filter(revision_id=revision_id, removed_at__isnull=True)
        assert photos.exists() and not photos.filter(comparison_complete=False).exists()
        assert not photos.exclude(blob__status="ready").exists()
        ready = time.monotonic()
        ledger = []
        for pub in targets:
            event = executions[pub["id"]]
            assert event["role"] == "worker" and event["start_monotonic"] >= pub["monotonic"]
            assert event["pid"] in identities and event["pid"] != process.pid
            ledger.append({"task": pub["task"], "task_id": pub["id"],
                           "publish_monotonic": pub["monotonic"],
                           "worker_start_monotonic": event["start_monotonic"],
                           "worker_end_monotonic": event["end_monotonic"], "worker_pid": event["pid"], "publish_to_start_seconds": event["start_monotonic"] - pub["monotonic"],
                           "worker_wall_seconds": event["wall"], "eager": event["eager"],
                           "state": event["state"]})
        assert not {"photo_task_eager", "state_task_eager"} & stages.keys()
        samples.append({"case": case, "ordinal": len(samples) + 1, "status": 302,
                        "task_always_eager": False, "request_seconds_instrumented": request_seconds,
                        "after_request_ready_seconds": ready - request_end,
                        "sql_queries": sum(s["sql_queries"] for s in stages.values()),
                        "stages": dict(stages), "task_ledger": ledger,
                        "dirty_after_ready": PublicationDirty.objects.count(),
                        "active_photo_count": photos.count()})
        return response

    before_task_publish.connect(published_task, weak=False)
    try:
        with override_settings(CELERY_TASK_ALWAYS_EAGER=False):
            assert celery_app.conf.task_always_eager is False
            with runtime_role_environment(base_module) as runtime:
                role = runtime["POSTGRES_USER"]
                private_path = Path(runtime["RIGHTS_EVIDENCE_RUNTIME_CONFIG"])
                env = {**os.environ, **runtime, "POSTGRES_DB": connection.settings_dict["NAME"],
                       "WEB_MODELOS_CELERY_OBSERVER_DIR": str(events), "WEB_MODELOS_PROCESS_ROLE": "worker"}
                try:
                    log = out / ("n06b-worker-" + case + ".log")
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
                        (_approved_oracle if case == "approved" else _rejection_oracle)(fixture)
                    assert len(samples) == (1 if case == "approved" else 2)
                    prepare_current_state()
                    report["samples"] = samples
                finally:
                    terminate_owned(process)
                    deadline = time.monotonic() + 5
                    while True:
                        absent = {str(pid): identity_gone(pid, ticks)
                                  for pid, ticks in identities.items()}
                        if all(absent.values()) or time.monotonic() >= deadline:
                            break
                        time.sleep(.05)
                    report.update(processes_absent=absent, worker_root_exited=process is None or process.poll() is not None,
                                  worker_exit_code=None if process is None else process.returncode)
                    assert all(absent.values()) and report["worker_root_exited"]
                    if "samples" in report:
                        assert report["worker_exit_code"] == 0, "Owned worker did not stop normally"
            with connection.cursor() as cursor:
                cursor.execute("SELECT NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=%s)", [role])
                report["runtime_role_removed"] = cursor.fetchone()[0]
            report["private_credentials_removed"] = not private_path.exists()
            assert report["runtime_role_removed"] and report["private_credentials_removed"]
    finally:
        before_task_publish.disconnect(published_task)
        remaining = set(broker.scan_iter())
        report["foreign_keys_preserved"] = all(hashlib.sha256(broker.dump(key)).hexdigest() == digest
                                               for key, digest in foreign.items() if key in remaining)
        report["unexpected_unscoped_keys"] = len([k for k in remaining - foreign.keys() if not k.startswith(prefix)])
        (out / ("n06b-publishes-" + case + ".json")).write_text(json.dumps(publishes, indent=2) + "\n")
        (out / ("n06b-runtime-" + case + ".json")).write_text(json.dumps(report, indent=2) + "\n")
    assert report["foreign_keys_preserved"] and report["unexpected_unscoped_keys"] == 0
    record_property("n06b_queued_baseline", json.dumps(report, sort_keys=True))
