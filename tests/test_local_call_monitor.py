"""Accounting and owned-event cleanup, including recursion and exception unwind."""

import sys

import pytest

from scripts.benchmark_local_monitor import LocalCallMonitor


def test_monitor_direct_children_recursion_exception_and_cleanup():
    def leaf():
        sum(range(20))

    def nested(count):
        leaf()
        if count:
            nested(count - 1)

    def fails():
        raise ValueError("synthetic unwind")

    before = [sys.monitoring.get_tool(i) for i in range(6)]
    with LocalCallMonitor([leaf, nested, fails]) as profile:
        owned = profile.tool
        nested(2)
        with pytest.raises(ValueError, match="synthetic unwind"):
            fails()
    rules = {r["rule"].rsplit(".", 1)[-1]: r for r in profile.report()}
    assert rules["leaf"]["calls"] == rules["nested"]["calls"] == 3
    assert rules["fails"]["calls"] == 1
    assert len(rules["nested"]["instrumented_children"]) == 2
    for row in rules.values():
        assert row["inclusive_time"] == pytest.approx(
            row["exclusive_time"] + sum(row["instrumented_children"].values()), abs=1e-9
        )
    assert not profile.stack
    assert [sys.monitoring.get_tool(i) for i in range(6)] == before
    assert sys.monitoring.get_events(owned) == 0
    assert all(
        sys.monitoring.get_local_events(owned, f.__code__) == 0 for f in [leaf, nested, fails]
    )


def test_monitor_does_not_replace_existing_tool_or_consume_generators():
    free = next(i for i in range(6) if sys.monitoring.get_tool(i) is None)
    sys.monitoring.use_tool_id(free, "synthetic-foreign-tool")

    def scalar():
        return 1

    def generator():
        yield 1

    try:
        with LocalCallMonitor([scalar]) as monitor:
            assert monitor.tool != free and scalar() == 1
        assert sys.monitoring.get_tool(free) == "synthetic-foreign-tool"
        with pytest.raises(ValueError, match="Ordinary synchronous"):
            LocalCallMonitor([generator])
        with pytest.raises(ValueError, match="synthetic outer"):
            with LocalCallMonitor([scalar]):
                raise ValueError("synthetic outer")
        assert sys.monitoring.get_tool(free) == "synthetic-foreign-tool"
    finally:
        sys.monitoring.free_tool_id(free)
