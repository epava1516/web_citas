"""Marked WSGI diagnostics must retain response and worker lifecycle behavior."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager

import capacity_profile_wsgi as wrapper
import pytest


class Response:
    def __init__(self, *, close_error=None):
        self.closed = False
        self.close_error = close_error

    def __iter__(self):
        yield b'original body'

    def close(self):
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


def outputs(monkeypatch):
    saved = {}

    def write(path, value):
        saved[path.name] = value

    monkeypatch.setattr(wrapper.Path, 'write_text', write)
    return saved


@pytest.mark.parametrize('close_failure', [False, True])
@pytest.mark.parametrize('stage', ['json_download', 'coverage_page_read'])
def test_native_mode_avoids_old_profile_hooks_and_preserves_close(monkeypatch, close_failure, stage):
    import capacity_native_profile

    error = ValueError('native-mode original close failure')
    response = Response(close_error=error if close_failure else None)
    order = []

    @contextmanager
    def capture(stage):
        order.append('enter')
        try:
            yield
        finally:
            assert response.closed
            order.append('leave')

    monkeypatch.setattr(wrapper.settings, 'CAPACITY_NATIVE_PROFILE', True, raising=False)
    monkeypatch.setattr(capacity_native_profile, 'capture', capture)
    monkeypatch.setattr(wrapper.cProfile, 'Profile', lambda: pytest.fail('cProfile installed'))
    monkeypatch.setattr(wrapper, 'scope', lambda: pytest.fail('worker hooks installed'))
    monkeypatch.setattr(wrapper, 'phase_scope', lambda **kwargs: pytest.fail('phase hooks installed'))
    monkeypatch.setattr(wrapper, 'observe', lambda *args, **kwargs: pytest.fail('request observer installed'))
    monkeypatch.setattr(wrapper, 'original', lambda environ, start: response)
    saved = outputs(monkeypatch)
    operation = wrapper.application({'HTTP_X_CAPACITY_PROFILE': stage,
                                     'HTTP_X_CAPACITY_LISTING_SAMPLE': '1'}, lambda *args: None)
    if close_failure:
        with pytest.raises(ValueError) as caught:
            list(operation)
        assert caught.value is error
    else:
        assert list(operation) == [b'original body']
    assert order == ['enter', 'leave']
    assert len(saved) == 1 and 'cProfile and worker profile hooks disabled' in next(iter(saved.values()))


@pytest.mark.parametrize('close_failure', [False, True])
def test_native_controls_have_no_in_process_observers(monkeypatch, close_failure):
    error = ValueError('control close failure')
    response = Response(close_error=error if close_failure else None)
    monkeypatch.setattr(wrapper.settings, 'CAPACITY_NATIVE_PROFILE', True, raising=False)
    monkeypatch.setattr(wrapper, 'original', lambda environ, start: response)
    monkeypatch.setattr(wrapper, 'observe', lambda *args, **kwargs: pytest.fail('request observer installed'))
    monkeypatch.setattr(wrapper, 'phase_scope', lambda **kwargs: pytest.fail('phase hooks installed'))
    monkeypatch.setattr(wrapper, 'scope', lambda: pytest.fail('worker hooks installed'))
    monkeypatch.setattr(wrapper.cProfile, 'Profile', lambda: pytest.fail('cProfile installed'))
    saved = outputs(monkeypatch)
    operation = wrapper.application({'HTTP_X_CAPACITY_LISTING_SAMPLE': '1'}, lambda *args: None)
    if close_failure:
        with pytest.raises(ValueError) as caught:
            list(operation)
        assert caught.value is error
    else:
        assert list(operation) == [b'original body']
    assert response.closed and saved == {}


@pytest.mark.parametrize('marker', ['', 'bad-marker!', 'a' * 41])
def test_unmarked_or_invalid_request_never_installs_worker_scope(monkeypatch, marker):
    response = Response()
    monkeypatch.setattr(wrapper, 'original', lambda environ, start: response)
    monkeypatch.setattr(wrapper, 'scope', lambda: pytest.fail('worker scope installed'))
    saved = outputs(monkeypatch)
    assert list(wrapper.application({'HTTP_X_CAPACITY_PROFILE': marker}, lambda *args: None)) == [
        b'original body']
    assert response.closed and saved == {}


def test_marked_real_workers_produce_aggregate_only_after_draining(monkeypatch):
    namespace = {}
    exec(compile('def verify():\n    return sum(range(20000))\n',
                 '/fixture/apps/safety/object_storage/repository.py', 'exec'), namespace)
    barrier = threading.Barrier(2)
    response = Response()

    def original(environ, start):
        def work():
            barrier.wait(timeout=5)
            return namespace['verify']()

        with ThreadPoolExecutor(max_workers=2, thread_name_prefix='rights-object-verify') as executor:
            assert len(list(executor.map(lambda _: work(), range(2)))) == 2
        return response

    monkeypatch.setattr(wrapper, 'original', original)
    saved = outputs(monkeypatch)
    previous = threading.getprofile()
    assert list(wrapper.application({'HTTP_X_CAPACITY_PROFILE': 'json_download_proxy'},
                                    lambda *args: None)) == [b'original body']
    assert response.closed and threading.getprofile() is previous
    assert len(saved) == 1
    text = next(iter(saved.values()))
    result = json.loads(text.split('Capacity worker diagnostic JSON:\n', 1)[1])
    assert result['status'] == 'complete' and not result['incomplete']
    assert len(result['workers']) == 2
    assert all(w['phases']['repository_verify']['segments'] == 1 for w in result['workers'])
    assert '/fixture' not in text.split('Capacity worker diagnostic JSON:\n', 1)[1]


@pytest.mark.parametrize('failure_at', ['original', 'close'])
def test_domain_failure_remains_identical_and_hook_is_restored(monkeypatch, failure_at):
    error = ValueError('original domain failure')
    response = Response(close_error=error if failure_at == 'close' else None)

    def original(environ, start):
        if failure_at == 'original':
            raise error
        return response

    monkeypatch.setattr(wrapper, 'original', original)
    outputs(monkeypatch)
    previous = threading.getprofile()
    with pytest.raises(ValueError) as captured:
        list(wrapper.application({'HTTP_X_CAPACITY_PROFILE': 'binary_download_proxy'},
                                 lambda *args: None))
    assert captured.value is error and threading.getprofile() is previous
    if failure_at == 'close':
        assert response.closed


@pytest.mark.parametrize('close_failure', [False, True])
def test_listing_phase_marker_bypasses_both_profilers_and_drains(monkeypatch, close_failure):
    error = ValueError('domain close failure')
    response = Response(close_error=error if close_failure else None)
    order = []

    class Collector:
        def snapshot(self):
            assert response.closed and order == ['enter', 'exit']
            return {'status': 'complete', 'pages': [1, 2, 3, 4]}

    @contextmanager
    def phase_scope(*, sql_context):
        assert callable(sql_context)
        order.append('enter')
        try:
            yield Collector()
        finally:
            order.append('exit')

    monkeypatch.setattr(wrapper, 'phase_scope', phase_scope)
    monkeypatch.setattr(wrapper, 'scope', lambda: pytest.fail('worker hook installed'))
    monkeypatch.setattr(wrapper.cProfile, 'Profile', lambda: pytest.fail('cProfile installed'))
    monkeypatch.setattr(wrapper, 'original', lambda environ, start: response)
    saved = outputs(monkeypatch)
    request = wrapper.application({'HTTP_X_CAPACITY_PROFILE': 'coverage_page_read'},
                                  lambda *args: None)
    if close_failure:
        with pytest.raises(ValueError) as captured:
            list(request)
        assert captured.value is error
    else:
        assert list(request) == [b'original body']
    text = next(iter(saved.values()))
    result = json.loads(text.split('Capacity listing phase diagnostic JSON:\n', 1)[1])
    assert result == {'status': 'complete', 'pages': [1, 2, 3, 4]}
