"""Bounded process-local transport; producer never writes to the logging sink."""
import json
import logging
import os
import queue
import threading
import time
import weakref

_COUNTER_LIMIT = (1 << 63) - 1
_HANDLERS = weakref.WeakSet()
_FORK_HELD = ()


def _before_fork():
    # Logging's module lock is shared with dictConfig and its own atfork hooks.
    # Never wait for a handler while holding it: shutdown may hold the handler
    # and need the module lock. A failed try releases everything before retry.
    global _FORK_HELD
    while True:
        logging._lock.acquire()
        held = []
        try:
            for handler in sorted(_HANDLERS, key=id):
                if not handler.lock.acquire(blocking=False):
                    break
                held.append(handler)
            else:
                _FORK_HELD = tuple(held)
                return
        except BaseException:
            for handler in reversed(held):
                handler.release()
            logging._lock.release()
            raise
        for handler in reversed(held):
            handler.release()
        logging._lock.release()
        time.sleep(.001)


def _after_fork_parent():
    global _FORK_HELD
    for handler in reversed(_FORK_HELD):
        handler.release()
    _FORK_HELD = ()
    logging._lock.release()


def _after_fork_child():
    # Logging's earlier child callback has already reinitialized its locks.
    global _FORK_HELD
    for handler in _FORK_HELD:
        with handler.lock:
            handler._fork_reset()
    _FORK_HELD = ()


if hasattr(os, "register_at_fork"):
    os.register_at_fork(before=_before_fork, after_in_parent=_after_fork_parent,
                        after_in_child=_after_fork_child)


class NonBlockingOperationalHandler(logging.Handler):
    """A daemon owns sink I/O; overload loses events rather than awaiting I/O.

    Counters are per process and best effort, not a durable global ledger.
    After fork discard inherited queue/thread state and duplicate the local fd.
    No descriptor flags are changed, and shutdown never joins a blocked writer.
    """

    def __init__(self, capacity=256, max_message_bytes=1024, stream_fd=2):
        super().__init__()
        if type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError("Operational queue capacity must be between 1 and 256")
        if type(max_message_bytes) is not int or not 1 <= max_message_bytes <= 1024:
            raise ValueError("Operational event size must be between 1 and 1024 bytes")
        if type(stream_fd) is not int or stream_fd < 0:
            raise ValueError("Operational stream requires a valid descriptor")
        self.capacity = capacity
        self.max_message_bytes = max_message_bytes
        self.stream_fd = stream_fd
        self._pid = os.getpid()
        self._reset_state()
        logging._lock.acquire()
        try:
            _HANDLERS.add(self)
        finally:
            logging._lock.release()

    def _reset_state(self):
        self._queue = None
        self._thread = None
        self._fd = None
        self._stop = threading.Event()
        self._dropped = self._write_errors = self._written = self._inflight = 0
        self._reported_dropped = self._reported_errors = 0

    def _fork_reset(self):
        # The before-fork protocol serialized descriptor publication/retirement.
        if self._fd is not None:
            os.close(self._fd)
        self._pid = os.getpid()
        self._reset_state()
        if self._closed:
            self._stop.set()

    def _ensure_process(self):
        if self._pid != os.getpid():
            raise RuntimeError("Operational transport fork protocol was bypassed")

    def _increment(self, field, amount=1):
        setattr(self, field, min(_COUNTER_LIMIT, getattr(self, field) + amount))

    def emit(self, record):
        self.acquire()
        try:
            self._ensure_process()
            if self._closed:
                return
            try:
                payload = self.format(record).encode("utf-8")
                if len(payload) > self.max_message_bytes:
                    self._increment("_dropped")
                    return
                if self._thread is None:
                    fd = os.dup(self.stream_fd)
                    try:
                        pending = queue.Queue(self.capacity)
                        worker = threading.Thread(
                            target=self._write_loop, args=(fd, pending, self._stop),
                            name="operational-events", daemon=True,
                        )
                        self._queue, self._fd, self._thread = pending, fd, worker
                        worker.start()
                    except Exception:
                        os.close(fd)
                        self._fd = self._thread = self._queue = None
                        raise
                self._queue.put_nowait(payload + b"\n")
            except queue.Full:
                self._increment("_dropped")
            except Exception:
                self._increment("_dropped")
                self._increment("_write_errors")
        finally:
            self.release()

    @staticmethod
    def _write(fd, payload):
        remaining = memoryview(payload)
        while remaining:
            count = os.write(fd, remaining)
            if count <= 0:
                raise OSError("Operational sink made no progress")
            remaining = remaining[count:]

    def _write_loop(self, fd, pending, stop):
        try:
            while not stop.is_set():
                try:
                    payload = pending.get(timeout=.2)
                except queue.Empty:
                    continue
                with self.lock:
                    self._inflight = 1
                try:
                    self._write(fd, payload)
                    with self.lock:
                        self._increment("_written")
                        dropped, errors = self._dropped, self._write_errors
                        gap = dropped > self._reported_dropped or errors > self._reported_errors
                    if gap:
                        marker = json.dumps({
                            "schema_version": 1, "event": "transport_gap",
                            "timestamp_seconds": int(time.time()),
                            "dropped_events": dropped, "write_errors": errors,
                            "counter_scope": "process_local_cumulative",
                        }, sort_keys=True, separators=(",", ":")).encode() + b"\n"
                        self._write(fd, marker)
                        with self.lock:
                            self._reported_dropped, self._reported_errors = dropped, errors
                except Exception:
                    with self.lock:
                        self._increment("_write_errors")
                finally:
                    with self.lock:
                        self._inflight = 0
        finally:
            with self.lock:
                os.close(fd)
                self._fd = None

    def transport_status(self):
        """Local diagnostic only; cannot be queried as another process's health."""
        with self.lock:
            self._ensure_process()
            return {
                "scope": "process_local", "capacity": self.capacity,
                "max_message_bytes": self.max_message_bytes,
                "queued": self._queue.qsize() if self._queue is not None else 0,
                "inflight": self._inflight, "dropped": self._dropped,
                "write_errors": self._write_errors, "written": self._written,
                "thread_alive": bool(self._thread and self._thread.is_alive()),
                "closed": self._closed,
            }

    def close(self):
        # Deliberately no flush/join: a blocked sink must not block shutdown.
        with self.lock:
            self._ensure_process()
            self._closed = True
            self._stop.set()
        super().close()
