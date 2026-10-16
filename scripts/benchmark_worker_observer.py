"""Opt-in Gunicorn diagnostics, restricted to disposable synthetic test databases."""

import hashlib
import json
import os
import re
import sys
import time
from contextvars import ContextVar
from functools import wraps
from pathlib import Path

_CURRENT = ContextVar("benchmark_worker_request", default=None)
_ID = re.compile(r"[du]-[0-9]+\Z")


class WorkerObserver:
    def __init__(self, folder, *, observe_gc=False, observe_prelude=False):
        self.prelude_remaining = 32 if observe_prelude else 0
        self.pid = os.getpid()
        self.fd = os.open(
            Path(folder) / f"worker-{self.pid}.jsonl",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND,
            0o600,
        )

        self.gc_observer = None
        if observe_gc:
            from scripts.benchmark_gc_observer import GCObserver

            self.gc_observer = GCObserver(monotonic_clock=time.monotonic)
            self.gc_observer.__enter__()

    def write(self, state, event, **values):
        record = {
            "id": state["id"],
            "pid": self.pid,
            "event": event,
            "monotonic": time.monotonic(),
            **values,
        }
        payload = (json.dumps(record, separators=(",", ":")) + "\n").encode()
        if os.write(self.fd, payload) != len(payload):
            raise OSError("Incomplete diagnostic event write")

    def measured(self, name, original, *, progress=False):
        @wraps(original)
        def call(*args, **kwargs):
            state = _CURRENT.get()
            if state is None:
                return original(*args, **kwargs)
            bucket = state["stages"].setdefault(name, {"calls": 0, "wall": 0.0, "thread_cpu": 0.0})
            if not progress or bucket["calls"] == 0:
                self.write(state, "stage_start", stage=name)
            wall, cpu = time.monotonic(), time.thread_time()
            try:
                return original(*args, **kwargs)
            finally:
                bucket["calls"] += 1
                bucket["wall"] += time.monotonic() - wall
                bucket["thread_cpu"] += time.thread_time() - cpu
                if not progress or bucket["calls"] % 1000 == 0:
                    self.write(
                        state,
                        "stage_progress" if progress else "stage_end",
                        stage=name,
                        stages=state["stages"],
                        sql=state["sql"],
                    )

        return call

    def sql(self, execute, sql, params, many, context):
        state = _CURRENT.get()
        if state is None:
            return execute(sql, params, many, context)
        wall, cpu = time.monotonic(), time.thread_time()
        try:
            return execute(sql, params, many, context)
        finally:
            elapsed, used_cpu = time.monotonic() - wall, time.thread_time() - cpu
            state["sql"]["calls"] += 1
            state["sql"]["wall"] += elapsed
            state["sql"]["thread_cpu"] += used_cpu
            # Bounded diagnostic attribution; never retain SQL or parameter values.
            fingerprint = hashlib.sha256(str(sql).encode()).hexdigest()
            queries = state["sql"].setdefault("queries", {})
            key = fingerprint if fingerprint in queries or len(queries) < 32 else "overflow"
            if key not in queries and key != "overflow":
                root = str(Path(__file__).resolve().parents[1]) + os.sep
                frame = sys._getframe(1)
                try:
                    for _ in range(32):
                        if frame is None:
                            break
                        filename = frame.f_code.co_filename
                        if filename.startswith(root + "apps" + os.sep):
                            queries[key] = {
                                "calls": 0,
                                "wall": 0.0,
                                "thread_cpu": 0.0,
                                "caller": filename[len(root) :] + ":" + str(frame.f_lineno),
                            }
                            break
                        frame = frame.f_back
                finally:
                    del frame
            bucket = queries.setdefault(key, {"calls": 0, "wall": 0.0, "thread_cpu": 0.0})
            bucket["calls"] += 1
            bucket["wall"] += elapsed
            bucket["thread_cpu"] += used_cpu

    def wsgi(self, original):
        def application(environ, start_response):
            identity = environ.get("HTTP_X_BENCHMARK_ID", "")
            prelude = False
            if not _ID.fullmatch(identity):
                if identity or self.prelude_remaining <= 0:
                    return original(environ, start_response)
                self.prelude_remaining -= 1
                identity = "p-" + str(32 - self.prelude_remaining)
                prelude = True
            state = {
                "id": identity,
                "started": time.monotonic(),
                "cpu_started": time.thread_time(),
                "status": None,
                "stages": {},
                "sql": {"calls": 0, "wall": 0.0, "thread_cpu": 0.0},
            }
            if self.gc_observer is not None:
                state["gc_start"] = len(self.gc_observer.events)
            token = _CURRENT.set(state)
            self.write(state, "wsgi_start", started=state["started"], prelude=prelude)

            def status(response_status, headers, exc_info=None):
                state["status"] = int(response_status.split()[0])
                return start_response(response_status, headers, exc_info)

            try:
                response = original(environ, status)
            except BaseException as error:
                self.finish(state, token, type(error).__name__)
                raise
            return ObservedResponse(self, response, state, token)

        return application

    def finish(self, state, token, error=None):
        extra = {}
        if self.gc_observer is not None:
            events = self.gc_observer.events[state["gc_start"]:]
            own = [e for e in events if e["on_observer_thread"]]
            extra["gc"] = {
                "events_count": len(events),
                "on_worker_thread_count": len(own),
                "wall_seconds": sum(e["wall_seconds"] for e in own),
                "thread_cpu_seconds": sum(e["collector_thread_cpu_seconds"] for e in own),
                "largest_events": sorted(own, key=lambda e: e["wall_seconds"], reverse=True)[:16],
                "scope": "GC intervals overlap request/stages/SQL; never add as independent cost. "
                         "Other-thread collections excluded from sums. Policy unchanged, no forced GC. "
                         "Callback overhead not measured; only16largest intervals retained per request.",
            }
        try:
            self.write(
                state,
                "wsgi_end",
                status=state["status"],
                error_type=error,
                wall=time.monotonic() - state["started"],
                thread_cpu=time.thread_time() - state["cpu_started"],
                stages=state["stages"],
                sql=state["sql"],
                **extra,
            )
        finally:
            _CURRENT.reset(token)

    def close(self):
        try:
            if self.gc_observer is not None:
                self.gc_observer.__exit__()
        finally:
            os.close(self.fd)


class ObservedResponse:
    def __init__(self, observer, response, state, token):
        self.observer, self.response = observer, response
        self.state, self.token = state, token
        self.iterator = iter(response)
        self.closed = False
        self.error = None

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return next(self.iterator)
        except StopIteration:
            raise
        except BaseException as error:
            self.error = type(error).__name__
            raise

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if hasattr(self.response, "close"):
                self.response.close()
        except BaseException as error:
            self.error = type(error).__name__
            raise
        finally:
            self.observer.finish(self.state, self.token, self.error)


def post_worker_init(worker):
    from django.db import connection

    from apps.listings import discovery, moderation, moderation_views
    from apps.listings.public_validation import PublicationContext

    folder = os.environ.get("WEB_MODELOS_BENCHMARK_OBSERVER_DIR")
    if (
        not folder
        or not Path(folder).is_dir()
        or connection.vendor != "postgresql"
        or not connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    ):
        raise RuntimeError("Observer requires an owned synthetic PostgreSQL runner")
    observer = WorkerObserver(folder, observe_gc=True)
    worker._benchmark_observer = observer
    route_only = os.environ.get("WEB_MODELOS_BENCHMARK_ROUTE_ONLY") == "1"
    if not route_only:
        PublicationContext.__init__ = observer.measured("context", PublicationContext.__init__)
        moderation.validate_submission = observer.measured(
            "validation", moderation.validate_submission, progress=True
        )
    else:
        original_response = worker.wsgi.get_response

        def route_response(request):
            try:
                return original_response(request)
            finally:
                state = _CURRENT.get()
                if state is not None:
                    route = getattr(request, "_publication_route", None)
                    if route is None:
                        route = {"route": "native", "reason": "handler_without_projection"}
                    observer.write(state, "publication_route", **route)

        worker.wsgi.get_response = route_response
    discovery.render = observer.measured("render", discovery.render)
    moderation_views.render = observer.measured("render", moderation_views.render)
    connection.execute_wrappers.append(observer.sql)
    worker.wsgi = observer.wsgi(worker.wsgi)


def worker_exit(server, worker):
    if hasattr(worker, "_benchmark_observer"):
        worker._benchmark_observer.close()


def collect_events(folder):
    events, errors = [], []
    for path in sorted(Path(folder).glob("worker-*.jsonl")):
        for number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                errors.append(
                    {"file": path.name, "line": number, "error": "truncated_or_invalid_json"}
                )
    return {
        "events": events,
        "parse_errors": errors,
        "scope": "WSGI entry/end and phase snapshots of identified synthetic requests. Partial snapshots are lower-bound observed work, not inferred zeros. Phase/SQL/thread CPU timings include instrumentation and overlap, never sum as a request partition. WSGI entry is not TCP accept; end includes response.close. No raw URI, headers, body, SQL or parameters stored; PostgreSQL CPU/rows/RSS/waits/locks/IO and causal observer overhead not_measured.",
    }
