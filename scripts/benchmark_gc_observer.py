"""Observe process GC intervals without changing collector policy or forcing it."""

import gc
import threading
import time
from collections import Counter


class GCObserver:
    def __init__(self, rule_path=lambda: (), monotonic_clock=None):
        self.rule_path = rule_path
        self.monotonic_clock = monotonic_clock
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
                time.perf_counter(), time.thread_time(), tuple(self.rule_path()),
                self.monotonic_clock() if self.monotonic_clock else None,
            )
        elif phase == "stop":
            end_wall, end_cpu = time.perf_counter(), time.thread_time()
            end_monotonic = self.monotonic_clock() if self.monotonic_clock else None
            start_wall, start_cpu, path, start_monotonic = self.pending.pop(key)
            event = {
                "generation": generation,
                "wall_seconds": end_wall - start_wall,
                "collector_thread_cpu_seconds": end_cpu - start_cpu,
                "on_observer_thread": key[0] == self.owner_thread,
                "active_rule_path": path,
                "collected": info["collected"],
                "uncollectable": info["uncollectable"],
            }
            if self.monotonic_clock:
                event.update(monotonic_start=start_monotonic, monotonic_end=end_monotonic)
            self.events.append(event)

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


def generator_gc_overlap(events, rows, origin):
    """Intersect emission delays with observed GC intervals; overlap isn't cause.

    Merge overlapping intervals first, so an interval is never counted twice.
    Both timestamps must explicitly use time.monotonic (the standard loop clock).
    """
    intervals = sorted((event["monotonic_start"] - origin,
                        event["monotonic_end"] - origin) for event in events)
    merged = []
    for start, end in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    delays = []
    for row in rows:
        if row["emitted_at"] is None:
            continue
        start, end = row["scheduled_at"], row["emitted_at"]
        overlap = sum(max(0, min(end, stop) - max(start, begin)) for begin, stop in merged)
        delays.append({"id": row["id"], "delay_seconds": end - start,
                       "gc_overlap_seconds": overlap})
    return {
        "emitted_population": len(delays),
        "requests_with_gc_overlap": sum(row["gc_overlap_seconds"] > 0 for row in delays),
        "largest_delay": max(delays, key=lambda row: row["delay_seconds"], default=None),
        "overlapping_delays": [row for row in delays if row["gc_overlap_seconds"] > 0],
        "scope": "Union of client GC intervals intersected with scheduled-to-emitted delays, same monotonic origin. Overlap measured, not sole causal attribution; CPU/scheduling/network/other processes remain separate. GC events before the arrival clock or during drain do not imply arrival delay. No thresholds or collector policy changed.",
    }
