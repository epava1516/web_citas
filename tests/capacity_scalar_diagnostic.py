"""Test-only consumer spans and separate structural census; no candidate or profiler."""

import gc
import hashlib
import sys
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from functools import wraps
from time import perf_counter_ns, thread_time_ns
from unittest.mock import patch

from tests.capacity_chain_diagnostic import Collector

_active = ContextVar("scalar_consumer_diagnostic", default=None)


def statistics(rows):
    """Independent, untimed census of JSON-shaped rows. Never retain leaf values."""
    result = dict(rows=len(rows), nodes=0, leaves=0, containers=0, empty_containers=0,
                  max_depth=0, sum_leaf_depth=0, escaped_keys=0, sum_path_chars=0,
                  max_path_chars=0, leaf_types={})
    for row in rows:
        stack = [(row, "", 0)]
        while stack:
            value, prefix, depth = stack.pop()
            if result["nodes"] >= 1_000_000 or depth > 2048:
                raise ValueError("Diagnostic census limit reached")
            result["nodes"] += 1
            result["max_depth"] = max(result["max_depth"], depth)
            if isinstance(value, (dict, list)):
                result["containers"] += 1
                result["empty_containers"] += not bool(value)
                if isinstance(value, dict):
                    children = []
                    for key, child in value.items():
                        if not isinstance(key, str):
                            raise ValueError("Census requires JSON object keys")
                        result["escaped_keys"] += "~" in key or "/" in key
                        path = prefix + "/" + key.replace("~", "~0").replace("/", "~1")
                        children.append((child, path, depth + 1))
                else:
                    children = [(child, prefix + "/" + str(index), depth + 1)
                                for index, child in enumerate(value)]
                stack.extend(reversed(children))
            else:
                result["leaves"] += 1
                result["sum_leaf_depth"] += depth
                result["sum_path_chars"] += len(prefix)
                result["max_path_chars"] = max(result["max_path_chars"], len(prefix))
                kind = type(value).__name__
                result["leaf_types"][kind] = result["leaf_types"].get(kind, 0) + 1
    return result


def source_census(source):
    from apps.safety.fast_canonical import canonical_bytes
    from apps.safety.rights_copy_inspection import SECTIONS

    return dict(sha256=hashlib.sha256(canonical_bytes(source)).hexdigest(),
                datasets={name: statistics(reader(source)) for name, reader in SECTIONS.items()})


def counted_leaves(original, module_name, collector):
    """Count only aliases at consumers; original recursive definition remains untouched."""
    @wraps(original)
    def wrapper(*args, **kwargs):
        iterator = original(*args, **kwargs)
        frame = sys._getframe(1)
        site = f"{module_name}:{frame.f_code.co_name}:{frame.f_lineno}"
        del frame
        counts = collector.sites.setdefault(site, dict(calls=0, leaves_yielded=0))
        counts["calls"] += 1
        try:
            for leaf in iterator:
                counts["leaves_yielded"] += 1
                yield leaf
        finally:
            iterator.close()
    wrapper.__scalar_diagnostic_original__ = original
    return wrapper


def observed(original, name, collector):
    @wraps(original)
    def wrapper(*args, **kwargs):
        if collector.mode == "spans":
            with collector.span(name):
                return original(*args, **kwargs)
        collector.calls[name] += 1
        result = original(*args, **kwargs)
        if name == "source_copy":
            collector.source = source_census(result)
        if name == "compile_coverage":
            source, assessment = args[:2]
            from apps.safety.rights_copy_inspection import SECTIONS

            collector.compile_rows = {
                dataset: statistics(reader(source)) for dataset, reader in SECTIONS.items()
                if assessment[dataset]["status"] != "excluded"
            }
        return result
    wrapper.__scalar_diagnostic_original__ = original
    return wrapper


@contextmanager
def scope(mode):
    from apps.safety import (
        rights_access_coverage,
        rights_exports,
        rights_portability_catalog,
        rights_portability_coverage,
        rights_portability_coverage_page,
        rights_portability_coverage_pages,
        rights_portability_coverage_read_gate,
        rights_portability_selection,
    )

    if _active.get() is not None or mode not in {"spans", "count"}:
        raise RuntimeError("Invalid or nested scalar diagnosis")
    targets = [
        (rights_exports.source_copy, "source_copy"),
        (rights_portability_coverage.compile_coverage, "compile_coverage"),
        (rights_portability_selection.project_selected, "project_selected"),
        (rights_portability_coverage_page.coverage_page, "coverage_page"),
        (rights_portability_coverage_read_gate.required_pages, "required_pages"),
        (rights_portability_catalog.inspect_catalog, "inspect_catalog"),
        (rights_portability_coverage_pages.prepare_page, "prepare_page"),
        (rights_access_coverage.compile_coverage, "access_compile_coverage"),
    ]
    collector = Collector()
    collector.mode, collector.sites, collector.source = mode, {}, None
    collector.compile_rows = None
    collector.calls = {name: 0 for _, name in targets}
    # Zero entries mean the consumer was not observed, not an inferred zero-cost leaf walk.
    collector.spans = {name: dict(calls=0, wall_ns=0, thread_cpu_ns=0,
                                 exclusive_wall_ns=0, exclusive_thread_cpu_ns=0)
                       for _, name in targets}
    aliases = [(module, attr, observed(function, name, collector))
               for module_name, module in list(sys.modules.items())
               if module_name.startswith("apps.safety.") and module is not None
               for attr, value in list(vars(module).items())
               for function, name in targets if value is function]
    token = _active.set(collector)
    try:
        with ExitStack() as stack:
            for module, attr, wrapper in aliases:
                stack.enter_context(patch.object(module, attr, wrapper))
            if mode == "count":
                # Do not patch catalog.scalar_fields: its recursive global name stays original.
                for module in (rights_portability_coverage, rights_portability_coverage_page,
                               rights_portability_coverage_pages,
                               rights_portability_coverage_read_gate, rights_access_coverage):
                    stack.enter_context(patch.object(module, "scalar_fields", counted_leaves(
                        rights_portability_catalog.scalar_fields, module.__name__, collector)))
                stack.enter_context(patch.object(rights_portability_coverage, "_scalar_paths", counted_leaves(
                    rights_portability_coverage._scalar_paths, rights_portability_coverage.__name__, collector)))
            try:
                yield collector
            finally:
                for module_name, module in list(sys.modules.items()):
                    if module_name.startswith("apps.safety.") and module is not None:
                        for attr, value in list(vars(module).items()):
                            original = getattr(value, "__scalar_diagnostic_original__", None)
                            if original is not None:
                                setattr(module, attr, original)
    finally:
        _active.reset(token)


def benchmark(rows, pointer_inputs):
    """Original code A/A only; preparation, assertions and GC census outside timers."""
    from apps.safety.rights_portability_catalog import scalar_fields
    from apps.safety.rights_portability_selection import pointer_value

    operations = {
        "path_sets": lambda: sum(len({leaf["path"] for leaf in scalar_fields(row)}) for row in rows),
        "leaf_count": lambda: sum(1 for row in rows for _ in scalar_fields(row)),
        "selected_pointers": lambda: sum(1 for row, path in pointer_inputs
                                        for _ in (pointer_value(row, path),)),
    }
    samples = []
    for name, operation in operations.items():
        expected = operation()
        assert operation() == expected  # two declared warmups, discarded
        for label in "ABBA" * 5:  # ten samples per label, both labels are the same original
            before = gc.get_stats()
            wall, cpu = perf_counter_ns(), thread_time_ns()
            result = operation()
            cpu, wall = thread_time_ns() - cpu, perf_counter_ns() - wall
            after = gc.get_stats()
            assert result == expected
            samples.append(dict(operation=name, label=label, wall_ns=wall, thread_cpu_ns=cpu,
                                result_count=result,
                                gc_collections=[b["collections"] - a["collections"]
                                                for a, b in zip(before, after, strict=True)]))
    return dict(samples=samples, gc_enabled=gc.isenabled(), gc_thresholds=gc.get_threshold(),
                semantics="Original A/A, includes consuming sets/counts or pointer-value discard; "
                          "no profiler, no database reads, no candidate or request-saving estimate")
