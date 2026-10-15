"""Own diagnostic only: connection lifecycle timestamps, no payload or SQL.

Enqueue-call to handler-entry includes native parser setup/submission overhead;
it is not an exact exclusive executor queue timer. Original behavior is delegated.
"""
from contextvars import ContextVar
from functools import wraps
from time import monotonic

from scripts.benchmark_resource_observer import worker_exit  # noqa: F401

_CONNECTION = ContextVar("owned_connection_timestamps", default=None)


def install_admission_hooks(worker, connection_class, observer):
    if getattr(connection_class, "_owned_admission_installed", False):
        raise RuntimeError("Admission observation already installed")
    original_init = connection_class.__init__
    original_enqueue, original_handle, original_write = worker.enqueue_req, worker.handle, observer.write

    @wraps(original_init)
    def init(conn, *args, **kwargs):
        conn._owned_created = monotonic()
        original_init(conn, *args, **kwargs)

    @wraps(original_enqueue)
    def enqueue(conn):
        conn._owned_enqueue_called = monotonic()
        return original_enqueue(conn)

    @wraps(original_handle)
    def handle(conn):
        times = {"connection_created": conn._owned_created,
                 "enqueue_called": conn._owned_enqueue_called,
                 "handler_entered": monotonic()}
        token = _CONNECTION.set(times)
        try:
            return original_handle(conn)
        finally:
            _CONNECTION.reset(token)

    def write(state, event, **values):
        if event == "wsgi_start":
            values["connection_times"] = _CONNECTION.get()
        return original_write(state, event, **values)

    connection_class.__init__ = init
    connection_class._owned_admission_installed = True
    worker.enqueue_req, worker.handle, observer.write = enqueue, handle, write


def post_worker_init(worker):
    from gunicorn.workers.gthread import TConn, ThreadWorker

    from scripts.benchmark_resource_observer import post_worker_init as resource_init

    if not isinstance(worker, ThreadWorker):
        raise RuntimeError("Explicit threaded diagnostic required")
    resource_init(worker)  # Checks own synthetic DB before installing any hooks.
    install_admission_hooks(worker, TConn, worker._benchmark_observer)
