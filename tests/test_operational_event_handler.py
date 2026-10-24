"""Real kernel backpressure/fork and bounded descriptor ownership checks."""
import errno
import json
import logging
import os
import subprocess
import sys
import time

import pytest

from apps.core import operational_event_handler as transport


@pytest.mark.parametrize('scenario', ['recovery-fork', 'blocked-close', 'retirement-fork'])
def test_real_pipe_and_fork_lifecycle(tmp_path, scenario):
    output = tmp_path / 'probe.json'
    completed = subprocess.run(
        [sys.executable, '-m', 'scripts.probe_operational_sink', '--scenario', scenario,
         '--output', str(output)], capture_output=True, text=True, timeout=25,
    )
    assert completed.returncode == 0, completed.stderr[-2000:]
    proof = json.loads(output.read_text())
    assert proof['child_terminal'] and proof['scope'] == 'owned_real_pipe_not_HTTP_capacity'


@pytest.mark.parametrize('constructor', ['queue', 'thread'])
def test_initialization_failure_retires_every_duplicate(monkeypatch, constructor):
    read_fd, write_fd = os.pipe()
    handler = transport.NonBlockingOperationalHandler(stream_fd=write_fd)
    duplicates = []
    original_dup = os.dup
    def duplicate(fd):
        result = original_dup(fd)
        if fd == write_fd:
            duplicates.append(result)
        return result
    def fail(*args, **kwargs):
        raise RuntimeError('SYNTHETIC_INITIALIZATION_FAILURE')
    monkeypatch.setattr(transport.os, 'dup', duplicate)
    if constructor == 'queue':
        monkeypatch.setattr(transport.queue, 'Queue', fail)
    else:
        monkeypatch.setattr(transport.threading, 'Thread', fail)
    try:
        for _ in range(2):
            handler.handle(logging.makeLogRecord({'msg': 'fixed event'}))
        assert len(duplicates) == 2
        for fd in duplicates:
            with pytest.raises(OSError) as error:
                os.fstat(fd)
            assert error.value.errno == errno.EBADF
        os.fstat(write_fd)
        assert handler.transport_status()['write_errors'] == 2
    finally:
        handler.close()
        os.close(read_fd)
        os.close(write_fd)


def test_size_limit_and_closed_handler_never_start_a_writer():
    handler = transport.NonBlockingOperationalHandler()
    try:
        handler.handle(logging.makeLogRecord({'msg': 'x' * 1025}))
        assert handler.transport_status()['dropped'] == 1
        assert not handler.transport_status()['thread_alive']
        handler.close()
        handler.handle(logging.makeLogRecord({'msg': 'fixed event'}))
        assert not handler.transport_status()['thread_alive']
    finally:
        handler.close()


def test_broken_pipe_becomes_counter_without_exception_details():
    read_fd, write_fd = os.pipe()
    handler = transport.NonBlockingOperationalHandler(stream_fd=write_fd)
    os.close(read_fd)
    try:
        handler.handle(logging.makeLogRecord({'msg': 'fixed event'}))
        deadline = time.monotonic() + 3
        while not handler.transport_status()['write_errors'] and time.monotonic() < deadline:
            time.sleep(.01)
        assert handler.transport_status()['write_errors'] == 1
        assert 'BrokenPipe' not in json.dumps(handler.transport_status())
    finally:
        handler.close()
        if handler._thread is not None:
            handler._thread.join(3)
            assert not handler._thread.is_alive()
        os.close(write_fd)
