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

    work = observer.measured(
        "context", lambda: observer.sql(lambda *a: 17, "secret-sql", ["secret-param"], False, {})
    )

    def native(environ, start_response):
        assert work() == 17
        start_response("200 OK", [("Content-Type", "text/plain")])
        return Body([b"first", b"second"])

    try:
        statuses = []
        response = observer.wsgi(native)(
            {"HTTP_X_BENCHMARK_ID": "d-4"}, lambda s, h, e: statuses.append(s)
        )
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
        assert observer.wsgi(lambda e, s: [b"native"])(
            {"HTTP_X_BENCHMARK_ID": "private-value"}, None
        ) == [b"native"]
        assert _CURRENT.get() is None
    finally:
        observer.close()
    assert collect_events(tmp_path)["events"] == []
    (tmp_path / "worker-torn.jsonl").write_text('{"event":')
    assert collect_events(tmp_path)["parse_errors"][0]["error"] == "truncated_or_invalid_json"


def test_sql_attribution_is_bounded_private_and_keeps_failed_calls(tmp_path):
    observer = WorkerObserver(tmp_path)

    def native(environ, start_response):
        for index in range(40):
            observer.sql(lambda *args: None, f"private-query-{index}", ["secret"], False, {})
        with pytest.raises(ValueError):
            observer.sql(
                lambda *args: (_ for _ in ()).throw(ValueError("private-error")),
                "private-query-0",
                ["secret"],
                False,
                {},
            )
        start_response("200 OK", [])
        return [b"ok"]

    try:
        response = observer.wsgi(native)({"HTTP_X_BENCHMARK_ID": "d-0"}, lambda *args: None)
        assert list(response) == [b"ok"]
        response.close()
    finally:
        observer.close()
    events = collect_events(tmp_path)["events"]
    sql = events[-1]["sql"]
    assert sql["calls"] == 41
    assert len(sql["queries"]) == 33
    assert sql["queries"]["overflow"]["calls"] == 8
    assert sum(row["calls"] for row in sql["queries"].values()) == sql["calls"]
    assert sum(row["wall"] for row in sql["queries"].values()) == pytest.approx(sql["wall"])
    assert sum(row["thread_cpu"] for row in sql["queries"].values()) == pytest.approx(
        sql["thread_cpu"]
    )
    assert not any(
        value in json.dumps(events) for value in ("private-query", "secret", "private-error")
    )


def test_wsgi_context_and_finish_are_isolated_between_concurrent_threads(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    observer = WorkerObserver(tmp_path)
    barrier = Barrier(2)

    def native(environ, start_response):
        identity = environ["HTTP_X_BENCHMARK_ID"]
        assert _CURRENT.get()["id"] == identity
        barrier.wait(timeout=5)
        assert _CURRENT.get()["id"] == identity
        start_response("200 OK", [])
        return [identity.encode()]

    app = observer.wsgi(native)

    def request(identity):
        response = app({"HTTP_X_BENCHMARK_ID": identity}, lambda *args: None)
        try:
            assert b"".join(response) == identity.encode()
        finally:
            response.close()
        assert _CURRENT.get() is None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(request, ["d-1", "d-2"]))
    finally:
        observer.close()
    observed = collect_events(tmp_path)
    assert observed["parse_errors"] == []
    for identity in ("d-1", "d-2"):
        events = [e for e in observed["events"] if e["id"] == identity]
        assert [e["event"] for e in events] == ["wsgi_start", "wsgi_end"]
        assert events[-1]["status"] == 200 and events[-1]["error_type"] is None


def test_opt_in_gc_records_real_collection_and_removes_callback(tmp_path):
    import gc

    callbacks, enabled, thresholds = list(gc.callbacks), gc.isenabled(), gc.get_threshold()
    observer = WorkerObserver(tmp_path, observe_gc=True)

    def native(environ, start_response):
        gc.collect(2)  # Test stimulus only; observer never forces collection.
        start_response('200 OK', [])
        return [b'ok']

    try:
        response = observer.wsgi(native)({'HTTP_X_BENCHMARK_ID': 'd-0'}, lambda *a: None)
        assert b''.join(response) == b'ok'
        response.close()
    finally:
        observer.close()
    assert gc.callbacks == callbacks
    assert gc.isenabled() == enabled and gc.get_threshold() == thresholds
    data = collect_events(tmp_path)
    assert not data['parse_errors']
    measured = data['events'][-1]['gc']
    assert measured['events_count'] >= 1
    assert measured['on_worker_thread_count'] >= 1
    assert measured['wall_seconds'] >= measured['thread_cpu_seconds'] * 0.5
    assert any(e['generation'] == 2 for e in measured['largest_events'])
    assert _CURRENT.get() is None


def test_prelude_is_bounded_private_and_does_not_modify_request(tmp_path):
    observer = WorkerObserver(tmp_path, observe_prelude=True)
    seen = []
    def native(environ, start_response):
        seen.append(dict(environ))
        start_response('200 OK', [])
        return [b'ok']
    env = {'PATH_INFO': '/secret-path', 'HTTP_COOKIE': 'secret-cookie'}
    try:
        for _ in range(34):
            response = observer.wsgi(native)(env, lambda *args: None)
            assert list(response) == [b'ok']
            if hasattr(response, 'close'):
                response.close()
    finally:
        observer.close()
    events = collect_events(tmp_path)['events']
    starts = [e for e in events if e['event'] == 'wsgi_start']
    assert len(starts) == 32 and all(e['prelude'] for e in starts)
    assert len({e['id'] for e in starts}) == 32
    assert seen == [env] * 34 and 'secret' not in json.dumps(events)
    assert _CURRENT.get() is None


def test_sql_shapes_are_opt_in_bounded_cardinalities_without_values(tmp_path):
    observer = WorkerObserver(tmp_path, observe_sql_shapes=True)

    def native(environ, start_response):
        for i in range(140):
            observer.sql(lambda *args: None, f'secret-sql-{i}', [['secret'] * 3, 'hidden'], False, {})
        for size in range(12):
            observer.sql(lambda *args: None, 'secret-sql-0', [['hidden'] * size], False, {})
        start_response('200 OK', [])
        return [b'ok']

    try:
        response = observer.wsgi(native)(
            {'HTTP_X_BENCHMARK_ID': 'd-0', 'PATH_INFO': '/secret/', 'QUERY_STRING': 'hidden=secret'},
            lambda *args: None,
        )
        assert list(response) == [b'ok']
        response.close()
    finally:
        observer.close()
    events = collect_events(tmp_path)['events']
    queries = events[-1]['sql']['queries']
    assert len(queries) == 129 and queries['overflow']['calls'] == 12
    assert sum(x['calls'] for x in queries.values()) == 152
    bucket = next(x for x in queries.values() if x['calls'] == 13)
    assert len(bucket['parameter_shapes']) == 9
    assert sum(bucket['parameter_shapes'].values()) == bucket['calls']
    assert any(json.loads(key).get('nested_lengths') == [3, None]
               for key in bucket['parameter_shapes'] if key != 'overflow')
    assert len(events[0]['route_sha256']) == 64
    assert not any(value in json.dumps(events) for value in ['secret', 'hidden'])
