"""Marked WSGI diagnostics must retain response and worker lifecycle behavior."""

import json
import threading
from concurrent.futures import ThreadPoolExecutor

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
