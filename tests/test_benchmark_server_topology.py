"""Configuration guards only; no concurrency or performance claim."""
import pytest

from scripts.benchmark_server_topology import server_topology


def test_default_preserves_four_sync_workers():
    assert server_topology({}) == {"worker_class": "sync", "workers": 4, "threads": 1}
    assert server_topology({"WEB_MODELOS_BENCHMARK_GTHREAD": "1",
                            "LOCAL_CI_POSTGRES_CONTAINER": "web-modelos-ci-pg-20261015-120000-deadbeef"}) == {
        "worker_class": "gthread", "workers": 4, "threads": 2}


@pytest.mark.parametrize("mode,container", [("2", ""), ("0", ""), ("1", "web-modelos-db-1"), ("1", "")])
def test_threaded_candidate_rejects_other_modes_or_normal_resources(mode, container):
    with pytest.raises(ValueError):
        server_topology({"WEB_MODELOS_BENCHMARK_GTHREAD": mode, "LOCAL_CI_POSTGRES_CONTAINER": container})


def test_frozen_order_reference_keeps_original_arguments_with_snapshot_keyword():
    from scripts.publication_order_benchmark import compatible_order_reference

    calls = []

    def reference(query, number, checked, observation, stale):
        calls.append((query, number, checked, observation, stale))
        return "original-result"

    adapted = compatible_order_reference(reference)
    assert adapted("query", 2, ("age",), {}, [], trusted_snapshot=True) == "original-result"
    assert calls == [("query", 2, ("age",), {}, [])]
