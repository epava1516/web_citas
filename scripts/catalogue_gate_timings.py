"""Pytest gate timing report; setup includes fixtures and test environment work."""

import json
from pathlib import Path

_rows = {}


def pytest_addoption(parser):
    parser.addoption("--gate-timings-output", default=None)


def pytest_runtest_logreport(report):
    row = _rows.setdefault(report.nodeid, {})
    row[report.when] = {"seconds": report.duration, "outcome": report.outcome}


def pytest_terminal_summary(terminalreporter):
    target = terminalreporter.config.getoption("--gate-timings-output")
    if target:
        totals = {
            phase: sum(row.get(phase, {}).get("seconds", 0) for row in _rows.values())
            for phase in ["setup", "call", "teardown"]
        }
        Path(target).write_text(
            json.dumps(
                {
                    "schema": "catalogue-gate-test-timings-v1",
                    "tests": _rows,
                    "seconds_by_phase": totals,
                    "limits": [
                        "Setup includes fixtures and test environment; not product latency.",
                        "Diagnosis and integration time are outside this test invocation.",
                    ],
                },
                indent=2,
            )
            + "\n"
        )
