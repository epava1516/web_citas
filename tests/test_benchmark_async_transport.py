"""Client protocol/scheduling evidence only; native PG calibration is separate."""

import asyncio

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
