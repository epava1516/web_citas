from scripts.benchmark_rule_profile import RuleProfile


def test_direct_child_discount_does_not_double_count_grandchildren():
    times = iter([0, 1, 2, 4, 6, 10])
    profile = RuleProfile(clock=lambda: next(times))
    leaf = profile.wrap("leaf", lambda: None)
    child = profile.wrap("child", leaf)
    parent = profile.wrap("parent", child)
    parent()
    rows = {row["rule"]: row for row in profile.report()}
    assert rows["parent"]["inclusive_time"] == 10
    assert rows["parent"]["exclusive_time"] == 5
    assert rows["parent"]["instrumented_children"] == {"child": 5}
    assert rows["child"]["exclusive_time"] == 3
    assert rows["leaf"]["exclusive_time"] == 2
    assert sum(row["exclusive_time"] for row in rows.values()) == 10


def test_exception_closes_event_and_restores_parent_stack():
    times = iter([0, 2, 3, 7])
    profile = RuleProfile(clock=lambda: next(times))
    def fail():
        raise ValueError("synthetic")
    measured = profile.wrap("fail", fail)
    try:
        measured()
    except ValueError:
        pass
    profile.wrap("next", lambda: None)()
    assert profile.stack.get() == ()
    assert all(not row["instrumented_children"] for row in profile.report())
