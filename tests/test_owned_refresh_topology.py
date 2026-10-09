"""Wiring check of the owned MOD05 worker/Beat topology used by capacity experiments.

No load. Explicit opt-in only: starts an owned Celery worker and Beat with the deployed
commands against this synthetic test database and an empty owned Redis database, lets Beat
refresh one dirty mark, and verifies observation and cleanup.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from django.db import connection
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

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.skipif(not os.getenv("OWNED_REFRESH_TOPOLOGY_OUTPUT"), reason="Explicit owned wiring check only")
def test_owned_worker_beat_refresh_wiring(request, tmp_path):
    request.getfixturevalue("directory")
    db = connection.settings_dict
    assert db["NAME"].startswith("test_promotion_gate_")
    out = Path(os.environ["OWNED_REFRESH_TOPOLOGY_OUTPUT"])
    publication_state.refresh_all()
    listing = Listing.objects.filter(status="published").first()
    # bulk_create sends no model signal: nothing is enqueued from this test process.
    Revision.objects.bulk_create([Revision(listing=listing, manager_version=listing.person.manager_version)])
    assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) == {listing.pk}
    broker = owned_redis()
    assert broker.dbsize() == 0
    generation = "t" + uuid4().hex[:31]
    (tmp_path / "load_runtime_settings.py").write_text("from config.settings import *\n" + OBSERVER_SETTINGS)
    events = out / "celery-events-raw"
    events.mkdir(parents=True)
    env = {**os.environ, "POSTGRES_DB": db["NAME"], "DJANGO_SETTINGS_MODULE": "load_runtime_settings",
           "PYTHONPATH": str(tmp_path) + os.pathsep + str(Path.cwd()), "REDIS_URL": OWNED_REDIS,
           "TASK_QUEUE_GENERATION": generation, "WEB_MODELOS_CELERY_OBSERVER_DIR": str(events)}
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
        # Beat's 30 s interval: first refresh is due ~30 s after start.
        while PublicationDirty.objects.exists():
            assert time.monotonic() < ready + 45, "Beat/worker did not refresh the mark"
            time.sleep(.5)
        report["cleared_after_ready_seconds"] = time.monotonic() - ready
        while not any("refresh_publication_state" in p.read_text() for p in events.glob("*.jsonl")):
            assert time.monotonic() < ready + 50, "Observer record missing"
            time.sleep(.2)
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
        (out / "wiring.json").write_text(json.dumps(report, indent=2))
    refresh = [r for r in report["observer"]
               if r["event"] == "execution" and r["task"].endswith("refresh_publication_state")]
    assert refresh and refresh[0]["cleared"] == 1 and refresh[0]["mark_to_clear_seconds"]
    published = {r["id"]: r["role"] for r in report["observer"] if r["event"] == "publish"}
    assert published[refresh[0]["id"]] == "beat" and refresh[0]["role"] == "worker"
    assert all(report["pid_absence"].values()) and report["owned_redis_empty"]
