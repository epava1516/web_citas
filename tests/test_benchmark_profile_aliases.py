"""Observer labels must not silently overwrite distinct callable identities."""
from functools import wraps

import pytest
from scripts.benchmark_call_profile import CallProfile


def decorate(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)
    return wrapper


@decorate
def first_rule(value):
    return value + 1


@decorate
def second_rule(value):
    return value * 2


def test_shared_wrapper_code_rejects_ambiguous_rule_names():
    assert first_rule.__code__ is second_rule.__code__
    with pytest.raises(ValueError, match="Ambiguous profile code"):
        CallProfile([first_rule, second_rule])


def test_selected_bodies_preserve_call_counts_without_changing_wrappers():
    before = first_rule.__code__, second_rule.__code__
    profile = CallProfile([first_rule.__wrapped__, second_rule.__wrapped__])
    with profile:
        assert first_rule(3) == 4
        assert first_rule(4) == 5
        assert second_rule(4) == 8
    rows = {row["rule"]: row for row in profile.report()}
    assert rows[first_rule.__module__ + ".first_rule"]["calls"] == 2
    assert rows[second_rule.__module__ + ".second_rule"]["calls"] == 1
    assert before == (first_rule.__code__, second_rule.__code__)


def test_exclusive_time_discounts_each_observed_descendant_once(monkeypatch):
    from types import SimpleNamespace
    from scripts import benchmark_call_profile
    wall = iter([0, 1, 2, 4, 6, 10])
    cpu = iter([0, .5, .75, 1, 1.5, 3])
    monkeypatch.setattr(benchmark_call_profile, "time", SimpleNamespace(
        perf_counter=lambda: next(wall), thread_time=lambda: next(cpu)))

    def leaf():
        return None

    def child():
        leaf()

    def parent():
        child()

    profile = CallProfile([parent, child, leaf])
    with profile:
        parent()
    rows = {row["rule"].rsplit(".", 1)[-1]: row for row in profile.report()}
    assert rows["parent"]["inclusive_time"] == 10
    assert rows["parent"]["exclusive_time"] == 5
    assert rows["child"]["exclusive_time"] == 3
    assert rows["leaf"]["exclusive_time"] == 2
    assert sum(row["exclusive_time"] for row in rows.values()) == 10
    assert sum(row["exclusive_thread_cpu_time"] for row in rows.values()) == 3
