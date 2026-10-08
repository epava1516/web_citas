"""Owned synchronous code-local monitoring; never replaces audited callables.

Python 3.12 sys.monitoring API: https://docs.python.org/3.12/library/sys.monitoring.html
Only selected ordinary functions receive start/return events. Exception unwind
is a global event filtered to those codes. No request input or frame is stored.
"""

import inspect
import sys
import threading
import time
from collections import Counter


class LocalCallMonitor:
    def __init__(self, targets):
        self.targets = {}
        for function in targets:
            function = getattr(function, "__func__", function)
            code = function.__code__
            if code.co_flags & (
                inspect.CO_GENERATOR | inspect.CO_COROUTINE | inspect.CO_ASYNC_GENERATOR
            ):
                raise ValueError("Ordinary synchronous functions only")
            label = function.__module__ + "." + function.__qualname__
            if code in self.targets and self.targets[code] != label:
                raise ValueError("Ambiguous shared code")
            self.targets[code] = label
        self.stack = []
        self.rules = {}
        self.tool = None

    def start(self, code, offset):
        if threading.get_ident() != self.thread:
            return
        self.stack.append(
            {
                "code": code,
                "wall": time.perf_counter(),
                "cpu": time.thread_time(),
                "children": Counter(),
                "cpu_children": 0.0,
            }
        )

    def end(self, code, offset, value):
        if code not in self.targets or threading.get_ident() != self.thread:
            return
        if not self.stack or self.stack[-1]["code"] is not code:
            raise RuntimeError("Unbalanced local function events")
        item = self.stack.pop()
        wall = time.perf_counter() - item["wall"]
        cpu = time.thread_time() - item["cpu"]
        exclusive = max(0.0, wall - sum(item["children"].values()))
        label = self.targets[code]
        bucket = self.rules.setdefault(
            label,
            {
                "calls": 0,
                "inclusive_time": 0.0,
                "exclusive_time": 0.0,
                "max_exclusive_time": 0.0,
                "inclusive_thread_cpu_time": 0.0,
                "exclusive_thread_cpu_time": 0.0,
                "instrumented_children": Counter(),
            },
        )
        bucket["calls"] += 1
        bucket["inclusive_time"] += wall
        bucket["exclusive_time"] += exclusive
        bucket["max_exclusive_time"] = max(bucket["max_exclusive_time"], exclusive)
        bucket["inclusive_thread_cpu_time"] += cpu
        bucket["exclusive_thread_cpu_time"] += max(0.0, cpu - item["cpu_children"])
        bucket["instrumented_children"].update(item["children"])
        if self.stack:
            self.stack[-1]["children"][label] += wall
            self.stack[-1]["cpu_children"] += cpu

    def __enter__(self):
        if self.tool is not None:
            raise RuntimeError("Monitor already active")
        monitor = sys.monitoring
        self.thread = threading.get_ident()
        self.tool = next((i for i in [4, 3, 2, 5, 1, 0] if monitor.get_tool(i) is None), None)
        if self.tool is None:
            raise RuntimeError("No unused monitoring tool ID")
        monitor.use_tool_id(self.tool, "owned-reading-stage-diagnostic")
        try:
            monitor.register_callback(self.tool, monitor.events.PY_START, self.start)
            monitor.register_callback(self.tool, monitor.events.PY_RETURN, self.end)
            monitor.register_callback(self.tool, monitor.events.PY_UNWIND, self.end)
            monitor.set_events(self.tool, monitor.events.PY_UNWIND)
            for code in self.targets:
                monitor.set_local_events(
                    self.tool, code, monitor.events.PY_START | monitor.events.PY_RETURN
                )
        except BaseException:
            self.release()
            raise
        return self

    def release(self):
        monitor = sys.monitoring
        monitor.set_events(self.tool, 0)
        for code in self.targets:
            monitor.set_local_events(self.tool, code, 0)
        for event in [monitor.events.PY_START, monitor.events.PY_RETURN, monitor.events.PY_UNWIND]:
            monitor.register_callback(self.tool, event, None)
        monitor.free_tool_id(self.tool)
        self.tool = None

    def __exit__(self, kind, *args):
        self.release()
        if self.stack and kind is None:
            raise RuntimeError("Incomplete monitored function")

    def report(self):
        return [
            {
                "rule": name,
                **values,
                "instrumented_children": dict(values["instrumented_children"]),
                "mean_exclusive_time": values["exclusive_time"] / values["calls"],
            }
            for name, values in sorted(
                self.rules.items(), key=lambda item: item[1]["exclusive_time"], reverse=True
            )
        ]
