"""Opt-in signal ledger for the owned real media recovery experiment only.

Generated private child settings import this module; normal settings never do.
No task arguments, result bodies, exception messages or subject data are recorded.
"""

import json
import math
import os
import time
from pathlib import Path

from celery.signals import before_task_publish, task_failure, task_postrun, task_prerun, task_retry

OUTPUT = Path(os.environ["WEB_MODELOS_CELERY_OBSERVER_DIR"])
ROLE = os.environ["WEB_MODELOS_PROCESS_ROLE"]
_running = {}


def _write(record):
    record.update(role=ROLE, pid=os.getpid(), monotonic=time.monotonic(), wall_epoch=time.time())
    path = OUTPUT / f"media-{ROLE}-{os.getpid()}.jsonl"
    if path.exists() and path.stat().st_size >= 2 * 1024 * 1024:
        raise RuntimeError("ObserverFileBound")
    with path.open("a") as stream:
        stream.write(json.dumps(record, allow_nan=False, separators=(",", ":")) + "\n")


def _error(event, exc, task_id=None):
    # Signal handlers must not change task behavior. Missing or error rows fail
    # the harness; a taxonomy is sufficient and cannot expose exception text.
    try:
        _write({"event": event, "id": task_id, "snapshot_error": type(exc).__name__})
    except Exception:
        pass


@before_task_publish.connect(weak=False)
def _published(sender=None, headers=None, **kwargs):
    headers = headers or {}
    try:
        _write({"event": "publish", "task": sender, "id": headers.get("id"),
                "retries": headers.get("retries", 0), "eta": headers.get("eta")})
    except Exception as exc:
        _error("publish", exc, headers.get("id"))


@task_prerun.connect(weak=False)
def _prerun(task_id=None, task=None, **kwargs):
    try:
        from django.db import connection

        entry = {"start_monotonic": time.monotonic(), "start_cpu": time.thread_time(),
                 "retries": int(task.request.retries), "task": task.name,
                 "eager": bool(task.request.is_eager)}
        _running[task_id] = entry
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user")
            entry["sql_role"] = cursor.fetchone()[0]
        _write({"event": "prerun", "id": task_id, **{k: v for k, v in entry.items()
                                                      if k != "start_cpu"}})
    except Exception as exc:
        _error("prerun", exc, task_id)


@task_retry.connect(weak=False)
def _retry(sender=None, request=None, reason=None, **kwargs):
    task_id = getattr(request, "id", None)
    try:
        entry = _running[task_id]
        when = getattr(reason, "when", None)
        numeric = isinstance(when, (int, float)) and not isinstance(when, bool)
        if not numeric or not math.isfinite(when):
            raise ValueError("RetryCountdownNotFiniteNumeric")
        _write({"event": "retry", "task": entry["task"], "id": task_id,
                "retries": entry["retries"], "countdown": when,
                "exception_type": type(getattr(reason, "exc", None)).__name__,
                "eager": entry["eager"], "sql_role": entry["sql_role"]})
    except Exception as exc:
        _error("retry", exc, task_id)


@task_failure.connect(weak=False)
def _failure(task_id=None, exception=None, sender=None, **kwargs):
    try:
        entry = _running[task_id]
        _write({"event": "failure", "task": entry["task"], "id": task_id,
                "retries": entry["retries"], "exception_type": type(exception).__name__,
                "eager": entry["eager"], "sql_role": entry["sql_role"]})
    except Exception as exc:
        _error("failure", exc, task_id)


@task_postrun.connect(weak=False)
def _postrun(task_id=None, task=None, state=None, **kwargs):
    try:
        entry = _running.pop(task_id)
        end = time.monotonic()
        _write({"event": "execution", "task": entry["task"], "id": task_id,
                "retries": entry["retries"], "state": state, "eager": entry["eager"],
                "sql_role": entry["sql_role"], "start_monotonic": entry["start_monotonic"],
                "end_monotonic": end, "wall": end - entry["start_monotonic"],
                "thread_cpu": time.thread_time() - entry["start_cpu"]})
    except Exception as exc:
        _error("execution", exc, task_id)
