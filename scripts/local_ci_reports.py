"""Preserve synthetic CI reports before a terminal JUnit file is available."""

import json
import os
from pathlib import Path

_destination = None


def pytest_addoption(parser):
    parser.addoption("--local-ci-report-journal", help="Append-only local CI report journal")


def pytest_configure(config):
    global _destination
    value = config.getoption("--local-ci-report-journal")
    # The xdist controller receives every worker report; avoid duplicate writers.
    _destination = Path(value) if value and not hasattr(config, "workerinput") else None


def pytest_runtest_logreport(report):
    if _destination is None:
        return
    item = {
        "nodeid": report.nodeid,
        "when": report.when,
        "outcome": report.outcome,
        "duration": report.duration,
    }
    if report.failed or report.skipped:
        item["longrepr"] = report.longreprtext
    # One write per report. Failures reach disk immediately, even if CI is killed.
    with _destination.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(item, ensure_ascii=True) + "\n")
        stream.flush()
        if report.failed:
            os.fsync(stream.fileno())
