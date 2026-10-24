import json
from types import SimpleNamespace

import pytest
from gunicorn.config import Config

from scripts.benchmark_sync_boundaries import (
    close_sync_boundary_hooks,
    collect_sync_boundaries,
    install_sync_boundary_hooks,
)


def config(callback):
    result = Config()
    result.set("pre_request", callback)
    return result


def test_boundary_hooks_preserve_calls_results_and_restore(tmp_path):
    calls = []
    req = SimpleNamespace(headers=[("X-BENCHMARK-ID", "d-1")], path="/not-recorded")
    worker = SimpleNamespace(cfg=config(lambda w, r: calls.append((w, r))))

    def native(listener, client, address):
        worker.cfg.pre_request(worker, req)
        return listener, client, address

    worker.handle = native
    original_pre = worker.cfg.pre_request
    install_sync_boundary_hooks(worker, tmp_path)
    try:
        with pytest.raises(RuntimeError, match="already installed"):
            install_sync_boundary_hooks(worker, tmp_path)
        assert worker.handle("listener", "client", "address") == ("listener", "client", "address")
        assert calls == [(worker, req)]
        result = collect_sync_boundaries(tmp_path)
        assert not result["parse_errors"] and len(result["samples"]) == 1
        row = result["samples"][0]
        assert row["id"] == "d-1" and row["native_handle_returned"]
        assert row["handler_entered"] <= row["pre_request_entered"] <= row["handler_exited"]
        assert "not-recorded" not in str(result)
    finally:
        close_sync_boundary_hooks(worker)
    close_sync_boundary_hooks(worker)
    assert worker.handle is native and worker.cfg.pre_request is original_pre


def test_error_does_not_leave_connection_state_for_next_request(tmp_path):
    request = SimpleNamespace(headers=[("X-Benchmark-Id", "d-2")])
    worker = SimpleNamespace(cfg=config(lambda w, r: None))

    def native(fail):
        worker.cfg.pre_request(worker, request)
        if fail:
            raise LookupError("native failure")
        return "ok"

    worker.handle = native
    install_sync_boundary_hooks(worker, tmp_path)
    try:
        with pytest.raises(LookupError, match="native failure"):
            worker.handle(True)
        request.headers = [("X-Benchmark-Id", "d-3")]
        assert worker.handle(False) == "ok"
    finally:
        close_sync_boundary_hooks(worker)
    result = collect_sync_boundaries(tmp_path)
    assert not result["parse_errors"]
    assert [r["native_handle_returned"] for r in result["samples"]] == [False, True]
    assert [r["id"] for r in result["samples"]] == ["d-2", "d-3"]


def test_unknown_or_duplicate_identity_is_not_persisted(tmp_path):
    worker = SimpleNamespace(cfg=config(lambda w, r: None))
    worker.handle = lambda req: worker.cfg.pre_request(worker, req)
    install_sync_boundary_hooks(worker, tmp_path)
    try:
        for headers in [[], [("X-Benchmark-Id", "secret/path")],
                        [("X-Benchmark-Id", "d-0"), ("X-Benchmark-Id", "d-1")]]:
            worker.handle(SimpleNamespace(headers=headers))
        worker.handle(SimpleNamespace(headers=[("X-Benchmark-Id", "u-0")]))
    finally:
        close_sync_boundary_hooks(worker)
    result = collect_sync_boundaries(tmp_path)
    assert not result["parse_errors"] and [r["id"] for r in result["samples"]] == ["u-0"]
    assert "secret" not in str(result)


def test_collector_rejects_nonfinite_reversed_duplicate_and_extra_data(tmp_path):
    row = {"id": "d-0", "pid": 1, "handler_entered": 1, "pre_request_entered": 2,
           "handler_exited": 3, "native_handle_returned": True}
    lines = [row, row, {**row, "id": "d-1", "handler_exited": float("nan")},
             {**row, "id": "d-2", "pre_request_entered": 4},
             {**row, "id": "d-3", "path": "private-data"}]
    (tmp_path / "worker-1.jsonl").write_text("\n".join(json.dumps(r) for r in lines))
    result = collect_sync_boundaries(tmp_path)
    assert result["samples"] == [row] and len(result["parse_errors"]) == 4
    assert "private-data" not in str(result)
