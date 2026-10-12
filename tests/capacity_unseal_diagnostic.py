"""Test-only unseal decomposition. Never reuse decrypt, parsed data or authority.

Plaintext retained only in a bounded scope for full-value repetition checks;
exports contain numeric counters, never content, hashes, tokens or keys.
"""
import json
import sys
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from time import perf_counter_ns, thread_time_ns

from apps.safety import crypto

_current = ContextVar('capacity_unseal_diagnostic', default=None)
_lock = threading.Lock()
MAX_BYTES = 32 * 1024 * 1024
MAX_ENTRIES = 128


def _timed(call):
    wall, cpu = perf_counter_ns(), thread_time_ns()
    result = call()
    return result, {'wall_ns': perf_counter_ns() - wall, 'cpu_ns': thread_time_ns() - cpu}


class Collector:
    def __init__(self):
        self.thread = threading.get_ident()
        self.retained = []
        self.retained_bytes = 0
        self.rows = []
        self.calls = 0
        self.failures = 0
        self.untracked_calls = 0
        self.peak_bytes = 0
        self.alias_count = 0

    def observe(self, payload):
        self.calls += 1
        try:
            plain, decrypt = _timed(lambda: crypto.cipher().decrypt(payload.encode()))
            text, decode = _timed(plain.decode)
            result, parse = _timed(lambda: json.loads(text))
        except BaseException:
            self.failures += 1
            raise
        # Compare actual independent decrypt outputs. No digest or identity shortcut.
        wall, cpu = perf_counter_ns(), thread_time_ns()
        index = next((i for i, previous in enumerate(self.retained)
                      if len(previous) == len(plain) and previous == plain), None)
        compare = {'wall_ns': perf_counter_ns() - wall, 'cpu_ns': thread_time_ns() - cpu}
        if index is None:
            if (len(self.retained) >= MAX_ENTRIES
                    or self.retained_bytes + len(plain) > MAX_BYTES):
                self.untracked_calls += 1
                return result
            index = len(self.retained)
            self.retained.append(plain)
            self.retained_bytes += len(plain)
            self.peak_bytes = max(self.peak_bytes, self.retained_bytes)
            self.rows.append({'group': index + 1, 'bytes': len(plain), 'calls': 0,
                              'repeat_parse_cpu_ns': 0, 'repeat_parse_wall_ns': 0,
                              'decrypt': {'wall_ns': 0, 'cpu_ns': 0},
                              'decode': {'wall_ns': 0, 'cpu_ns': 0},
                              'parse': {'wall_ns': 0, 'cpu_ns': 0},
                              'compare': {'wall_ns': 0, 'cpu_ns': 0},
                              'copy_probe': {'wall_ns': 0, 'cpu_ns': 0}})
        row = self.rows[index]
        if row['calls']:
            row['repeat_parse_cpu_ns'] += parse['cpu_ns']
            row['repeat_parse_wall_ns'] += parse['wall_ns']
            # Probe only: discard copy; caller always receives fresh parsed result.
            cloned, cost = _timed(lambda: deepcopy(result))
            del cloned
            for clock in cost:
                row['copy_probe'][clock] += cost[clock]
        row['calls'] += 1
        for stage, cost in [('decrypt', decrypt), ('decode', decode),
                            ('parse', parse), ('compare', compare)]:
            for clock in cost:
                row[stage][clock] += cost[clock]
        return result

    def snapshot(self):
        return {'status': 'DIAGNOSTIC_NOT_CAPACITY', 'calls': self.calls,
                'failures': self.failures, 'untracked_calls': self.untracked_calls,
                'peak_retained_plaintext_bytes': self.peak_bytes,
                'alias_count': self.alias_count, 'groups': deepcopy(self.rows),
                'scope': 'thread_request_local_full_plaintext_equality_no_reuse',
                'limits': {'bytes': MAX_BYTES, 'entries': MAX_ENTRIES},
                'semantics': 'decode/parse/decrypt disjoint; compare/copy observer overhead; no HTTP p95'}


@contextmanager
def scope():
    """Wrap loaded safety aliases; reject overlap; always restore and clear bytes."""
    if not _lock.acquire(blocking=False):
        raise RuntimeError('Unseal diagnostic scope already active')
    collector = Collector()
    original = crypto.unseal
    plan = []
    token = None

    @wraps(original)
    def observed(payload):
        active = _current.get()
        if active is None or threading.get_ident() != active.thread:
            return original(payload)
        return active.observe(payload)

    try:
        for name, module in tuple(sys.modules.items()):
            if name == 'apps.safety.crypto' or name.startswith('apps.safety.'):
                for attribute, value in tuple(vars(module).items()):
                    if value is original:
                        plan.append((module, attribute))
        if len(plan) > 128:
            raise RuntimeError('Unseal diagnostic alias bound exceeded')
        collector.alias_count = len(plan)
        token = _current.set(collector)
        for module, attribute in plan:
            setattr(module, attribute, observed)
        yield collector
    finally:
        # Also restore aliases imported while the scope was active.
        for name, module in tuple(sys.modules.items()):
            if name == 'apps.safety.crypto' or name.startswith('apps.safety.'):
                for attribute, value in tuple(vars(module).items()):
                    if value is observed:
                        setattr(module, attribute, original)
        if token is not None:
            _current.reset(token)
        collector.retained.clear()
        collector.retained_bytes = 0
        _lock.release()
