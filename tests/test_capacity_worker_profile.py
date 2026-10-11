"""Synthetic transport-independent tests; real integration belongs to root."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests import capacity_worker_profile as diagnostic


def functions():
    # Deliberate fixed-code fixture, no application imports or approval fixtures.
    namespace = {}
    exec(compile('''
def verify():
    total = 0
    for index in range(20000):
        total += index
    return total

def _verified_ciphertext():
    yield verify()
    verify()
''', '/fixture/apps/safety/object_storage/repository.py', 'exec'), namespace)
    return namespace


def run(function, count=1, prefix='rights-object-verify'):
    with ThreadPoolExecutor(max_workers=count, thread_name_prefix=prefix) as executor:
        return list(executor.map(lambda _: function(), range(count)))


def test_two_workers_bounded_phases_cpu_and_independent_snapshot():
    barrier = threading.Barrier(2)
    verify = functions()['verify']

    def work():
        barrier.wait(timeout=5)
        return verify()

    previous = threading.getprofile()
    with diagnostic.scope() as collector:
        values = run(work, 2)
    assert values[0] == values[1] == sum(range(20000))
    assert threading.getprofile() is previous
    result = collector.snapshot()
    assert result['status'] == 'complete'
    assert len(result['workers']) == 2
    for worker in result['workers']:
        phase = worker['phases']['repository_verify']
        assert phase['segments'] == 1
        assert phase['wall_seconds'] >= 0
        assert phase['thread_cpu_seconds'] > 0
    result['workers'][0]['phases'].clear()
    assert collector.snapshot()['workers'][0]['phases']


def test_generator_resume_segments_and_inclusive_overlap_not_wall_sum():
    functions_by_name = functions()

    def consume():
        return list(functions_by_name['_verified_ciphertext']())

    with diagnostic.scope() as collector:
        run(consume)
    worker = collector.snapshot()['workers'][0]
    assert worker['phases']['ciphertext_segments']['segments'] == 2
    assert worker['phases']['repository_verify']['segments'] == 2
    assert collector.snapshot()['timing_semantics'] == \
        'inclusive_execution_segments_overlap_not_request_wall'


def test_unmatched_thread_names_and_nonwhitelisted_code_ignored():
    with diagnostic.scope() as collector:
        run(functions()['verify'], prefix='unrelated')
        run(lambda: sum(range(100)))
    assert collector.snapshot()['workers'] == []
    assert collector.snapshot()['events'] == 0


def test_streaming_phases_match_qualified_adapter_only():
    namespace = {}
    exec(compile('''
class _HashedBodyReader:
    def _fetch(self):
        return True
    def finish(self):
        self._fetch()
class OtherReader:
    def _fetch(self):
        return True
    def finish(self):
        self._fetch()
''', '/fixture/apps/safety/object_storage/repository.py', 'exec'), namespace)

    def work():
        namespace['_HashedBodyReader']().finish()
        namespace['OtherReader']().finish()

    with diagnostic.scope() as collector:
        run(work)
    result = collector.snapshot()
    assert result['status'] == 'complete' and not result['incomplete']
    phases = result['workers'][0]['phases']
    assert set(phases) == {'ciphertext_fetch', 'ciphertext_finish'}
    assert phases['ciphertext_fetch']['segments'] == 1
    assert phases['ciphertext_finish']['segments'] == 1


def test_disabled_scope_never_installs_hook(monkeypatch):
    monkeypatch.setattr(threading, 'setprofile', lambda hook: pytest.fail('hook installed'))
    with diagnostic.scope(enabled=False) as collector:
        assert collector.snapshot()['status'] == 'inactive'


def test_existing_hook_preserved():
    previous = threading.getprofile()
    def hook(frame, event, arg):
        return None
    threading.setprofile(hook)
    try:
        with diagnostic.scope() as collector:
            assert collector.snapshot()['reason'] == 'existing_hook'
            assert threading.getprofile() is hook
        assert threading.getprofile() is hook
    finally:
        threading.setprofile(previous)


def test_nested_and_concurrent_scope_decline_without_clobbering():
    with diagnostic.scope() as outer:
        hook = threading.getprofile()
        with diagnostic.scope() as nested:
            assert nested.snapshot()['reason'] == 'concurrent_scope'
        with ThreadPoolExecutor(max_workers=1) as executor:
            def other():
                with diagnostic.scope() as concurrent:
                    return concurrent.snapshot()
            assert executor.submit(other).result(timeout=5)['reason'] == 'concurrent_scope'
        assert threading.getprofile() == hook
    assert outer.snapshot()['status'] == 'complete'


def test_callback_failure_preserves_domain_failure_and_teardown(monkeypatch):
    class DomainFailure(Exception):
        pass

    def broken_clock():
        raise RuntimeError('private diagnostic detail must not appear')

    namespace = {'DomainFailure': DomainFailure}
    exec(compile('def verify():\n    raise DomainFailure("original")\n',
                 '/fixture/apps/safety/object_storage/repository.py', 'exec'), namespace)
    monkeypatch.setattr(diagnostic.time, 'perf_counter', broken_clock)
    previous = threading.getprofile()
    with diagnostic.scope() as collector:
        with pytest.raises(DomainFailure, match='original'):
            run(namespace['verify'])
    assert threading.getprofile() is previous
    snapshot = collector.snapshot()
    assert snapshot['incomplete']
    assert snapshot['reason'] == 'callback_failure'
    assert 'private diagnostic' not in str(snapshot)


@pytest.mark.parametrize('limit,reason', [(0, 'event_bound'), (1, 'event_bound')])
def test_event_bound_does_not_change_results(monkeypatch, limit, reason):
    monkeypatch.setattr(diagnostic, 'MAX_EVENTS', limit)
    with diagnostic.scope() as collector:
        assert run(functions()['verify'])[0] == sum(range(20000))
    assert collector.snapshot()['reason'] == reason
    assert collector.snapshot()['events'] <= limit


def test_third_worker_is_bounded_without_affecting_work():
    barrier = threading.Barrier(3)
    verify = functions()['verify']

    def work():
        barrier.wait(timeout=5)
        return verify()

    with diagnostic.scope() as collector:
        assert len(run(work, 3)) == 3
    snapshot = collector.snapshot()
    assert snapshot['reason'] == 'worker_bound'
    assert len(snapshot['workers']) == 2


def test_segment_and_frame_bounds(monkeypatch):
    monkeypatch.setattr(diagnostic, 'MAX_SEGMENTS', 0)
    with diagnostic.scope() as collector:
        run(functions()['verify'])
    assert collector.snapshot()['reason'] == 'segment_bound'
    monkeypatch.setattr(diagnostic, 'MAX_SEGMENTS', 100)
    monkeypatch.setattr(diagnostic, 'MAX_OPEN_FRAMES', 0)
    with diagnostic.scope() as collector:
        run(functions()['verify'])
    assert collector.snapshot()['reason'] == 'frame_bound'


def test_scope_exception_restores_hook_and_propagates_same_exception():
    error = ValueError('domain')
    previous = threading.getprofile()
    with pytest.raises(ValueError) as captured:
        with diagnostic.scope():
            raise error
    assert captured.value is error
    assert threading.getprofile() is previous


def test_partial_hook_install_failure_restores_previous_hook(monkeypatch):
    previous = threading.getprofile()
    original_setprofile = threading.setprofile
    attempts = 0

    def partial_install(hook):
        nonlocal attempts
        attempts += 1
        original_setprofile(hook)
        if attempts == 1:
            raise RuntimeError('failed after installation')

    monkeypatch.setattr(threading, 'setprofile', partial_install)
    try:
        with diagnostic.scope() as collector:
            assert run(functions()['verify'])[0] == sum(range(20000))
        assert threading.getprofile() is previous
        assert collector.snapshot()['status'] == 'incomplete'
        assert collector.snapshot()['reason'] == 'hook_install_failure'
    finally:
        original_setprofile(previous)


def test_main_thread_cprofile_coexists_without_forwarding_worker_events():
    import cProfile
    import sys

    profiler = cProfile.Profile()
    previous = threading.getprofile()
    profiler.enable()
    try:
        main_hook = sys.getprofile()
        with diagnostic.scope() as collector:
            assert run(functions()['verify'])[0] == sum(range(20000))
            assert sys.getprofile() is main_hook
        assert sys.getprofile() is main_hook
    finally:
        profiler.disable()
    assert threading.getprofile() is previous
    assert collector.snapshot()['workers'][0]['phases']['repository_verify']['segments'] == 1
    # Only independent worker records are evidence; cProfile totals are neither
    # interpreted nor assumed to exclude every concurrent native event.


def test_timing_bound_clamps_report_and_preserves_result(monkeypatch):
    clock = iter([0.0, 1000.0])
    monkeypatch.setattr(diagnostic.time, 'perf_counter', lambda: next(clock))
    with diagnostic.scope() as collector:
        assert run(functions()['verify'])[0] == sum(range(20000))
    result = collector.snapshot()
    assert result['reason'] == 'timing_bound'
    assert result['workers'][0]['observed_wall_seconds'] == diagnostic.MAX_SECONDS


def test_replaced_hook_is_not_clobbered():
    previous = threading.getprofile()
    def replacement(frame, event, arg):
        return None
    try:
        with diagnostic.scope() as collector:
            threading.setprofile(replacement)
        assert threading.getprofile() is replacement
        assert collector.snapshot()['reason'] == 'hook_replaced'
    finally:
        threading.setprofile(previous)


def test_hook_install_failure_is_diagnostic_only(monkeypatch):
    def fail(hook):
        raise RuntimeError('must not replace domain result')

    monkeypatch.setattr(threading, 'setprofile', fail)
    with diagnostic.scope() as collector:
        result = 42
    assert result == 42
    assert collector.snapshot()['reason'] == 'hook_install_failure'


def test_scope_closed_before_workers_drain_reports_incomplete():
    started = threading.Event()
    release = threading.Event()
    namespace = {'started': started, 'release': release}
    exec(compile('def verify():\n    started.set()\n    release.wait(timeout=5)\n',
                 '/fixture/apps/safety/object_storage/repository.py', 'exec'), namespace)
    executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='rights-object-verify')
    try:
        with diagnostic.scope() as collector:
            future = executor.submit(namespace['verify'])
            assert started.wait(timeout=5)
        assert collector.snapshot()['reason'] == 'workers_not_drained'
        release.set()
        assert future.result(timeout=5) is None
    finally:
        release.set()
        executor.shutdown(wait=True)
