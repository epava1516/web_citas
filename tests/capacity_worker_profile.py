"""Opt-in diagnostics for future object-verification threads, never domain state.

Phase durations are inclusive *execution segments*. Generator resumes count as
segments; suspension time is excluded. Nested phases and workers overlap: their
sums are not request wall time. Thread CPU includes native work during a segment
but excludes other threads. This helper never imports application modules.
"""

import threading
import time
import weakref
from contextlib import contextmanager
from pathlib import PurePath

# Fixed source/function identities; no arbitrary labels or frame data exported.
PHASES = {
    ('apps/safety/object_storage/factory.py', 'repository'): 'factory_repository',
    ('apps/safety/object_storage/factory.py', '_new_s3_client'): 'factory_new_s3_client',
    ('apps/safety/object_storage/read_clients.py', 'client'): 'read_client',
    ('apps/safety/rights_object_content.py', '_verify_object'): 'object_verify',
    ('apps/safety/object_storage/repository.py', 'verify'): 'repository_verify',
    ('apps/safety/object_storage/repository.py', 'descriptor'): 'descriptor',
    ('apps/safety/object_storage/repository.py', '_tombstone'): 'tombstone',
    ('apps/safety/object_storage/repository.py', '_verified_ciphertext'): 'ciphertext_segments',
    ('apps/safety/object_storage/repository.py', '_HashedBodyReader._fetch'): 'ciphertext_fetch',
    ('apps/safety/object_storage/repository.py', '_HashedBodyReader.finish'): 'ciphertext_finish',
    ('apps/safety/object_storage/codec.py', 'verify'): 'codec_verify',
    ('apps/safety/object_storage/codec.py', '_header'): 'header',
    ('apps/safety/object_storage/codec.py', '_authenticate_frames'): 'authenticate_frames',
}
_PHASE_FUNCTIONS = frozenset(function.rsplit('.', 1)[-1] for _, function in PHASES)
_PHASE_SUFFIXES = tuple((PurePath(filename).parts, function, phase)
                        for (filename, function), phase in PHASES.items())
MAX_WORKERS = 4
MAX_EVENTS = 100_000
MAX_SEGMENTS = 10_000
MAX_OPEN_FRAMES = 32
MAX_SECONDS = 600.0
_scope_lock = threading.Lock()


def _phase(code):
    # Anchored component suffix, not arbitrary substring or frame globals/locals.
    if code.co_name not in _PHASE_FUNCTIONS:
        return None
    parts = PurePath(code.co_filename).parts
    for suffix, function, phase in _PHASE_SUFFIXES:
        if function in (code.co_name, code.co_qualname) and parts[-len(suffix):] == suffix:
            # New setup phases identify module functions, never same-name methods.
            if phase in {'factory_repository', 'factory_new_s3_client', 'read_client'}:
                if code.co_qualname != function:
                    continue
            return phase
    return None


class Collector:
    def __init__(self):
        self._lock = threading.Lock()
        self._enabled = False
        self._status = 'inactive'
        self._reason = None
        self._workers = {}  # Weak identities only; no thread target/arguments retained.
        self._events = 0
        self._incomplete = False

    def _fail(self, reason):
        # Reasons are fixed diagnostic codes, never exception messages.
        self._incomplete = True
        self._reason = reason
        self._enabled = False

    def _callback(self, frame, event, arg):
        try:
            if not self._enabled or event not in ('call', 'return'):
                return
            thread = threading.current_thread()
            if not thread.name.startswith('rights-object-verify_'):
                return
            phase = _phase(frame.f_code)
            if phase is None:
                return
            with self._lock:
                if not self._enabled:
                    return
                if self._events >= MAX_EVENTS:
                    self._fail('event_bound')
                    return
                self._events += 1
                identity_thread = weakref.ref(thread)
                worker = self._workers.get(identity_thread)
                if worker is None:
                    if len(self._workers) >= MAX_WORKERS:
                        self._fail('worker_bound')
                        return
                    worker = {'phases': {}, 'open': {}, 'first_wall': None,
                              'last_wall': None, 'first_cpu': None, 'last_cpu': None}
                    self._workers[identity_thread] = worker
                wall, cpu = time.perf_counter(), time.thread_time()
                if worker['first_wall'] is None:
                    worker['first_wall'], worker['first_cpu'] = wall, cpu
                worker['last_wall'], worker['last_cpu'] = wall, cpu
                if (wall - worker['first_wall'] > MAX_SECONDS or
                        cpu - worker['first_cpu'] > MAX_SECONDS):
                    self._fail('timing_bound')
                    return
                # Store integer frame identities only, never frame/args/locals.
                identity = id(frame)
                if event == 'call':
                    if len(worker['open']) >= MAX_OPEN_FRAMES:
                        self._fail('frame_bound')
                        return
                    counters = worker['phases'].setdefault(
                        phase, {'segments': 0, 'wall_seconds': 0.0, 'thread_cpu_seconds': 0.0})
                    if counters['segments'] >= MAX_SEGMENTS:
                        self._fail('segment_bound')
                        return
                    counters['segments'] += 1
                    worker['open'][identity] = (phase, wall, cpu)
                else:
                    started = worker['open'].pop(identity, None)
                    if started is None:
                        self._fail('unmatched_return')
                        return
                    name, start_wall, start_cpu = started
                    counters = worker['phases'][name]
                    counters['wall_seconds'] += max(0.0, wall - start_wall)
                    counters['thread_cpu_seconds'] += max(0.0, cpu - start_cpu)
                    if (counters['wall_seconds'] > MAX_SECONDS or
                            counters['thread_cpu_seconds'] > MAX_SECONDS):
                        counters['wall_seconds'] = min(MAX_SECONDS, counters['wall_seconds'])
                        counters['thread_cpu_seconds'] = min(MAX_SECONDS, counters['thread_cpu_seconds'])
                        self._fail('timing_bound')
        except BaseException:
            # A diagnostic callback must never replace the worker's exception.
            self._fail('callback_failure')

    def snapshot(self):
        with self._lock:
            workers = []
            for ordinal, worker in enumerate(self._workers.values(), 1):
                workers.append({
                    'worker': ordinal,
                    'observed_wall_seconds': 0.0 if worker['first_wall'] is None else min(
                        MAX_SECONDS, max(0.0, worker['last_wall'] - worker['first_wall'])),
                    'observed_thread_cpu_seconds': 0.0 if worker['first_cpu'] is None else min(
                        MAX_SECONDS, max(0.0, worker['last_cpu'] - worker['first_cpu'])),
                    'phases': {name: dict(values) for name, values in worker['phases'].items()},
                })
            return {'status': self._status, 'incomplete': self._incomplete,
                    'reason': self._reason, 'events': self._events, 'workers': workers,
                    'timing_semantics': 'inclusive_execution_segments_overlap_not_request_wall'}

    def _finish(self):
        with self._lock:
            self._enabled = False
            if any(worker['open'] for worker in self._workers.values()):
                self._incomplete = True
                self._reason = self._reason or 'workers_not_drained'
            for worker in self._workers.values():
                worker['open'].clear()
            self._status = 'incomplete' if self._incomplete else 'complete'


@contextmanager
def scope(*, enabled=True):
    """Only future matching threads; caller must join them before scope exit.

    Existing profile hooks and concurrent/nested scopes decline. No setprofile
    is performed when disabled/declined. Never installs on already-live threads.
    """
    collector = Collector()
    if not enabled:
        yield collector
        return
    if not _scope_lock.acquire(blocking=False):
        collector._status, collector._reason = 'declined', 'concurrent_scope'
        yield collector
        return
    previous = None
    installed = False
    try:
        previous = threading.getprofile()
        if previous is not None:
            collector._status, collector._reason = 'declined', 'existing_hook'
        else:
            collector._enabled, collector._status = True, 'active'
            try:
                threading.setprofile(collector._callback)
                installed = True
            except BaseException:
                collector._fail('hook_install_failure')
                collector._status = 'incomplete'
        yield collector
    finally:
        try:
            if installed or threading.getprofile() == collector._callback:
                # Preserve another owner's replacement instead of clobbering it.
                if threading.getprofile() == collector._callback:
                    try:
                        threading.setprofile(previous)
                    except BaseException:
                        collector._fail('hook_restore_failure')
                else:
                    collector._fail('hook_replaced')
                collector._finish()
        finally:
            _scope_lock.release()
