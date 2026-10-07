"""Synchronous nested rule events, exclusive relative to observed direct children."""

from collections import defaultdict
from contextvars import ContextVar
from functools import wraps
from time import perf_counter


class RuleProfile:
    def __init__(self, clock=perf_counter):
        self.clock = clock
        self.stack = ContextVar("rule_profile_stack", default=())
        self.rules = {}

    def wrap(self, name, function):
        @wraps(function)
        def measured(*args, **kwargs):
            parents = self.stack.get()
            frame = {"children": defaultdict(float)}
            token = self.stack.set((*parents, frame))
            start = self.clock()
            try:
                return function(*args, **kwargs)
            finally:
                elapsed = self.clock() - start
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
        return measured

    def report(self):
        return [{"rule": name, **data,
                 "mean_exclusive_time": data["exclusive_time"] / data["calls"]}
                for name, data in sorted(self.rules.items(),
                                        key=lambda item: item[1]["exclusive_time"], reverse=True)]
