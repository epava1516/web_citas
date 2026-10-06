import json
import os
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from django.db import connection

from config.celery import RecoveryAwareTask, app

pytestmark = pytest.mark.django_db(transaction=True)


def wait_for(predicate, timeout=25):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("Worker observation timed out")


def test_actual_worker_ignores_recovery_and_executes_normal_probe(tmp_path):
    app.autodiscover_tasks(force=True)
    business = [task for name, task in app.tasks.items() if name.startswith("apps.")]
    assert business and all(isinstance(task, RecoveryAwareTask) for task in business)
    database = connection.settings_dict
    assert database["NAME"].startswith("test_")
    results = []
    for mode in ["1", "0"]:
        directory = tmp_path / ("worker-" + mode)
        directory.mkdir(mode=0o700)
        marker, log = directory / "executed.json", directory / "worker.log"
        queue = "recovery_gate_" + uuid4().hex[:12]
        task_id = str(uuid4())
        environment = os.environ.copy()
        environment.update(
            RECOVERY_MODE=mode,
            RECOVERY_PROBE_MARKER=str(marker),
            POSTGRES_DB=database["NAME"],
            POSTGRES_USER=database["USER"],
            POSTGRES_PASSWORD=database["PASSWORD"],
            DB_HOST=database["HOST"],
            DB_PORT=str(database["PORT"]),
        )
        with log.open("w") as output:
            process = subprocess.Popen(
                [sys.executable, "-m", "scripts.probe_recovery_task_gate", "--queue", queue],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                stdout=output,
                stderr=subprocess.STDOUT,
            )
        try:
            wait_for(lambda: " ready." in log.read_text() or process.poll() is not None)
            assert process.poll() is None, log.read_text()[-1000:]
            app.send_task("recovery_gate.synthetic_database_probe", queue=queue, task_id=task_id)
            if mode == "1":
                wait_for(
                    lambda: task_id in log.read_text() and "ignored" in log.read_text().lower()
                )
                assert not marker.exists()
                results.append({"mode": "recovery", "ignored": True, "task_id": task_id})
            else:
                wait_for(marker.exists)
                data = json.loads(marker.read_text())
                assert data["synthetic_probe_executed"] and data["postgres_pid"] > 0
                results.append(
                    {
                        "mode": "normal",
                        "executed": True,
                        "postgres_pid": data["postgres_pid"],
                        "task_id": task_id,
                    }
                )
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            assert process.poll() is not None
            with app.connection_for_write() as broker:
                broker.default_channel.queue_delete(queue)
    (tmp_path / "worker-gate-result.json").write_text(
        json.dumps(
            {
                "real_worker": True,
                "results": results,
                "workers_stopped": True,
                "isolated_queues_deleted": True,
                "business_tasks_guarded": len(business),
            }
        )
    )


@pytest.fixture
def beat_probe_queue():
    queue = "recovery_gate_" + uuid4().hex[:12]
    try:
        yield queue
    finally:
        # Runs even when schedule assertions fail; never delete business queues.
        with app.connection_for_write() as broker:
            broker.default_channel.queue_delete(queue)


def test_actual_beat_removes_prior_schedule_during_recovery(tmp_path, beat_probe_queue):
    import shelve

    database = connection.settings_dict
    assert database["NAME"].startswith("test_")
    directory = tmp_path / "beat"
    directory.mkdir(mode=0o700)
    queue = beat_probe_queue
    schedule = directory / "beat-state"
    with app.connection_for_write() as broker:
        broker.default_channel.queue_declare(queue)
    for mode in ["0", "1"]:
        log = directory / ("beat-" + mode + ".log")
        environment = os.environ.copy()
        environment.update(
            RECOVERY_MODE=mode,
            POSTGRES_DB=database["NAME"],
            DB_HOST=database["HOST"],
            DB_PORT=str(database["PORT"]),
            POSTGRES_USER=database["USER"],
            POSTGRES_PASSWORD=database["PASSWORD"],
            RECOVERY_PROBE_MARKER=str(directory / "never-executed.json"),
        )
        with log.open("w") as output:
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "scripts.probe_recovery_task_gate",
                    "--queue",
                    queue,
                    "--beat",
                    "--schedule",
                    str(schedule),
                ],
                cwd=Path(__file__).resolve().parents[1],
                env=environment,
                stdout=output,
                stderr=subprocess.STDOUT,
            )
        try:
            wait_for(lambda: "beat: Starting" in log.read_text() or process.poll() is not None)
            assert process.poll() is None, log.read_text()[-1000:]
            if mode == "0":
                wait_for(lambda: "Sending due task synthetic-probe" in log.read_text())
                with app.connection_for_write() as broker:

                    def published():
                        message = broker.default_channel.basic_get(queue)
                        if message:
                            assert (
                                message.headers["task"] == "recovery_gate.synthetic_database_probe"
                            )
                            message.ack()
                            return True
                        return False

                    wait_for(published)
            else:
                assert '"effective_tasks": []' in log.read_text()
                time.sleep(1.5)
                assert "Sending due task" not in log.read_text()
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            assert process.poll() is not None
        with shelve.open(str(schedule), flag="r") as state:
            entries = state["entries"]
            assert ("synthetic-probe" in entries) if mode == "0" else (not entries)
        with app.connection_for_write() as broker:
            while message := broker.default_channel.basic_get(queue):
                message.ack()
    assert not (directory / "never-executed.json").exists()
    with app.connection_for_write() as broker:
        broker.default_channel.queue_delete(queue)
    (tmp_path / "beat-gate-result.json").write_text(
        json.dumps(
            {
                "real_beat": True,
                "normal_dispatch_observed": True,
                "recovery_effective_schedule_empty": True,
                "old_persisted_entries_removed": True,
                "processes_stopped": True,
                "isolated_queue_deleted": True,
            }
        )
    )
