"""Lightweight own-run WSGI boundaries and route, no rule/SQL profiler."""

import json
import os
import time
from pathlib import Path


class RouteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        request.META["_publication_route_observed"] = getattr(request, "_publication_route", None)
        return response


def post_worker_init(worker):
    folder = Path(os.environ["PUBLICATION_TCP_EVENTS"])
    fd = os.open(
        folder / f"worker-{os.getpid()}.jsonl",
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_APPEND,
        0o600,
    )
    original = worker.wsgi

    def observed(environ, start_response):
        request_id = environ.get("HTTP_X_BENCHMARK_ID", "")
        entry = time.monotonic()
        response = None
        try:
            response = original(environ, start_response)
            yield from response
        finally:
            if response is not None and hasattr(response, "close"):
                response.close()
            end = time.monotonic()
            if request_id.startswith("d-"):
                record = {
                    "id": request_id,
                    "pid": os.getpid(),
                    "entry": entry,
                    "exit": end,
                    "route": environ.get("_publication_route_observed"),
                }
                os.write(fd, (json.dumps(record) + "\n").encode())

    worker.wsgi = observed
