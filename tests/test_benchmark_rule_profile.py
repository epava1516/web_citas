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


def test_thread_cpu_excludes_wait_and_discounts_only_direct_children():
    wall = iter([0, 1, 2, 4, 6, 10])
    cpu = iter([0, 0.5, 0.75, 1, 1.5, 3])
    profile = RuleProfile(clock=lambda: next(wall), cpu_clock=lambda: next(cpu))
    leaf = profile.wrap("leaf", lambda: None)
    child = profile.wrap("child", leaf)
    profile.wrap("parent", child)()
    rows = {row["rule"]: row for row in profile.report()}
    assert rows["parent"]["inclusive_time"] == 10
    assert rows["parent"]["inclusive_thread_cpu_time"] == 3
    assert rows["parent"]["exclusive_thread_cpu_time"] == 2
    assert rows["parent"]["instrumented_children_thread_cpu"] == {"child": 1}
    assert rows["child"]["exclusive_thread_cpu_time"] == 0.75
    assert rows["leaf"]["exclusive_thread_cpu_time"] == 0.25
    assert sum(row["exclusive_thread_cpu_time"] for row in rows.values()) == 3
