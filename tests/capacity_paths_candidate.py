"""Finite path-only A/B controls; no authority caching or production switches."""
import ast
import gc
import inspect
import sys
import tracemalloc
from contextlib import ExitStack, contextmanager
from functools import lru_cache
from statistics import median
from time import perf_counter_ns, thread_time_ns
from unittest.mock import patch


@lru_cache(maxsize=1)
def original_compiler():
    from apps.safety import rights_portability_coverage as coverage
    tree = ast.parse(inspect.getsource(coverage.compile_coverage))
    replacements = 0
    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'paths'):
            node.value = ast.parse('paths = {item["path"] for item in scalar_fields(row)}').body[0].value
            replacements += 1
    assert replacements == 1
    ast.fix_missing_locations(tree)
    namespace = dict(vars(coverage))
    exec(compile(tree, '<original-coverage-paths>', 'exec'), namespace)
    return namespace['compile_coverage']


@contextmanager
def variant(mode):
    from apps.safety import rights_portability_coverage as coverage
    assert mode in {'original', 'paths'}
    target = coverage.compile_coverage
    baseline = original_compiler()
    replacement = baseline if mode == 'original' else target
    aliases = [(module, attr) for name, module in list(sys.modules.items())
               if name.startswith('apps.safety.') and module is not None
               for attr, value in list(vars(module).items()) if value is target]
    try:
        with ExitStack() as stack:
            for module, attr in aliases:
                stack.enter_context(patch.object(module, attr, replacement))
            yield
    finally:
        # Also restore aliases imported during a request; both modes scan equally.
        for name, module in list(sys.modules.items()):
            if name.startswith('apps.safety.') and module is not None:
                for attr, value in list(vars(module).items()):
                    if replacement is not target and value is replacement:
                        setattr(module, attr, target)


def pure_benchmark(rows):
    from apps.safety.rights_portability_catalog import scalar_fields
    from apps.safety.rights_portability_paths import _scalar_paths
    def original():
        return sum(len({leaf['path'] for leaf in scalar_fields(row)}) for row in rows)
    def paths():
        return sum(len({path for path in _scalar_paths(row)}) for row in rows)
    operations = {'original': original, 'paths': paths}
    expected = original()
    assert paths() == expected
    for operation in operations.values():
        assert operation() == operation() == expected
    samples = []
    for round_number in range(10):
        for mode in ('original', 'paths', 'paths', 'original'):
            before = gc.get_stats()
            wall, cpu = perf_counter_ns(), thread_time_ns()
            result = operations[mode]()
            cpu, wall = thread_time_ns()-cpu, perf_counter_ns()-wall
            after = gc.get_stats()
            assert result == expected
            samples.append(dict(mode=mode, round=round_number, wall_ns=wall, cpu_ns=cpu,
                                gc_collections=[b['collections']-a['collections']
                                                for a,b in zip(before,after,strict=True)]))
    # Distinct experiment, no allocation profiler in time samples. Peak live bytes
    # do NOT count cumulative transient dictionary allocations.
    memory = []
    assert not tracemalloc.is_tracing()
    for mode in ('original','paths')*5:
        tracemalloc.start()
        try:
            assert operations[mode]() == expected
            current, peak = tracemalloc.get_traced_memory()
            memory.append(dict(mode=mode, current_bytes=current, peak_bytes=peak))
        finally:
            tracemalloc.stop()
    criteria = {}
    for clock in ('wall_ns','cpu_ns'):
        pairs = []
        for index in range(0,40,2):
            pair = {sample['mode']:sample[clock] for sample in samples[index:index+2]}
            pairs.append(pair['original']-pair['paths'])
        blocks = [median(pairs[index:index+5]) for index in range(0,20,5)]
        criteria[clock] = dict(paired_wins=sum(delta>0 for delta in pairs),
                               median_paired_saving_ns=median(pairs),
                               chronological_block_medians=blocks,
                               passes=sum(delta>0 for delta in pairs)>=15 and all(b>0 for b in blocks))
    peaks = {mode: median(v['peak_bytes'] for v in memory if v['mode']==mode) for mode in operations}
    return dict(samples=samples,memory=memory,peaks=peaks,criteria=criteria,
                passes=all(v['passes'] for v in criteria.values())
                       and peaks['paths']<=peaks['original']*1.05+1024,
                leaves=expected, gc_enabled=gc.isenabled(),gc_thresholds=gc.get_threshold(),
                semantics='20 samples per mode ABBAx10; leaf output sets; no DB, no GC manipulation; traced peak separate')
