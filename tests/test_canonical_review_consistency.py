"""Keep the independent Python fallback bodies equivalent without a native build."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from apps.safety import canonical_kernel_loader, fast_canonical
from scripts import build_canonical_kernel, canonical_artifacts


def outcome(check, value, depth=0):
    try:
        return ("ok", check(value, depth))
    except (TypeError, ValueError, RecursionError) as error:
        return (type(error), str(error))


@pytest.mark.parametrize("depth", [0, 199, 200, 201])
def test_reference_and_unavailable_kernel_fallback_preserve_order(monkeypatch, depth):
    monkeypatch.setattr(canonical_kernel_loader, "validated_kernel", lambda: None)
    cycle = []
    cycle.append(cycle)
    nested = None
    for _ in range(201):
        nested = [nested]
    values = [
        None, True, 2**100, "é\ud800", -0.0,
        {"z": [1, ("a", None)], "a": {}},
        float("nan"), float("inf"), object(),
        {1: float("nan")}, {"first": float("nan"), 1: None},
        [object(), float("nan")], [float("nan"), object()],
        cycle, nested,
    ]
    for value in values:
        assert outcome(fast_canonical._check, value, depth) == outcome(
            fast_canonical.reference_check, value, depth
        )


def test_builder_and_loader_share_build_identity():
    assert build_canonical_kernel.FLAGS is canonical_artifacts.BUILD_FLAGS
    assert canonical_kernel_loader.BUILD_FLAGS is canonical_artifacts.BUILD_FLAGS
    assert build_canonical_kernel.CYTHON_VERSION == canonical_kernel_loader.CYTHON_VERSION
    assert build_canonical_kernel.MODULE == canonical_kernel_loader.MODULE
    assert canonical_artifacts.CYTHON_VERSION == "3.0.12"
    assert canonical_artifacts.BUILD_FLAGS == ["-O3", "-fPIC", "-shared"]


def test_standalone_builder_imports_without_build_or_project_path(tmp_path):
    builder = Path(build_canonical_kernel.__file__).resolve()
    # run_path uses a non-main name: exercise the direct-script import branch
    # without importing Cython, invoking a compiler or producing artifacts.
    code = """
import runpy, sys
sys.path.insert(0, sys.argv[1])
namespace = runpy.run_path(sys.argv[2], run_name='standalone_probe')
assert namespace['CYTHON_VERSION'] == '3.0.12'
assert namespace['FLAGS'] == ['-O3', '-fPIC', '-shared']
assert 'Cython' not in sys.modules
assert 'apps.safety.canonical_kernel_loader' not in sys.modules
"""
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(builder.parent), str(builder)],
        cwd=tmp_path, env=environment, check=True, capture_output=True, timeout=15,
    )
