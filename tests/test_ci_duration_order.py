"""Duration hints may change scheduling, never the selected cases or local sequence."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.local_ci_duration_order import file_costs, order_items


def test_long_single_case_file_precedes_many_short_cases_without_losing_local_order(tmp_path):
    nodes = ["tests/test_short.py::test_z", "tests/test_long.py::test_only",
             "tests/test_short.py::test_a", "tests/test_new.py::test_new"]
    report = {"schema": "catalogue-gate-test-timings-v1", "tests": {
        nodes[0]: {"call": {"seconds": 1}}, nodes[1]: {"call": {"seconds": 100}},
        nodes[2]: {"setup": {"seconds": 2}, "call": {"seconds": 1}},
    }}
    path = tmp_path / "history.json"
    path.write_text(json.dumps(report))
    items = [SimpleNamespace(nodeid=node) for node in nodes]
    first = order_items(items, file_costs(path))
    assert [item.nodeid for item in items] == [nodes[1], nodes[0], nodes[2], nodes[3]]
    assert order_items(items, file_costs(path)) == first
    assert sorted(item.nodeid for item in items) == sorted(nodes)


@pytest.mark.parametrize("seconds", [-1, float("nan"), True, "100"])
def test_invalid_duration_cannot_silently_change_scheduling(tmp_path, seconds):
    path = tmp_path / "history.json"
    path.write_text(json.dumps({"schema": "catalogue-gate-test-timings-v1", "tests": {
        "tests/test_case.py::test_a": {"call": {"seconds": seconds}},
    }}))
    with pytest.raises(ValueError, match="Invalid test duration"):
        file_costs(path)


def test_direct_cli_validates_history_before_creating_resources(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run([
        sys.executable, str(root / "scripts/run_local_ci.py"), "--profile", "regression",
        "--regression-lane", "functional", "--workers", "2", "--duration-order-from",
        str(tmp_path / "missing.json"),
    ], cwd=tmp_path, capture_output=True, text=True, timeout=10)
    assert result.returncode == 2
    assert "Invalid duration history" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr
