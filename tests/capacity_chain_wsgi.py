"""Owned finite diagnostic: clean control or chain-only instrumentation through EOF."""
import json
import os
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

from django.urls import get_resolver

from config.wsgi import application as original
from tests import capacity_chain_diagnostic


def application(environ, start_response):
    mode = environ.get('HTTP_X_CHAIN_DIAGNOSTIC')
    if mode not in ('control', 'instrumented'):
        response = original(environ, start_response)
        try:
            yield from response
        finally:
            response.close()
        return
    wall, cpu = perf_counter_ns(), thread_time_ns()
    get_resolver().url_patterns
    response = None
    from contextlib import nullcontext
    manager = capacity_chain_diagnostic.scope() if mode == 'instrumented' else nullcontext()
    with manager as collector:
        try:
            response = original(environ, start_response)
            yield from response
        finally:
            if response is not None:
                response.close()
    report = dict(mode=mode, wsgi_wall_ns=perf_counter_ns() - wall,
                  wsgi_thread_cpu_ns=thread_time_ns() - cpu,
                  chain=collector.snapshot() if collector else None)
    output = Path(os.environ['CHAIN_DIAGNOSTIC_OUTPUT'])
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(report))
    temporary.replace(output)
