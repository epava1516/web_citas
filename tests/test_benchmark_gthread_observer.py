"""Pure delegation/context controls; no real server or capacity evidence."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from types import SimpleNamespace

import pytest

from scripts.benchmark_gthread_observer import _CONNECTION, install_admission_hooks


def test_admission_hooks_preserve_native_results_and_isolate_thread_contexts():
    events, init_calls, enqueue_calls = [], [], []
    barrier = Barrier(2)

    class Connection:
        def __init__(self, identity, *, secret):
            self.identity = identity
            init_calls.append(identity)

    def write(state, event, **values):
        events.append({"id": state["id"], "event": event, **values})
        return "native-write"

    observer = SimpleNamespace(write=write)

    def handle(conn):
        identity = conn.identity
        barrier.wait(timeout=5)
        assert observer.write({"id": identity}, "wsgi_start") == "native-write"
        assert _CONNECTION.get()["connection_created"] == conn._owned_created
        return identity

    worker = SimpleNamespace(enqueue_req=lambda conn: enqueue_calls.append(conn.identity), handle=handle)
    install_admission_hooks(worker, Connection, observer)
    conns = [Connection(identity, secret="never-record-this") for identity in ("d-1", "d-2")]
    for conn in conns:
        assert worker.enqueue_req(conn) is None

    def invoke(conn):
        result = worker.handle(conn)
        assert _CONNECTION.get() is None
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(invoke, conns)) == ["d-1", "d-2"]
    assert init_calls == enqueue_calls == ["d-1", "d-2"]
    assert len(events) == 2 and {e["id"] for e in events} == {"d-1", "d-2"}
    for event in events:
        t = event["connection_times"]
        assert t["connection_created"] <= t["enqueue_called"] <= t["handler_entered"]
    assert "never-record" not in str(events)
    with pytest.raises(RuntimeError, match="already installed"):
        install_admission_hooks(worker, Connection, observer)


def test_native_handler_exception_resets_admission_context():
    class Connection:
        pass

    def native(conn):
        assert _CONNECTION.get() is not None
        raise LookupError("synthetic failure")

    worker = SimpleNamespace(enqueue_req=lambda conn: 17, handle=native)
    observer = SimpleNamespace(write=lambda *args, **kwargs: None)
    install_admission_hooks(worker, Connection, observer)
    conn = Connection()
    assert worker.enqueue_req(conn) == 17
    with pytest.raises(LookupError, match="synthetic failure"):
        worker.handle(conn)
    assert _CONNECTION.get() is None
