"""Observer protocol/cleanup only; no backend capacity claims from unit tests."""

import json

import pytest

from scripts.benchmark_worker_observer import _CURRENT, WorkerObserver, collect_events


def test_wsgi_observer_preserves_body_close_status_and_context(tmp_path):
    observer = WorkerObserver(tmp_path)
    closed = []

    class Body(list):
        def close(self):
            closed.append(True)

    work = observer.measured("context", lambda: observer.sql(lambda *a: 17, "secret-sql", ["secret-param"], False, {}))

    def native(environ, start_response):
        assert work() == 17
        start_response("200 OK", [("Content-Type", "text/plain")])
        return Body([b"first", b"second"])

    try:
        statuses = []
        response = observer.wsgi(native)({"HTTP_X_BENCHMARK_ID": "d-4"}, lambda s,h,e: statuses.append(s))
        assert list(response) == [b"first", b"second"]
        response.close()
        response.close()
        assert statuses == ["200 OK"] and closed == [True]
        assert _CURRENT.get() is None
    finally:
        observer.close()
    result = collect_events(tmp_path)
    assert not result["parse_errors"]
    events = result["events"]
    assert [e["event"] for e in events] == ["wsgi_start", "stage_start", "stage_end", "wsgi_end"]
    end = events[-1]
    assert end["status"] == 200 and end["sql"]["calls"] == 1
    assert end["stages"]["context"]["calls"] == 1
    assert "secret" not in json.dumps(result)


def test_worker_exception_retains_partial_work_and_resets_context(tmp_path):
    observer = WorkerObserver(tmp_path)
    work = observer.measured("validation", lambda: 19, progress=True)

    def native(environ, start_response):
        for _ in range(1001):
            assert work() == 19
        raise ValueError("Private payload must not be logged")

    try:
        with pytest.raises(ValueError):
            observer.wsgi(native)({"HTTP_X_BENCHMARK_ID": "u-0"}, lambda *a: None)
        assert _CURRENT.get() is None
    finally:
        observer.close()
    events = collect_events(tmp_path)["events"]
    assert events[-1]["error_type"] == "ValueError"
    assert events[-1]["stages"]["validation"]["calls"] == 1001
    assert len([e for e in events if e["event"] == "stage_progress"]) == 1
    assert "Private payload" not in json.dumps(events)


def test_unidentified_requests_not_captured_and_truncation_explicit(tmp_path):
    observer = WorkerObserver(tmp_path)
    try:
        assert observer.wsgi(lambda e,s: [b"native"])({"HTTP_X_BENCHMARK_ID": "private-value"}, None) == [b"native"]
        assert _CURRENT.get() is None
    finally:
        observer.close()
    assert collect_events(tmp_path)["events"] == []
    (tmp_path / "worker-torn.jsonl").write_text('{"event":')
    assert collect_events(tmp_path)["parse_errors"][0]["error"] == "truncated_or_invalid_json"
