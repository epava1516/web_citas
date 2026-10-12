"""Original-only request clocks on allowlisted owned clones, telemetry outside clocks."""

import gc
import json
import os
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

from django.db import connection
from django.urls import get_resolver

from apps.safety.canonical_kernel_loader import kernel_identity
from config.wsgi import application as original


def application(environ, start_response):
    name = environ.get("HTTP_X_CHAIN_CLONE")
    if name is None:
        response = original(environ, start_response)
        try:
            yield from response
        finally:
            response.close()
        return
    allowed = json.loads(Path(os.environ["CHAIN_CLONE_ALLOWLIST"]).read_text())
    assert name in allowed
    connection.close()
    previous = connection.settings_dict["NAME"]
    connection.settings_dict["NAME"] = name
    get_resolver().url_patterns
    response = None
    kernel = kernel_identity()
    host_before = host_state()
    before_gc = gc.get_stats()
    wall, cpu = perf_counter_ns(), thread_time_ns()
    try:
        def start(status, headers, exc_info=None):
            return start_response(status, headers + [("X-Benchmark-Pid", str(os.getpid()))], exc_info)
        response = original(environ, start)
        yield from response
    finally:
        if response is not None:
            response.close()
        connection.close()
        connection.settings_dict["NAME"] = previous
    cpu, wall = thread_time_ns() - cpu, perf_counter_ns() - wall
    after_gc = gc.get_stats()
    report = dict(kernel=kernel, host_before=host_before, host_after=host_state(), pid=os.getpid(), wsgi_wall_ns=wall, wsgi_thread_cpu_ns=cpu,
                  gc_enabled=gc.isenabled(), gc_thresholds=gc.get_threshold(),
                  gc_collections=[b["collections"] - a["collections"]
                                  for a, b in zip(before_gc, after_gc, strict=True)])
    output = Path(os.environ["CHAIN_CLONE_OUTPUT"])
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(report))
    temporary.replace(output)


def host_state():
    # Only read-only, outside request timers; values can correlate, not explain causally.
    status = Path('/proc/self/status').read_text().splitlines()
    return dict(loadavg=list(os.getloadavg()),
                memory=[line for line in status if line.startswith(('VmRSS:', 'VmHWM:'))])
