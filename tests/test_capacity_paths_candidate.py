"""Baseline AST and alias lifecycle are controls, not mocked integration."""
import ast
import inspect
import subprocess
import sys
from types import ModuleType

import pytest

from tests.capacity_paths_candidate import original_compiler, variant


def test_original_compiler_matches_head_function():
    source = subprocess.check_output(['git','show','HEAD:apps/safety/rights_portability_coverage.py'],text=True)
    original = next(node for node in ast.parse(source).body if isinstance(node,ast.FunctionDef) and node.name=='compile_coverage')
    # First verify the entire loaded function against the frozen source at HEAD.
    from apps.safety.rights_portability_coverage import compile_coverage
    current = ast.parse(inspect.getsource(compile_coverage)).body[0]
    assert ast.dump(current)==ast.dump(original)
    # Independently reconstruct the baseline from HEAD, then compare its complete
    # code object with the adapter's baseline (not with the optimized HEAD).
    ast.increment_lineno(original, 1 - original.lineno)
    replacements = 0
    for node in ast.walk(original):
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='paths':
            node.value=ast.parse('paths = {item["path"] for item in scalar_fields(row)}').body[0].value
            replacements += 1
    assert replacements == 1
    from apps.safety import rights_portability_coverage as coverage
    tree = ast.Module(body=[original], type_ignores=[])
    ast.fix_missing_locations(tree)
    namespace = dict(vars(coverage))
    exec(compile(tree, '<original-coverage-paths>', 'exec'), namespace)
    assert namespace['compile_coverage'].__code__ == original_compiler().__code__
    assert original_compiler() is original_compiler()


@pytest.mark.parametrize('mode',['original','paths'])
def test_aliases_regular_and_late_restored_after_exception(mode,monkeypatch):
    from apps.safety import rights_portability_coverage as coverage
    original=coverage.compile_coverage
    late=ModuleType('apps.safety._paths_late_test')
    monkeypatch.setitem(sys.modules,late.__name__,late)
    with pytest.raises(ValueError):
        with variant(mode):
            late.operation=coverage.compile_coverage
            if mode=='original':
                assert late.operation is not original
            raise ValueError('synthetic')
    assert coverage.compile_coverage is original and late.operation is original
