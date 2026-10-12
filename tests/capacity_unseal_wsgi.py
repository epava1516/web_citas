"""One marked diagnostic POST; original WSGI response, fresh checks and EOF intact."""
import json
import os
from pathlib import Path
from time import perf_counter_ns, thread_time_ns

from django.db import connection
from django.urls import get_resolver

from config.wsgi import application as original
from tests import capacity_phase_spans, capacity_unseal_diagnostic


def application(environ, start_response):
    if environ.get('HTTP_X_UNSEAL_DIAGNOSTIC') != 'one_batch':
        response = original(environ, start_response)
        try:
            yield from response
        finally:
            response.close()
        return
    response = None
    wall, cpu = perf_counter_ns(), thread_time_ns()
    # This worker may never have served the warm-up GET. Resolve the same URL
    # module inventory Django would load for this request before planning aliases.
    # No domain validation/read is performed; import time stays in WSGI/TCP total.
    get_resolver().url_patterns
    with capacity_unseal_diagnostic.scope() as unseal:
        with capacity_phase_spans.scope(sql_context=connection.execute_wrapper) as phases:
            try:
                response = original(environ, start_response)
                yield from response
            finally:
                if response is not None:
                    response.close()
    report = {'unseal': unseal.snapshot(), 'phases': phases.snapshot(),
              'wsgi_wall_ns': perf_counter_ns() - wall,
              'wsgi_thread_cpu_ns': thread_time_ns() - cpu,
              'runtime_enforced': True, 'scope': 'single_instrumented_HTTP_not_p95'}
    # Destination is a per-test private directory, supplied only to owned child.
    destination = Path(os.environ['UNSEAL_DIAGNOSTIC_OUTPUT'])
    temporary = destination.with_suffix('.tmp')
    temporary.write_text(json.dumps(report))
    temporary.replace(destination)
