"""Explicit listing diagnostics; no profile hooks, application imports or data.

Wall/CPU counters are inclusive and overlap. Four pages are sequential calls
inside one batch, never four HTTP requests. Generator/contextmanager/coroutine
phases are deliberately omitted. SQL durations belong to the innermost span.
"""

import inspect
import sys
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter_ns, thread_time_ns

PHASE_TARGETS = {
    'batch': ('apps.safety.rights_portability_coverage_batch', 'inspect_batch'),
    'page': ('apps.safety.rights_portability_coverage_inspection', 'inspect_page'),
    'record': ('apps.safety.rights_portability_selection_review', 'record'),
    'baseline': ('apps.safety.rights_portability_coverage_pages', 'baseline_body'),
    'unseal': ('apps.safety.crypto', 'unseal'),
    'source': ('apps.safety.rights_exports', 'source_copy'),
    'compile': ('apps.safety.rights_portability_coverage', 'compile_coverage'),
    'authorize': ('apps.safety.rights_portability_review', 'authorize'),
    'validate_selection': ('apps.safety.rights_portability_selection_review', 'validate_approved_selection'),
    'validate_assessment': ('apps.safety.rights_portability_review', 'validate_approved_assessment'),
    'assessment_evidence': ('apps.safety.rights_portability', 'validate_assessment_evidence'),
    'selection_evidence': ('apps.safety.rights_portability_selection_store', 'validate_selection_evidence'),
    'audited_images': ('apps.safety.rights_portability_images', 'audited_images'),
    'checked_images': ('apps.safety.rights_portability_images', 'checked_images'),
    'read_image_blob': ('apps.safety.rights_exports', '_read_image_blob'),
    'content_digest': ('apps.safety.rights_operation_content_digests', 'content_digest'),
    'batch_projection': ('apps.safety.rights_portability_batch_projection', 'project'),
}
MODULES = tuple(dict.fromkeys(tuple(module for module, _ in PHASE_TARGETS.values()) + (
    'apps.safety.rights_inspection_source',
    'apps.safety.rights_portability_coverage_review_views',
    'apps.safety.rights_portability_batch_projection',
)))
MAX_ALIASES = 128
MAX_CALLS = 100_000
MAX_DEPTH = 32
MAX_SQL = 100_000
MAX_NS = 600_000_000_000
_current = ContextVar('capacity_listing_phase_spans', default=None)
_install_lock = threading.Lock()


def _counter():
    return {'calls': 0, 'wall_ns': 0, 'thread_cpu_ns': 0,
            'sql_count': 0, 'sql_wall_ns': 0, 'sql_thread_cpu_ns': 0}


class Collector:
    def __init__(self):
        self.status = 'inactive'
        self.reason = None
        self.incomplete = False
        self._thread = threading.get_ident()
        self._phases = {phase: _counter() for phase in PHASE_TARGETS}
        self._pages = [{phase: _counter() for phase in PHASE_TARGETS} for _ in range(4)]
        self._page_count = 0
        self._page = None
        self._stack = []
        self._sql_count = 0
        self._sql_totals = {'wall_ns': 0, 'thread_cpu_ns': 0}
        self._omitted = []
        self._missing = []

    def fail(self, reason):
        self.incomplete = True
        self.reason = self.reason or reason

    def _add(self, counter, name, amount):
        value = counter[name] + max(0, amount)
        if value > MAX_NS:
            self.fail('time_bound')
        counter[name] = min(MAX_NS, value)

    def begin(self, phase):
        if self.incomplete:
            return None
        if len(self._stack) >= MAX_DEPTH or self._phases[phase]['calls'] >= MAX_CALLS:
            self.fail('call_bound')
            return None
        previous_page = self._page
        if phase == 'page':
            if self._page_count >= 4 or any(item[0] == 'page' for item in self._stack):
                self.fail('page_bound_or_overlap')
                return None
            self._page = self._page_count
            self._page_count += 1
        started = (phase, self._page, perf_counter_ns(), thread_time_ns(), previous_page)
        self._stack.append(started)
        self._phases[phase]['calls'] += 1
        if self._page is not None:
            self._pages[self._page][phase]['calls'] += 1
        return started

    def end(self, started):
        if started is None:
            return
        try:
            phase, page, wall, cpu, previous_page = started
            elapsed, cpu_elapsed = perf_counter_ns() - wall, thread_time_ns() - cpu
            self._add(self._phases[phase], 'wall_ns', elapsed)
            self._add(self._phases[phase], 'thread_cpu_ns', cpu_elapsed)
            if page is not None:
                self._add(self._pages[page][phase], 'wall_ns', elapsed)
                self._add(self._pages[page][phase], 'thread_cpu_ns', cpu_elapsed)
        finally:
            if self._stack and self._stack[-1] is started:
                self._stack.pop()
                self._page = started[4]
            else:
                self.fail('span_order')

    def sql(self, execute, sql, params, many, context):
        collector = _active()
        if collector is not self or self.incomplete:
            return execute(sql, params, many, context)
        started = None
        try:
            if self._sql_count >= MAX_SQL:
                self.fail('sql_bound')
            else:
                self._sql_count += 1
                started = (perf_counter_ns(), thread_time_ns(),
                           self._stack[-1][0] if self._stack else None, self._page)
        except BaseException:
            self.fail('observer_failure')
        try:
            return execute(sql, params, many, context)
        finally:
            if started is not None:
                try:
                    wall, cpu, phase, page = started
                    elapsed, cpu_elapsed = perf_counter_ns() - wall, thread_time_ns() - cpu
                    self._add(self._sql_totals, 'wall_ns', elapsed)
                    self._add(self._sql_totals, 'thread_cpu_ns', cpu_elapsed)
                    if phase is not None:
                        for counters in [self._phases[phase]] + (
                                [self._pages[page][phase]] if page is not None else []):
                            counters['sql_count'] += 1
                            self._add(counters, 'sql_wall_ns', elapsed)
                            self._add(counters, 'sql_thread_cpu_ns', cpu_elapsed)
                except BaseException:
                    self.fail('observer_failure')

    def snapshot(self):
        return {'status': self.status, 'incomplete': self.incomplete, 'reason': self.reason,
                'phases': {name: dict(value) for name, value in self._phases.items()},
                'pages': [{name: dict(value) for name, value in page.items()}
                          for page in self._pages[:self._page_count]],
                'sql_count': self._sql_count, 'sql_totals': dict(self._sql_totals), 'omitted_phases': list(self._omitted),
                'missing_phases': list(self._missing),
                'timing_semantics': 'inclusive_overlapping_not_summed_request_wall',
                'sql_attribution': 'innermost_span_only'}


def _active():
    collector = _current.get()
    if collector is None or collector._thread != threading.get_ident():
        return None
    return collector


def _wrapper(original, phase):
    @wraps(original)
    def observed(*args, **kwargs):
        collector = _active()
        if collector is None:
            return original(*args, **kwargs)
        started = None
        try:
            started = collector.begin(phase)
        except BaseException:
            collector.fail('observer_failure')
        try:
            return original(*args, **kwargs)
        finally:
            try:
                collector.end(started)
            except BaseException:
                collector.fail('observer_failure')
    return observed


def _plan(targets, collector):
    if not isinstance(targets, dict) or any(phase not in PHASE_TARGETS for phase in targets):
        raise ValueError('Invalid diagnostic target whitelist')
    originals = []
    for phase, original in targets.items():
        if not callable(original):
            raise ValueError('Invalid diagnostic target callable')
        unwrapped = inspect.unwrap(original)
        if (inspect.isgeneratorfunction(unwrapped) or inspect.iscoroutinefunction(unwrapped)
                or inspect.isasyncgenfunction(unwrapped)):
            collector._omitted.append(phase)
            continue
        if any(original is existing for existing, _, _ in originals):
            raise ValueError('Ambiguous diagnostic target')
        originals.append((original, phase, _wrapper(original, phase)))
    plan = []
    for module_name in MODULES:
        module = sys.modules.get(module_name)
        if module is None:
            continue
        for name, current in tuple(vars(module).items()):
            for original, phase, wrapper in originals:
                if current is original:
                    plan.append((module, name, original, wrapper))
                    if len(plan) > MAX_ALIASES:
                        raise ValueError('Diagnostic alias bound')
    for original, phase, wrapper in originals:
        if not any(installed_original is original for _, _, installed_original, _ in plan):
            collector._missing.append(phase)
            collector.fail('missing_alias')
    return plan


@contextmanager
def scope(*, enabled=True, targets=None, sql_context=None):
    """Root supplies connection.execute_wrapper; no project imports are needed.

    Targets map fixed phase names to already-loaded callable identities. Every
    identity alias in the fixed module list is wrapped. Unmarked other threads
    bypass observation. Concurrent/nested scopes decline without blocking.
    SQL providers must support __exit__ following partial __enter__ failure;
    ordinary connection.execute_wrapper has this standard cleanup behavior.
    """
    collector = Collector()
    if not enabled:
        yield collector
        return
    if not _install_lock.acquire(blocking=False):
        collector.status, collector.reason = 'declined', 'concurrent_scope'
        yield collector
        return
    installed, token, sql_manager = [], None, None
    try:
        try:
            if targets is None:
                collector._missing = [phase for phase, (module, name) in PHASE_TARGETS.items()
                                      if module not in sys.modules or
                                      not hasattr(sys.modules[module], name)]
                if any(phase in ('batch', 'page') for phase in collector._missing):
                    collector.fail('missing_required_target')
                targets = {phase: getattr(sys.modules[module], name)
                           for phase, (module, name) in PHASE_TARGETS.items()
                           if module in sys.modules and hasattr(sys.modules[module], name)}
            plan = _plan(targets, collector)
            for module, name, original, wrapper in plan:
                setattr(module, name, wrapper)
                installed.append((module, name, original, wrapper))
            token = _current.set(collector)
            collector.status = 'active'
            if sql_context is not None:
                # Register cleanup before entry: a custom provider may install
                # instrumentation and then raise. It must make __exit__ safe
                # after partial entry, just as after successful entry.
                sql_manager = sql_context(collector.sql)
                sql_manager.__enter__()
        except BaseException:
            collector.fail('installation_failure')
        yield collector
    finally:
        exception = sys.exc_info()
        try:
            if sql_manager is not None:
                try:
                    sql_manager.__exit__(*exception)
                except BaseException:
                    collector.fail('sql_restore_failure')
            if token is not None:
                _current.reset(token)
            for module, name, original, wrapper in reversed(installed):
                try:
                    if getattr(module, name, None) is wrapper:
                        setattr(module, name, original)
                    else:
                        collector.fail('foreign_replacement')
                except BaseException:
                    collector.fail('restore_failure')
            if collector._stack:
                collector.fail('unclosed_spans')
            collector._stack.clear()
            collector.status = 'incomplete' if collector.incomplete else 'complete'
        finally:
            _install_lock.release()
