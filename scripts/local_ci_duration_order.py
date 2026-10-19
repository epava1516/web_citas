"""Opt-in whole-file duration ordering; never remove cases or change file-local order."""

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import pytest


def file_costs(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or data.get("schema") != "catalogue-gate-test-timings-v1":
        raise ValueError("Expected an owned gate timing report")
    if not isinstance(data.get("tests"), dict):
        raise ValueError("Expected test timing records")
    costs = Counter()
    for nodeid, phases in data["tests"].items():
        if not isinstance(nodeid, str) or not isinstance(phases, dict):
            raise ValueError("Invalid test timing record")
        name = nodeid.split("::", 1)[0]
        if not name.startswith("tests/") or ".." in Path(name).parts:
            raise ValueError("Unexpected test source in timing report")
        for phase in ("setup", "call", "teardown"):
            value = phases.get(phase, {})
            if not isinstance(value, dict):
                raise ValueError("Invalid test timing phase")
            seconds = value.get("seconds", 0)
            if type(seconds) not in (int, float) or not math.isfinite(seconds) or seconds < 0:
                raise ValueError("Invalid test duration")
            costs[name] += seconds
    return costs


def order_items(items, costs):
    before = [item.nodeid for item in items]
    items.sort(key=lambda item: (-costs.get(item.nodeid.split("::", 1)[0], 0),
                                 item.nodeid.split("::", 1)[0]))
    after = [item.nodeid for item in items]
    if Counter(before) != Counter(after):
        raise RuntimeError("Duration ordering changed the selected cases")
    return hashlib.sha256(json.dumps(sorted(after)).encode()).hexdigest()


def pytest_addoption(parser):
    parser.addoption("--local-ci-duration-history", required=True)
    parser.addoption("--local-ci-duration-order-report", required=True)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(config, items):
    history = Path(config.getoption("--local-ci-duration-history"))
    before = [item.nodeid for item in items]
    digest = order_items(items, file_costs(history))
    ordered = [item.nodeid for item in items]
    for name in {node.split("::", 1)[0] for node in before}:
        assert [n for n in before if n.split("::", 1)[0] == name] == [
            n for n in ordered if n.split("::", 1)[0] == name
        ]
    worker = getattr(config, "workerinput", {}).get("workerid", "controller")
    target = Path(config.getoption("--local-ci-duration-order-report"))
    target = target.with_name(target.stem + "." + worker + target.suffix)
    target.write_text(json.dumps({
        "nodeids": len(items), "nodeid_set_sha256": digest,
        "history_sha256": hashlib.sha256(history.read_bytes()).hexdigest(),
        "ordered_files": list(dict.fromkeys(n.split("::", 1)[0] for n in ordered)),
        "within_file_order_preserved": True,
        "scope": "Ordering only; not test PASS or measured speedup",
    }, indent=2) + "\n")
