"""Observe process GC intervals without changing collector policy or forcing it."""

import gc
import threading
import time
from collections import Counter


class GCObserver:
    def __init__(self, rule_path=lambda: ()):
        self.rule_path = rule_path
        self.events = []
        self.pending = {}

    def __enter__(self):
        self.owner_thread = threading.get_ident()
        self.policy_before = {"enabled": gc.isenabled(), "thresholds": gc.get_threshold()}
        self.stats_before = gc.get_stats()
        gc.callbacks.append(self._callback)
        return self

    def _callback(self, phase, info):
        generation = info["generation"]
        key = (threading.get_ident(), generation)
        if phase == "start":
            self.pending[key] = (
                time.perf_counter(), time.thread_time(), tuple(self.rule_path())
            )
        elif phase == "stop":
            end_wall, end_cpu = time.perf_counter(), time.thread_time()
            start_wall, start_cpu, path = self.pending.pop(key)
            self.events.append({
                "generation": generation,
                "wall_seconds": end_wall - start_wall,
                "collector_thread_cpu_seconds": end_cpu - start_cpu,
                "on_observer_thread": key[0] == self.owner_thread,
                "active_rule_path": path,
                "collected": info["collected"],
                "uncollectable": info["uncollectable"],
            })

    def __exit__(self, *exc):
        self.stats_after = gc.get_stats()
        if self._callback in gc.callbacks:
            gc.callbacks.remove(self._callback)
        self.policy_after = {"enabled": gc.isenabled(), "thresholds": gc.get_threshold()}

    def report(self):
        wall = sum(row["wall_seconds"] for row in self.events)
        cpu = sum(row["collector_thread_cpu_seconds"] for row in self.events)
        return {
            "events": self.events,
            "calls_by_generation": dict(Counter(row["generation"] for row in self.events)),
            "wall_seconds": wall,
            "collector_thread_cpu_seconds": cpu,
            "max_wall_seconds": max((row["wall_seconds"] for row in self.events), default=0),
            "max_collector_thread_cpu_seconds": max(
                (row["collector_thread_cpu_seconds"] for row in self.events), default=0
            ),
            "collections_stats_delta": [after["collections"] - before["collections"]
                                        for before, after in zip(self.stats_before, self.stats_after, strict=True)],
            "policy_before": self.policy_before,
            "policy_after": self.policy_after,
            "unfinished_events": len(self.pending),
            "scope": "gc.callbacks start/stop intervals of this process; CPU is collector thread only. Includes callback overhead and wall scheduling, not allocations or SQL/ORM rows. Events overlap enclosing rule/request intervals; never add or subtract them as an independent phase. Policy unchanged, no gc.collect/disable/threshold mutation. Causal callback overhead not_measured; no attribution to other processes or earlier runs.",
        }
