import gc
import time
import weakref

import pytest

from scripts.benchmark_gc_observer import GCObserver, generator_gc_overlap, prepare_generator_gc


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


def test_generator_overlap_unions_events_and_ignores_unemitted_requests():
    events = [{"monotonic_start": 10.02, "monotonic_end": 10.08},
              {"monotonic_start": 10.03, "monotonic_end": 10.05}]
    rows = [{"id": "d-0", "scheduled_at": 0, "emitted_at": 0.12},
            {"id": "d-1", "scheduled_at": 0.02, "emitted_at": 0.04},
            {"id": "d-2", "scheduled_at": 0.1, "emitted_at": None}]
    report = generator_gc_overlap(events, rows, 10)
    assert report["emitted_population"] == report["requests_with_gc_overlap"] == 2
    assert report["largest_delay"]["id"] == "d-0"
    assert report["largest_delay"]["gc_overlap_seconds"] == pytest.approx(0.06)
    assert report["overlapping_delays"][1]["gc_overlap_seconds"] == pytest.approx(0.02)


def test_gc_timestamps_share_standard_generator_monotonic_origin():
    from scripts.benchmark_async_transport import run_async_open_loop

    async def fetch(path, **kwargs):
        # Young-generation collection still produces observable events, but its cost does not grow
        # with the whole heap: a blocking full collection longer than the 50ms arrival gap made the
        # third arrival fall after the 0.15s window (arrival_window_closed), as reproduced with ballast.
        gc.collect(0)
        return dict(status=200, unexpected=False, timeout=False, bytes=2)

    with GCObserver(monotonic_clock=time.monotonic) as observer:
        outcome = run_async_open_loop(fetch, ["/synthetic"], duration=0.15, rps=20,
                                      upload_specs=[])
    assert outcome["counts"]["emitted"] == outcome["counts"]["successful"] == 3
    assert outcome["counts"]["reconciled"]
    events = observer.report()["events"]
    assert all(event["monotonic_start"] <= event["monotonic_end"] for event in events)
    assert any(event["monotonic_start"] >= outcome["monotonic_origin_seconds"] for event in events)
    assert generator_gc_overlap(events, outcome["samples"],
                                outcome["monotonic_origin_seconds"])["emitted_population"] == 3


def test_client_preparation_reclaims_cycles_without_changing_load_policy():
    class Cycle:
        pass

    node = Cycle()
    node.self_reference = node
    reference = weakref.ref(node)
    del node
    callbacks = list(gc.callbacks)
    prepared = prepare_generator_gc()
    assert reference() is None
    assert prepared["collected_gc_objects"] > 0
    assert prepared["policy_before"] == prepared["policy_after"]
    assert prepared["completed_at_monotonic"] <= time.monotonic()
    assert gc.callbacks == callbacks
