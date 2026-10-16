"""Explicit pytest plugin for generator diagnosis; never loaded by normal CI."""
import asyncio
import hashlib
import json
from pathlib import Path

import pytest

from scripts.benchmark_async_transport import POLICY

TARGET = 'tests/test_contract_http_load.py::test_contract_arrival_rate_http_with_limited_uploads[measured]'


def pytest_collection_modifyitems(items):
    if [item.nodeid for item in items] != [TARGET]:
        raise pytest.UsageError('Generator observer requires exactly the explicit measured HTTP node')


def observed_transport(fetch, routes, *, output, policy=POLICY, **kwargs):
    from owned_generator_schedule import ObservedLoop

    from scripts.benchmark_async_transport import _run

    loop = ObservedLoop()
    result = None

    def factory():
        asyncio.set_event_loop(loop)
        return loop

    try:
        result = asyncio.run(_run(fetch, routes, policy=policy, **kwargs), loop_factory=factory)
        return result
    finally:
        if not loop.is_closed():
            loop.close()
        report = loop.report()
        if result is not None:
            report['load'] = {key: result[key] for key in
                              ['monotonic_origin_seconds', 'counts', 'generator_delay_seconds',
                               'observable_latency_seconds', 'verdict', 'invalid_reasons']}
        report['scope'] = 'DIAGNOSTIC ONLY: unchanged emitter with observed loop; not acceptance timing'
        report['sources_sha256'] = {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [Path(__file__), Path('tests/owned_generator_schedule.py'),
                         Path('scripts/benchmark_async_transport.py')]
        }
        Path(output).write_text(json.dumps(report, indent=2)+'\n')


def pytest_runtest_setup(item):
    if item.nodeid != TARGET:
        raise pytest.UsageError('Unexpected item in explicit generator diagnostic')
    module = item.module
    original = module.run_async_open_loop
    output = Path(item.config.getoption('--gate-timings-output')).parent/'generator-schedule.json'

    def observed(fetch, routes, **kwargs):
        return observed_transport(fetch, routes, output=output, **kwargs)

    item._owned_generator_original = original
    module.run_async_open_loop = observed


def pytest_runtest_teardown(item):
    original = getattr(item, '_owned_generator_original', None)
    if original is not None:
        item.module.run_async_open_loop = original
        del item._owned_generator_original
