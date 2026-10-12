"""Test-only SQL controls on explicitly owned clones, normal committed HTTP requests."""
import json
import os
from contextlib import ExitStack
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

from django.db import connection
from django.urls import get_resolver

from apps.safety.canonical_kernel_loader import kernel_identity
from config.wsgi import application as original
from tests.capacity_full_wait_diagnostic import scope


def application(environ, start_response):
    name = environ.get('HTTP_X_CHAIN_CLONE')
    if name is None:
        response = original(environ, start_response)
        try:
            yield from response
        finally:
            response.close()
        return
    allowed = json.loads(Path(os.environ['CHAIN_CLONE_ALLOWLIST']).read_text())
    assert name in allowed
    mode = environ.get('HTTP_X_CHAIN_VARIANT')
    assert mode in ('control', 'profiled')
    connection.close()
    previous = connection.settings_dict['NAME']
    connection.settings_dict['NAME'] = name
    response = None
    get_resolver().url_patterns
    collector = None
    kernel = kernel_identity()
    wall, cpu = perf_counter_ns(), thread_time_ns()
    try:
        with ExitStack() as stack:
            if mode == 'profiled':
                collector = stack.enter_context(scope())
            def start(status, headers, exc_info=None):
                return start_response(status, headers + [('X-Benchmark-Pid', str(os.getpid()))], exc_info)
            response = original(environ, start)
            yield from response
    finally:
        if response is not None:
            response.close()
        connection.close()
        connection.settings_dict['NAME'] = previous
    report = dict(mode=mode, pid=os.getpid(), kernel=kernel, wsgi_wall_ns=perf_counter_ns()-wall,
                  wsgi_thread_cpu_ns=thread_time_ns()-cpu)
    report['source'] = dict(spans=collector.spans, fetch_counts=collector.fetch_counts) if collector else None
    output = Path(os.environ['CHAIN_CLONE_OUTPUT'])
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(report))
    temporary.replace(output)
