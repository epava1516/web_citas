"""Startup prepares structures without private data or request side effects."""
import runpy
import socket
import threading
from contextlib import ExitStack
from types import SimpleNamespace

import pytest
from django.db import connections
from django.utils.translation import get_language, override

from config.worker_startup import post_worker_init, prepare_static_structures


def test_static_preparation_has_no_network_database_or_language_side_effects(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Static preparation must not access external state')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    threads = threading.enumerate()
    with ExitStack() as stack:
        for connection in connections.all():
            stack.enter_context(connection.execute_wrapper(forbidden))
        with override('fr'):
            prepare_static_structures()
            prepare_static_structures()
            assert get_language() == 'fr'
    assert threading.enumerate() == threads


def test_default_gunicorn_hook_runs_preparation_and_propagates_failure(monkeypatch):
    assert runpy.run_path('gunicorn.conf.py')['post_worker_init'] is post_worker_init
    calls = []
    monkeypatch.setattr('config.worker_startup.prepare_static_structures', lambda: calls.append('ready'))
    worker = SimpleNamespace(pid=123, log=SimpleNamespace(info=lambda *args: calls.append('logged')))
    post_worker_init(worker)
    assert calls == ['ready', 'logged']
    def failure():
        raise RuntimeError('Preparation failed')
    monkeypatch.setattr('config.worker_startup.prepare_static_structures', failure)
    with pytest.raises(RuntimeError, match='Preparation failed'):
        post_worker_init(worker)
