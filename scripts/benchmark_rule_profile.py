"""Synchronous nested rule events, exclusive relative to observed direct children."""

from collections import defaultdict
from contextvars import ContextVar
from functools import wraps
from time import perf_counter


class RuleProfile:
    def __init__(self, clock=perf_counter, cpu_clock=None):
        self.clock = clock
        self.cpu_clock = cpu_clock
        self.stack = ContextVar("rule_profile_stack", default=())
        self.rules = {}

    def wrap(self, name, function):
        @wraps(function)
        def measured(*args, **kwargs):
            parents = self.stack.get()
            frame = {"rule": name, "children": defaultdict(float), "cpu_children": defaultdict(float)}
            token = self.stack.set((*parents, frame))
            start = self.clock()
            cpu_start = self.cpu_clock() if self.cpu_clock else None
            try:
                return function(*args, **kwargs)
            finally:
                elapsed = self.clock() - start
                cpu_elapsed = self.cpu_clock() - cpu_start if self.cpu_clock else None
                self.stack.reset(token)
                discounted = sum(frame["children"].values())
                exclusive = max(0.0, elapsed - discounted)
                bucket = self.rules.setdefault(name, {
                    "calls": 0, "inclusive_time": 0.0, "exclusive_time": 0.0,
                    "max_exclusive_time": 0.0, "instrumented_children": {},
                })
                bucket["calls"] += 1
                bucket["inclusive_time"] += elapsed
                bucket["exclusive_time"] += exclusive
                bucket["max_exclusive_time"] = max(bucket["max_exclusive_time"], exclusive)
                for child, seconds in frame["children"].items():
                    bucket["instrumented_children"][child] = (
                        bucket["instrumented_children"].get(child, 0.0) + seconds
                    )
                if parents:
                    parents[-1]["children"][name] += elapsed
                if self.cpu_clock:
                    cpu_exclusive = max(0.0, cpu_elapsed - sum(frame["cpu_children"].values()))
                    bucket["inclusive_thread_cpu_time"] = bucket.get("inclusive_thread_cpu_time", 0.0) + cpu_elapsed
                    bucket["exclusive_thread_cpu_time"] = bucket.get("exclusive_thread_cpu_time", 0.0) + cpu_exclusive
                    bucket["max_exclusive_thread_cpu_time"] = max(bucket.get("max_exclusive_thread_cpu_time", 0.0), cpu_exclusive)
                    child_cpu = bucket.setdefault("instrumented_children_thread_cpu", {})
                    for child, seconds in frame["cpu_children"].items():
                        child_cpu[child] = child_cpu.get(child, 0.0) + seconds
                    if parents:
                        parents[-1]["cpu_children"][name] += cpu_elapsed
        measured._publication_dependency_wrapper = measured
        measured._publication_dependency_original = function
        return measured

    def report(self):
        return [{"rule": name, **data,
                 "mean_exclusive_time": data["exclusive_time"] / data["calls"]}
                | ({"mean_exclusive_thread_cpu_time": data["exclusive_thread_cpu_time"] / data["calls"]}
                   if self.cpu_clock else {})
                for name, data in sorted(self.rules.items(),
                                        key=lambda item: item[1]["exclusive_time"], reverse=True)]
