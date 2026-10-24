"""Opt-in owned sync-worker boundaries, without app/SQL/render wrappers."""

import json
import math
import os
import re
from functools import wraps
from pathlib import Path
from time import monotonic

_ID = re.compile(r"[du]-[0-9]{1,6}\Z")
_FIELDS = {"id", "pid", "handler_entered", "pre_request_entered", "handler_exited",
           "native_handle_returned"}


def install_sync_boundary_hooks(worker, folder):
    if hasattr(worker, "_owned_sync_boundaries"):
        raise RuntimeError("Sync boundaries already installed")
    fd = os.open(Path(folder) / f"worker-{os.getpid()}.jsonl",
                 os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    original_handle, original_pre = worker.handle, worker.cfg.pre_request
    active = None

    @wraps(original_pre)
    def pre_request(target, request):
        if active is not None:
            active["pre_request_entered"] = monotonic()
            identities = [value for name, value in request.headers
                          if name.lower() == "x-benchmark-id"]
            if len(identities) == 1 and _ID.fullmatch(identities[0]):
                active["id"] = identities[0]
        return original_pre(target, request)

    @wraps(original_handle)
    def handle(*args, **kwargs):
        nonlocal active
        if active is not None:
            raise RuntimeError("Sync boundary observer cannot nest handlers")
        state = {"handler_entered": monotonic(), "pid": os.getpid(),
                 "native_handle_returned": False}
        active = state
        try:
            result = original_handle(*args, **kwargs)
            state["native_handle_returned"] = True
            return result
        finally:
            state["handler_exited"] = monotonic()
            active = None
            if "id" in state:
                os.write(fd, (json.dumps(state, separators=(",", ":")) + "\n").encode())

    worker.cfg.set("pre_request", pre_request)
    worker.handle = handle
    worker._owned_sync_boundaries = (fd, original_handle, original_pre)


def close_sync_boundary_hooks(worker):
    saved = getattr(worker, "_owned_sync_boundaries", None)
    if saved is not None:
        fd, original_handle, original_pre = saved
        worker.handle = original_handle
        worker.cfg.set("pre_request", original_pre)
        del worker._owned_sync_boundaries
        os.close(fd)


def post_worker_init(worker):
    from django.conf import settings
    from django.db import connection
    from gunicorn.workers.sync import SyncWorker

    run = os.environ.get("LOCAL_CI_BENCHMARK_RUN", "")
    folder = os.environ.get("WEB_MODELOS_SYNC_BOUNDARIES_DIR", "")
    expected = settings.BASE_DIR / "artifacts" / "local-ci" / run / "server-boundaries-raw"
    db = connection.settings_dict
    if (not re.fullmatch(r"\d{8}-\d{6}-[0-9a-f]{8}", run)
            or not isinstance(worker, SyncWorker) or worker.cfg.threads != 1
            or settings.PRODUCTION or settings.RECOVERY_MODE or not settings.PROMOTION_TEST_MODE
            or db["ENGINE"] != "django.db.backends.postgresql"
            or not db["NAME"].startswith("test_promotion_gate_")
            or db["HOST"] != "127.0.0.1" or db["USER"] != "ci"
            or os.environ.get("LOCAL_CI_POSTGRES_CONTAINER") != "web-modelos-ci-pg-" + run
            or not folder or Path(folder).resolve() != expected.resolve()
            or not expected.is_dir()):
        raise RuntimeError("Sync boundaries require exact owned synthetic single-thread runner")
    install_sync_boundary_hooks(worker, expected)


def worker_exit(server, worker):
    close_sync_boundary_hooks(worker)


def collect_sync_boundaries(folder):
    samples, errors, seen = [], [], set()
    for path in sorted(Path(folder).glob("worker-*.jsonl")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                row = json.loads(line)
                if (not isinstance(row, dict) or set(row) != _FIELDS
                        or not isinstance(row["id"], str) or not _ID.fullmatch(row["id"])
                        or type(row["pid"]) is not int or row["pid"] <= 0
                        or type(row["native_handle_returned"]) is not bool
                        or any(type(row[k]) not in (int, float) or not math.isfinite(row[k])
                               for k in ("handler_entered", "pre_request_entered", "handler_exited"))
                        or not 0 <= row["handler_entered"] <= row["pre_request_entered"] <= row["handler_exited"]
                        or row["id"] in seen):
                    raise ValueError("Invalid or duplicate boundary row")
                seen.add(row["id"])
                samples.append(row)
            except (ValueError, TypeError, KeyError):
                errors.append({"file": path.name, "line": number, "reason": "invalid_or_duplicate"})
    return {"samples": samples, "parse_errors": errors,
            "scope": "Same-host time.monotonic: handler entry after native accept/setblocking/cloexec, pre_request entry after HTTP parser, handler exit after native response cleanup. No exact TCP accept timestamp, socket-only queue, app/DB CPU or causal observer overhead. Only synthetic IDs; file append after handler exit."}
