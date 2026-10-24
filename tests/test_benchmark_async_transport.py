"""Client protocol/scheduling evidence only; native PG calibration is separate."""

import asyncio

import pytest

from scripts.benchmark_async_transport import POLICY, fetch_http, run_async_open_loop


def test_more_than_eighty_pending_requests_are_emitted_without_dropped_slots():
    async def slow(path, **kwargs):
        await asyncio.sleep(5)
        return dict(status=200, unexpected=False, timeout=False, bytes=2)

    report = run_async_open_loop(
        slow, ["/slow/"], duration=4.8, rps=20, upload_specs=[], policy=POLICY
    )
    assert report["counts"]["scheduled"] == report["counts"]["emitted"] == 96
    assert report["window_close"]["dynamic"]["pending"] == 96
    assert report["counts"]["not_emitted"] == report["counts"]["failed"] == 0
    assert report["counts"]["reconciled"] and report["counts"]["successful"] == 96
    assert "scheduler_trace" not in report
    assert all("scheduler_awoke_at" not in row and "task_queued_at" not in row
               for row in report["samples"])


def test_whole_request_timeout_and_fixed_drain_classify_pending_separately():
    async def slow(path, **kwargs):
        await asyncio.sleep(2)
        return dict(status=200, unexpected=False)

    report = run_async_open_loop(
        slow,
        ["/slow/"],
        duration=0.1,
        rps=10,
        upload_specs=[],
        policy={**POLICY, "drain_seconds": 0.05},
    )
    assert report["window_close"]["dynamic"]["pending"] == 1
    assert report["final_before_deadline_classification"]["dynamic"]["pending"] == 1
    assert report["counts"]["failed"] == report["counts"]["timeouts"] == 1
    assert report["samples"][0]["forced_terminal"]
    report = run_async_open_loop(
        slow,
        ["/slow/"],
        duration=0.1,
        rps=10,
        upload_specs=[],
        policy={**POLICY, "request_timeout_seconds": 0.02},
    )
    assert report["counts"]["failed"] == report["counts"]["timeouts"] == 1
    assert not report["samples"][0].get("forced_terminal")
    assert report["window_close"]["dynamic"]["pending"] == 0


def test_local_tcp_chunked_body_post_headers_and_redirect_status():
    async def exercise():
        seen = []

        async def handler(reader, writer):
            line = (await reader.readline()).decode("ascii").strip()
            headers = {}
            while True:
                raw = await reader.readline()
                if raw == b"\r\n":
                    break
                key, value = raw.decode("ascii").split(":", 1)
                headers[key.lower()] = value.strip()
            body = await reader.readexactly(int(headers.get("content-length", 0)))
            seen.append((line, headers, body))
            if line.startswith("POST"):
                writer.write(
                    b"HTTP/1.1 302 Found\r\nContent-Length: 0\r\nLocation: /ignored/\r\n\r\n"
                )
            else:
                writer.write(
                    b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n2\r\nok\r\n0\r\n\r\n"
                )
            await writer.drain()
            writer.close()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        async with server:
            origin = f"http://127.0.0.1:{port}"
            get = await fetch_http(origin, "/query/?q=synthetic", benchmark_id="d-0")
            post = await fetch_http(
                origin,
                "/upload/",
                benchmark_id="u-0",
                data=b"abc",
                headers={"X-CSRFToken": "synthetic-test"},
                expected=302,
            )
            assert get["status"] == 200 and get["bytes"] == 2 and not get["unexpected"]
            assert post["status"] == 302 and not post["unexpected"]
            assert len(seen) == 2  # No redirect follow.
            assert seen[0][0] == "GET /query/?q=synthetic HTTP/1.1"
            assert seen[1][1]["x-csrftoken"] == "synthetic-test"
            assert seen[1][1]["x-benchmark-id"] == "u-0" and seen[1][2] == b"abc"

    asyncio.run(exercise())


def test_optional_client_phases_separate_delayed_headers_and_body():
    async def exercise():
        async def handler(reader, writer):
            await reader.readuntil(b"\r\n\r\n")
            await asyncio.sleep(0.03)
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n")
            await writer.drain()
            await asyncio.sleep(0.03)
            writer.write(b"ok")
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        origin = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        async with server:
            plain = await fetch_http(origin, "/", benchmark_id="d-0")
            traced = await fetch_http(origin, "/", benchmark_id="d-1", trace_phases=True)
        assert "client_phases" not in plain
        assert {k: v for k, v in traced.items() if k != "client_phases"} == plain
        phase = traced["client_phases"]
        stamps = phase["timestamps_seconds"]
        assert list(stamps) == ["connect_started", "connected", "request_drained",
                                "status_line_received", "headers_received", "body_received", "terminal"]
        assert list(stamps.values()) == sorted(stamps.values())
        assert stamps["status_line_received"] - stamps["request_drained"] >= 0.02
        assert stamps["body_received"] - stamps["headers_received"] >= 0.02
        assert phase["complete_body"]

    asyncio.run(exercise())


def test_client_phases_preserve_partial_timeout_and_emitter_accounting():
    async def exercise():
        release = asyncio.Event()
        finished = asyncio.Event()

        async def handler(reader, writer):
            try:
                await reader.readuntil(b"\r\n\r\n")
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\n")
                await writer.drain()
                await release.wait()
            finally:
                writer.close()
                await writer.wait_closed()
                finished.set()

        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        origin = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}"
        async with server:
            try:
                result = await fetch_http(origin, "/", benchmark_id="d-0",
                                          timeout_seconds=0.05, trace_phases=True)
                assert result["unexpected"] and result["timeout"] and result["status"] == 0
                phase = result["client_phases"]
                assert not phase["complete_body"]
                assert "headers_received" in phase["timestamps_seconds"]
                assert "body_received" not in phase["timestamps_seconds"]
                assert phase["timestamps_seconds"]["terminal"] >= 0.04
            finally:
                release.set()
                await asyncio.wait_for(finished.wait(), 2)

    asyncio.run(exercise())


def test_open_loop_retains_optional_client_phase_payload():
    async def exercise_fetch(path, **kwargs):
        return {"status": 200, "unexpected": False, "timeout": False, "bytes": 2,
                "client_phases": {"timestamps_seconds": {"terminal": 0.01}, "complete_body": True}}

    report = run_async_open_loop(exercise_fetch, ["/"], duration=0.1, rps=10, upload_specs=[])
    assert report["counts"]["successful"] == report["counts"]["emitted"] == 1
    assert report["counts"]["not_emitted"] == report["counts"]["pending"] == 0
    assert report["samples"][0]["client_phases"]["complete_body"]


def test_completed_http_tasks_are_released_while_ledger_is_retained(monkeypatch):
    import weakref

    refs = []
    original_create_task = asyncio.create_task

    def tracked_create_task(coro):
        task = original_create_task(coro)
        refs.append(weakref.ref(task))
        return task

    monkeypatch.setattr(asyncio, "create_task", tracked_create_task)
    released_during_window = []

    async def fetch(path, benchmark_id, **kwargs):
        if benchmark_id == "d-15":
            released_during_window.append(sum(ref() is None for ref in refs[:10]))
        return dict(status=302 if benchmark_id.startswith("u-") else 200,
                    unexpected=False, timeout=False, bytes=2)

    report = run_async_open_loop(
        fetch, ["/"], duration=0.2, rps=100,
        upload_specs=[{"path": "/upload/", "at": 0.05}],
    )
    assert released_during_window == [10]
    assert len(report["samples"]) == report["counts"]["successful"] == 20
    assert report["counts"]["reconciled"] and report["counts"]["pending"] == 0
    assert report["final_upload_counts"]["successful"] == 1
    assert report["uploads"][0]["status"] == 302


def test_task_release_preserves_failed_upload_and_resource_stop():
    import threading

    async def failure(path, **kwargs):
        raise ConnectionError("synthetic failure")

    failed = run_async_open_loop(
        failure, ["/"], duration=0.05, rps=20,
        upload_specs=[{"path": "/upload/", "at": 0}],
    )
    assert failed["counts"]["failed"] == 1
    assert failed["final_upload_counts"]["failed"] == 1
    assert failed["samples"][0]["error"] == "ConnectionError"
    assert failed["counts"]["pending"] == 0

    stopped = threading.Event()
    terminal = []

    async def hanging(path, **kwargs):
        stopped.set()
        try:
            await asyncio.sleep(10)
        finally:
            terminal.append(path)

    report = run_async_open_loop(
        hanging, ["/"], duration=0.2, rps=20, upload_specs=[],
        stop_requested=stopped,
    )
    assert report["verdict"] == "INVALID"
    assert "trial_resource_stop" in report["invalid_reasons"]
    assert report["counts"]["emitted"] == report["counts"]["failed"] == 1
    assert report["counts"]["not_emitted"] == 3
    assert report["counts"]["pending"] == 0 and report["counts"]["reconciled"]
    assert terminal == ["/"]


@pytest.mark.parametrize("delayed_boundary", ["wake", "task"])
def test_scheduler_trace_separates_delays_without_hiding_invalid_emission(monkeypatch,
                                                                         delayed_boundary):
    original_sleep = asyncio.sleep
    original_create_task = asyncio.create_task
    first_sleep = True

    async def delayed_sleep(seconds):
        nonlocal first_sleep
        if first_sleep:
            first_sleep = False
            await original_sleep(0.04)
        await original_sleep(seconds)

    def delayed_create_task(coro):
        async def delayed():
            await original_sleep(0.04)
            return await coro
        return original_create_task(delayed())

    if delayed_boundary == "wake":
        monkeypatch.setattr(asyncio, "sleep", delayed_sleep)
    else:
        monkeypatch.setattr(asyncio, "create_task", delayed_create_task)

    async def fetch(path, benchmark_id, **kwargs):
        return dict(status=302 if benchmark_id.startswith("u-") else 200,
                    unexpected=False, timeout=False, bytes=2)

    report = run_async_open_loop(fetch, ["/"], duration=0.2, rps=10,
                                 upload_specs=[{"path": "/upload/", "at": 0}],
                                 trace_scheduler=True)
    assert report["verdict"] == "INVALID"
    assert report["generator_delay_seconds"]["p99"] > POLICY["generator_p99_seconds_max"]
    assert report["policy"] == POLICY
    assert report["counts"]["successful"] == report["counts"]["emitted"] == 2
    assert report["counts"]["reconciled"] and report["counts"]["pending"] == 0
    assert report["final_upload_counts"]["successful"] == 1
    assert report["scheduler_trace"]["emission_and_validity_policy_unchanged"]
    for row in report["samples"] + report["uploads"]:
        scheduled, awake, queued, emitted = (row[key] for key in (
            "scheduled_at", "scheduler_awoke_at", "task_queued_at", "emitted_at"))
        assert scheduled <= awake <= queued <= emitted <= row["ended_at"]
        assert emitted - scheduled == pytest.approx(
            (awake - scheduled) + (queued - awake) + (emitted - queued), abs=1e-12)
    first = report["samples"][0]
    assert (first["scheduler_awoke_at"] - first["scheduled_at"] if delayed_boundary == "wake"
            else first["emitted_at"] - first["task_queued_at"]) >= 0.035
    assert report["uploads"][0]["scheduler_awoke_at"] == first["scheduler_awoke_at"]
