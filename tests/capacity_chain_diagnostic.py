"""Finite test-only chain spans; original SQL, locks, fetches and checks unchanged."""
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter_ns, thread_time_ns
from unittest.mock import patch

_current = ContextVar('chain_diagnostic', default=None)


class Collector:
    def __init__(self):
        self.spans = {}
        self.stack = []
        self.head_counts = []
        self.event_rows = []
        self.source_row_counts = []
        self.failures = 0

    @contextmanager
    def span(self, name):
        item = [perf_counter_ns(), thread_time_ns(), 0, 0]
        self.stack.append(item)
        try:
            yield
        finally:
            wall, cpu = perf_counter_ns() - item[0], thread_time_ns() - item[1]
            self.stack.pop()
            value = self.spans.setdefault(name, dict(calls=0, wall_ns=0, thread_cpu_ns=0,
                                                    exclusive_wall_ns=0, exclusive_thread_cpu_ns=0))
            value['calls'] += 1
            value['wall_ns'] += wall
            value['thread_cpu_ns'] += cpu
            value['exclusive_wall_ns'] += wall - item[2]
            value['exclusive_thread_cpu_ns'] += cpu - item[3]
            if self.stack:
                self.stack[-1][2] += wall
                self.stack[-1][3] += cpu

    def snapshot(self):
        return dict(spans=self.spans, head_counts=self.head_counts, event_rows=self.event_rows,
                    source_row_counts=self.source_row_counts, failures=self.failures, semantics='inclusive_overlap; exclusive_parent_minus_children; '
                    'execute/fetch are application-driver wall/CPU, not server/network isolation; '
                    'chain residual includes Python verification, transaction and observer overhead')


class Cursor:
    def __init__(self, original, collector):
        self.original, self.collector, self.stage = original, collector, 'other'

    def __getattr__(self, name):
        return getattr(self.original, name)

    def __enter__(self):
        self.original.__enter__()
        return self

    def __exit__(self, *args):
        return self.original.__exit__(*args)

    def execute(self, query, *args, **kwargs):
        text = str(query)
        self.stage = ('head' if 'rights_evidence_locked_head' in text else
                      'events' if ('rights_evidence_link(request_id' in text or
                                   'FROM public."safety_rightsevidenceevent"' in text) else
                      'sources' if ('rights_evidence_row_hash(to_jsonb(s))' in text or
                                    ('SELECT s.id::text,' in text and 'WHERE a.request_id=%s' in text))
                      else 'other')
        with self.collector.span(self.stage + '_execute'):
            return self.original.execute(query, *args, **kwargs)

    def _fetch(self, method, *args, **kwargs):
        with self.collector.span(self.stage + '_' + method):
            result = getattr(self.original, method)(*args, **kwargs)
        if self.stage == 'events' and method == 'fetchall':
            self.collector.event_rows.append(len(result))
        if self.stage == 'sources' and method == 'fetchall':
            self.collector.source_row_counts.append(len(result))
        return result

    def fetchone(self, *args, **kwargs):
        return self._fetch('fetchone', *args, **kwargs)

    def fetchall(self, *args, **kwargs):
        return self._fetch('fetchall', *args, **kwargs)


def observed(original, name):
    @wraps(original)
    def wrapper(*args, **kwargs):
        collector = _current.get()
        if collector is None:
            return original(*args, **kwargs)
        with collector.span(name):
            try:
                result = original(*args, **kwargs)
            except BaseException:
                collector.failures += 1
                raise
            if name == 'chain':
                collector.head_counts.append(result.count)
            return result
    wrapper.__chain_diagnostic_original__ = original
    return wrapper


@contextmanager
def scope():
    from django.db import transaction
    from psycopg import Pipeline

    from apps.safety import evidence_chain

    if _current.get() is not None:
        raise RuntimeError('Nested chain diagnosis is forbidden')
    collector = Collector()
    targets = {'validate_chain': 'chain', '_source_rows': 'source_rows',
               '_source_rows_pipeline': 'source_pipeline', '_source_rows_serial': 'source_serial',
               '_runtime_is_trusted': 'runtime_trust'}
    originals = [(getattr(evidence_chain, name), phase) for name, phase in targets.items()]
    # Owned Gunicorn sync worker only: no concurrent patching or authority reuse.
    from contextlib import ExitStack
    with ExitStack() as restore:
        for module_name, module in tuple(sys.modules.items()):
            if not module_name.startswith('apps.safety.') or module is None:
                continue
            for name, value in tuple(vars(module).items()):
                for original, phase in originals:
                    if value is original:
                        restore.enter_context(patch.object(module, name, observed(original, phase)))
        database = transaction.get_connection()
        cursor = database.cursor

        def wrapped_cursor(*args, **kwargs):
            original = cursor(*args, **kwargs)
            active = _current.get()
            return Cursor(original, active) if active and active.stack else original

        restore.enter_context(patch.object(database, 'cursor', wrapped_cursor))
        restore.enter_context(patch.object(Pipeline, 'sync', observed(Pipeline.sync, 'pipeline_sync')))
        token = _current.set(collector)
        try:
            yield collector
        finally:
            _current.reset(token)
            # Restore aliases imported while the scope was active, too.
            for module_name, module in tuple(sys.modules.items()):
                if module_name.startswith('apps.safety.') and module is not None:
                    for name, value in tuple(vars(module).items()):
                        original = getattr(value, '__chain_diagnostic_original__', None)
                        if original is not None:
                            setattr(module, name, original)
