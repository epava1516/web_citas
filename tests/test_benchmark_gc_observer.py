import gc
import weakref

import pytest

from scripts.benchmark_gc_observer import GCObserver


def test_gc_observer_records_real_collection_and_preserves_policy():
    class Cycle:
        pass

    node = Cycle()
    node.self_reference = node
    reference = weakref.ref(node)
    del node
    before_callbacks = list(gc.callbacks)
    before_policy = gc.isenabled(), gc.get_threshold()
    with GCObserver(rule_path=lambda: ("synthetic_rule",)) as observer:
        gc.collect(2)  # Only the test drives collection; the observer never does.
    assert reference() is None
    report = observer.report()
    assert report["calls_by_generation"][2] >= 1
    assert sum(report["calls_by_generation"].values()) == sum(report["collections_stats_delta"])
    assert any(event["collected"] > 0 for event in report["events"])
    assert all(event["active_rule_path"] == ("synthetic_rule",) for event in report["events"])
    assert report["unfinished_events"] == 0
    assert report["wall_seconds"] >= 0 and report["collector_thread_cpu_seconds"] >= 0
    assert gc.callbacks == before_callbacks
    assert (gc.isenabled(), gc.get_threshold()) == before_policy


def test_gc_observer_removes_only_its_callback_after_exception():
    before_callbacks = list(gc.callbacks)
    with pytest.raises(ValueError), GCObserver():
        raise ValueError("synthetic")
    assert gc.callbacks == before_callbacks
