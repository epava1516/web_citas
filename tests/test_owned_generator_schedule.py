"""Controls with known blocking and CPU work for the isolated loop observer."""
import asyncio
import time

from owned_generator_schedule import ObservedLoop


def execute(callback=None):
    loop = ObservedLoop()
    async def scenario():
        if callback is not None:
            loop.call_soon(callback)
        await asyncio.sleep(.07)
    try:
        loop.run_until_complete(scenario())
        return loop.report()
    finally:
        loop.close()


def test_normal_timer_is_not_callback_cpu():
    report = execute()
    assert report['iterations'] > 0
    assert report['maxima']['cpu'] < .025


def test_cpu_callback_is_observed_as_cpu():
    def busy():
        deadline = time.thread_time()+.04
        while time.thread_time() < deadline:
            pass
    report = execute(busy)
    assert any(e['callback_cpu'] >= .035 for e in report['events'])


def test_blocking_callback_is_observed_without_inventing_cpu():
    report = execute(lambda: time.sleep(.04))
    assert any(e['callback_wall'] >= .035 and e['callback_cpu'] < .02
               for e in report['events'])
    assert len(report['events']) <= 256


def test_observed_transport_preserves_original_accounting(tmp_path):
    import json

    from scripts.benchmark_async_transport import POLICY
    from scripts.benchmark_generator_diagnostic import observed_transport

    async def fetch(path, **kwargs):
        await asyncio.sleep(.001)
        return dict(status=200, unexpected=False, timeout=False, bytes=2)
    output = tmp_path/'observer.json'
    report = observed_transport(fetch, ['/synthetic/'], output=output,
                                duration=.2, rps=20, upload_specs=[], policy=POLICY)
    assert report['counts']['scheduled'] == report['counts']['successful'] == 4
    assert report['counts']['not_emitted'] == report['counts']['pending'] == 0
    observed = json.loads(output.read_text())
    assert observed['iterations'] > 0
    assert observed['load']['counts'] == report['counts']
    assert observed['scope'].startswith('DIAGNOSTIC ONLY')


def test_plugin_rejects_unrelated_selection_and_restores_function(tmp_path):
    from types import SimpleNamespace

    import pytest

    from scripts import benchmark_generator_diagnostic as plugin

    original = object()
    module = SimpleNamespace(run_async_open_loop=original)
    item = SimpleNamespace(nodeid=plugin.TARGET, module=module,
                           config=SimpleNamespace(getoption=lambda _: str(tmp_path/'timings.json')))
    with pytest.raises(pytest.UsageError):
        plugin.pytest_collection_modifyitems([SimpleNamespace(nodeid='unrelated')])
    plugin.pytest_collection_modifyitems([item])
    plugin.pytest_runtest_setup(item)
    assert module.run_async_open_loop is not original
    plugin.pytest_runtest_teardown(item)
    assert module.run_async_open_loop is original
