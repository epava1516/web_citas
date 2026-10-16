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
