"""Low-event consumer spans on explicitly owned clones; control/count/spans are separate."""

import gc
import json
import os
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

from django.db import connection
from django.urls import get_resolver

from config.wsgi import application as original
from tests.capacity_scalar_diagnostic import scope


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
    mode = environ.get("HTTP_X_CHAIN_VARIANT")
    assert mode in {"control", "spans", "count"}
    connection.close()
    previous = connection.settings_dict["NAME"]
    connection.settings_dict["NAME"] = name
    get_resolver().url_patterns
    response, collector = None, None
    before_gc = gc.get_stats()
    wall, cpu = perf_counter_ns(), thread_time_ns()
    try:
        with ExitStack() as stack:
            if mode != "control":
                collector = stack.enter_context(scope(mode))

            def start(status, headers, exc_info=None):
                return start_response(status, headers + [("X-Benchmark-Pid", str(os.getpid()))],
                                      exc_info)

            response = original(environ, start)
            yield from response
    finally:
        if response is not None:
            response.close()
        connection.close()
        connection.settings_dict["NAME"] = previous
    cpu, wall = thread_time_ns() - cpu, perf_counter_ns() - wall
    after_gc = gc.get_stats()
    report = dict(mode=mode, pid=os.getpid(), wsgi_wall_ns=wall, wsgi_thread_cpu_ns=cpu,
                  gc_enabled=gc.isenabled(), gc_thresholds=gc.get_threshold(),
                  gc_collections=[b["collections"] - a["collections"]
                                  for a, b in zip(before_gc, after_gc, strict=True)])
    if collector:
        report["diagnostic"] = dict(spans=collector.spans, calls=collector.calls,
                                    sites=collector.sites, source=collector.source,
                                    compile_rows=collector.compile_rows)
    output = Path(os.environ["CHAIN_CLONE_OUTPUT"])
    temporary = output.with_suffix(".tmp")
    temporary.write_text(json.dumps(report))
    temporary.replace(output)
