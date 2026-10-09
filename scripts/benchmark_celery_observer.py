"""Celery task observer for owned synthetic capacity experiments only.

Imported by the owned runtime settings when WEB_MODELOS_CELERY_OBSERVER_DIR is set, so the
web, worker and Beat commands stay identical to the deployed ones. Writes one JSON line per
publish (role web/beat, task id) and per execution (wall/thread CPU, result and, for the
stored publication refresh, the dirty marks it cleared with an upper bound of their
mark-to-clear delay on the database clock). Eager executions inside the web process are
observed the same way. Never used by the normal runtime.
"""

import json
import os
import time
from pathlib import Path

from celery.signals import before_task_publish, task_postrun, task_prerun

OUTPUT = Path(os.environ["WEB_MODELOS_CELERY_OBSERVER_DIR"])
ROLE = os.environ.get("WEB_MODELOS_PROCESS_ROLE", "unknown")
REFRESH = "apps.listings.tasks.refresh_publication_state"
_running = {}


def _write(record):
    with (OUTPUT / f"celery-{ROLE}-{os.getpid()}.jsonl").open("a") as stream:
        stream.write(json.dumps(record, separators=(",", ":")) + "\n")


def _dirty_snapshot():
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT listing_id::text, generation, extract(epoch from marked_at) "
            "FROM listings_publicationdirty"
        )
        rows = cursor.fetchall()
        cursor.execute("SELECT extract(epoch from clock_timestamp())")
        now = float(cursor.fetchone()[0])
    return {(r[0], r[1]): float(r[2]) for r in rows}, now


@before_task_publish.connect(weak=False)
def _published(sender=None, headers=None, **kwargs):
    _write({"event": "publish", "task": sender, "id": (headers or {}).get("id"), "role": ROLE,
            "pid": os.getpid(), "monotonic": time.monotonic()})


@task_prerun.connect(weak=False)
def _prerun(task_id=None, task=None, **kwargs):
    entry = {"start_monotonic": time.monotonic(), "start_thread_cpu": time.thread_time()}
    if task is not None and task.name == REFRESH:
        try:
            entry["dirty_before"], entry["db_start_epoch"] = _dirty_snapshot()
        except Exception as exc:  # Observation must never change task behaviour.
            entry["snapshot_error"] = type(exc).__name__
    _running[task_id] = entry


@task_postrun.connect(weak=False)
def _postrun(task_id=None, task=None, retval=None, state=None, **kwargs):
    entry = _running.pop(task_id, None)
    if entry is None or task is None:
        return
    end = time.monotonic()
    record = {
        "event": "execution", "task": task.name, "id": task_id, "role": ROLE, "pid": os.getpid(),
        "eager": bool(getattr(task.request, "is_eager", False)), "state": state,
        "start_monotonic": entry["start_monotonic"], "end_monotonic": end,
        "wall": end - entry["start_monotonic"], "thread_cpu": time.thread_time() - entry["start_thread_cpu"],
        "result": retval if isinstance(retval, (int, float, bool)) or retval is None else "not_numeric",
    }
    if task.name == REFRESH and "dirty_before" in entry:
        try:
            after, db_end = _dirty_snapshot()
            cleared = [key for key in entry["dirty_before"] if key not in after]
            record.update(
                dirty_before=len(entry["dirty_before"]), dirty_after=len(after), cleared=len(cleared),
                db_wall=db_end - entry["db_start_epoch"],
                mark_to_clear_seconds=sorted(db_end - entry["dirty_before"][key] for key in cleared),
            )
        except Exception as exc:
            record["snapshot_error"] = type(exc).__name__
    elif "snapshot_error" in entry:
        record["snapshot_error"] = entry["snapshot_error"]
    _write(record)
