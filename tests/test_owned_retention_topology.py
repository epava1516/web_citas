"""Explicit owned retention task registration and unchanged Beat dispatch.

No load or external storage; synthetic listing expiry provides one real effect.
"""

import json
import os
import subprocess
import sys
import time
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_worker_capacity_comparison import (
    OBSERVER_SETTINGS,
    OWNED_REDIS,
    owned_redis,
    process_tree,
    terminate_owned,
    wait_for_log,
)

from apps.listings.models import LifecycleAction, Listing

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_retention_worker_beat_wiring(request, tmp_path, record_property):
    if not any(str(x).split("::")[0] == "tests/test_owned_retention_topology.py" for x in request.config.args):
        pytest.skip("Explicit owned retention topology only")
    request.getfixturevalue("directory")
    db = connection.settings_dict
    assert db["NAME"].startswith("test_promotion_gate_")
    out = Path(request.config.getoption("--gate-timings-output")).parent
    listing = Listing.objects.filter(status="published").first()
    assert listing is not None
    Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now() - timedelta(days=1))
    broker = owned_redis()
    assert broker.dbsize() == 0
    generation = "t" + uuid4().hex[:31]
    (tmp_path / "load_runtime_settings.py").write_text("from config.settings import *\n"
        + "MEDIA_ROOT = " + repr(str(django_settings.MEDIA_ROOT)) + "\n"
        + "RIGHTS_DELIVERY_ROOT = " + repr(str(tmp_path / "delivery")) + "\n"
        + OBSERVER_SETTINGS)
    events = out / "celery-events-raw"
    events.mkdir(parents=True)
    env = {**os.environ, "POSTGRES_DB": db["NAME"], "DJANGO_SETTINGS_MODULE": "load_runtime_settings",
           "PYTHONPATH": str(tmp_path) + os.pathsep + str(Path.cwd()), "REDIS_URL": OWNED_REDIS,
           "TASK_QUEUE_GENERATION": generation, "WEB_MODELOS_CELERY_OBSERVER_DIR": str(events)}
    manifest_path = out / "retention-effective-settings.json"
    manifest_code = """import django,json; django.setup()
from django.conf import settings
from config.celery import app
app.loader.import_default_modules()
rows={k:v for k,v in settings.CELERY_BEAT_SCHEDULE.items() if any(word in v['task'] for word in ('purge','retention','cleanup','erase','expire','orphan'))}
assert not app.conf.task_always_eager and not settings.RECOVERY_MODE
assert not settings.RIGHTS_OBJECT_STORAGE_ENABLED
assert settings.SAFETY_NOTICE_BACKEND == "disabled"
assert settings.MEDIA_ROOT != settings.BASE_DIR / "media/private"
assert str(settings.RIGHTS_DELIVERY_ROOT).startswith(str(__import__("pathlib").Path(__import__("os").environ["PYTHONPATH"].split(__import__("os").pathsep)[0])))
assert all(v['task'] in app.tasks for v in rows.values())
from pathlib import Path
Path(__import__('sys').argv[1]).write_text(json.dumps({'schedule':rows,'registered':sorted(v['task'] for v in rows.values()),'eager':app.conf.task_always_eager},indent=2))
"""
    subprocess.run([sys.executable, "-c", manifest_code, str(manifest_path)], env=env, check=True, timeout=30)
    manifest = json.loads(manifest_path.read_text())
    expected = {v["task"] for v in manifest["schedule"].values() if v["schedule"] <= 60}
    assert len(manifest["registered"]) == 18 and len(expected) == 17
    commands = {
        "worker": [sys.executable, "-m", "celery", "-A", "config", "worker", "--loglevel=INFO", "--concurrency=2"],
        "beat": [sys.executable, "-m", "celery", "-A", "config", "beat", "--loglevel=INFO",
                 "--schedule", str(tmp_path / "celerybeat-schedule")],
    }
    processes, report = {}, {"generation": generation}
    try:
        for role, command in commands.items():
            with (out / f"celery-{role}.log").open("w") as log:
                processes[role] = subprocess.Popen(command, env={**env, "WEB_MODELOS_PROCESS_ROLE": role}, stdout=log, stderr=log, start_new_session=True)
        deadline = time.monotonic() + 60
        wait_for_log(out / "celery-worker.log", " ready.", processes["worker"], deadline)
        wait_for_log(out / "celery-beat.log", "beat: Starting", processes["beat"], deadline)
        report["pids"] = {role: process_tree(p.pid) for role, p in processes.items()}
        ready = time.monotonic()
        while True:
            records = [json.loads(line) for p in events.glob("*.jsonl") for line in p.read_text().splitlines()]
            published = {r["id"]: r for r in records if r["event"] == "publish" and r["role"] == "beat"}
            completed = {r["task"] for r in records if r["event"] == "execution"
                         and r["task"] in expected and r["id"] in published
                         and r["role"] == "worker" and r["state"] == "SUCCESS" and not r["eager"]}
            if completed == expected:
                break
            assert all(p.poll() is None for p in processes.values()), "Owned worker/Beat exited"
            assert time.monotonic() < ready + 100, "Missing scheduled tasks: " + str(sorted(expected-completed))
            time.sleep(.5)
        listing.refresh_from_db()
        assert listing.status == "expired"
        assert LifecycleAction.objects.filter(listing=listing, operation="expire", actor__isnull=True).count() == 1
        report["scheduled_success"] = sorted(completed)
        report["registered"] = manifest["registered"]
        report["not_observed_hourly"] = sorted(set(manifest["registered"])-expected)
    finally:
        for owned in processes.values():
            terminate_owned(owned)
        report["pid_absence"] = {str(pid): not Path(f"/proc/{pid}").exists()
                                 for pids in report.get("pids", {}).values() for pid in pids}
        keys = list(broker.scan_iter(count=1000))
        report["owned_redis_keys_removed"] = len(keys)
        if keys:
            broker.delete(*keys)
        report["owned_redis_empty"] = broker.dbsize() == 0
        report["observer"] = [json.loads(line) for p in events.glob("*.jsonl") for line in p.read_text().splitlines()]
        (out / "retention-wiring.json").write_text(json.dumps(report, indent=2))
    assert all(report["pid_absence"].values()) and report["owned_redis_empty"]
    record_property("retention_wiring", json.dumps(report))
    record_property("limits", "17 scheduled tasks observed at unchanged intervals <=60s; 18 registered. Hourly orphan task not observed. Functional effects proven only for synthetic listing expiry; no object provider or full retention acceptance.")
