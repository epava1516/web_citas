"""Owned resource checkpoint: WSGI wall/threadCPU and actual route only.

No SQL/render/rule wrappers or Python profiler. SQL CPU comes from OS counters
of the PostgreSQL cgroup/processes, not from cursor wall time.
"""

import os
from pathlib import Path

from scripts.benchmark_worker_observer import _CURRENT, WorkerObserver, worker_exit  # noqa: F401


def post_worker_init(worker):
    from django.db import connection

    folder = os.environ["WEB_MODELOS_BENCHMARK_OBSERVER_DIR"]
    if not Path(folder).is_dir() or not connection.settings_dict["NAME"].startswith(
        "test_promotion_gate_"
    ):
        raise RuntimeError("Only owned synthetic database")
    observer = WorkerObserver(folder)
    worker._benchmark_observer = observer
    original = worker.wsgi.get_response

    def response(request):
        result = original(request)
        state = _CURRENT.get()
        if state is not None:
            route = getattr(request, "_publication_route", None)
            observer.write(
                state,
                "publication_route",
                **(route or {"route": "native", "reason": "handler_without_projection"}),
            )
        return result

    worker.wsgi.get_response = response
    worker.wsgi = observer.wsgi(worker.wsgi)
