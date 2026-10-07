"""Local HTTP client and open-loop emitter without a pending-request thread cap."""

import asyncio
from urllib.parse import urlsplit

from scripts.benchmark_accounting import POLICY as BASE_POLICY
from scripts.benchmark_accounting import counts, review

POLICY = {
    **BASE_POLICY,
    "emission": "Async coroutine begins whole HTTP transaction, before connection/open/read; event-loop scheduling wait included in generator delay",
    "request_timeout_scope": "65s total across connection, headers and body",
    "client_concurrency": "No pending-request cap; per-request65s timeout bounds outstanding lifetime",
}


async def fetch_http(
    origin,
    path,
    *,
    benchmark_id,
    data=None,
    headers=None,
    expected=200,
    timeout_seconds=65,
    scheduled=None,
):
    target = urlsplit(origin)
    if target.scheme != "http" or target.hostname != "127.0.0.1":
        raise ValueError("Benchmark transport is restricted to local plain HTTP")
    writer = None
    result = {"path": path, "expected": expected}
    try:
        async with asyncio.timeout(timeout_seconds):
            reader, writer = await asyncio.open_connection(target.hostname, target.port)
            call_headers = {
                "Host": f"{target.hostname}:{target.port}",
                "Connection": "close",
                "X-Benchmark-Id": benchmark_id,
                **(headers or {}),
            }
            if data is not None:
                call_headers["Content-Length"] = str(len(data))
            method = "POST" if data is not None else "GET"
            message = f"{method} {path} HTTP/1.1\r\n"
            message += "".join(f"{name}: {value}\r\n" for name, value in call_headers.items())
            writer.write(message.encode("ascii") + b"\r\n" + (data or b""))
            await writer.drain()
            status = int((await reader.readline()).split()[1])
            response_headers = {}
            while True:
                line = await reader.readline()
                if line == b"\r\n":
                    break
                if not line:
                    raise ConnectionError("Response headers ended early")
                name, value = line.decode("latin1").split(":", 1)
                response_headers[name.lower()] = value.strip()
            size = 0
            if response_headers.get("transfer-encoding", "").lower() == "chunked":
                while True:
                    length = int((await reader.readline()).split(b";", 1)[0], 16)
                    if not length:
                        while await reader.readline() not in [b"\r\n", b""]:
                            pass
                        break
                    size += len(await reader.readexactly(length))
                    if await reader.readexactly(2) != b"\r\n":
                        raise ValueError("Invalid chunk terminator")
            elif "content-length" in response_headers:
                size = len(await reader.readexactly(int(response_headers["content-length"])))
            else:
                size = len(await reader.read())
            result.update(status=status, bytes=size, unexpected=status != expected, timeout=False)
    except Exception as error:
        result.update(
            status=0,
            bytes=0,
            unexpected=True,
            timeout=isinstance(error, TimeoutError),
            error=type(error).__name__,
        )
    finally:
        if writer is not None:
            writer.close()
    return result


async def _run(fetch, routes, *, duration, rps, upload_specs, policy):
    loop = asyncio.get_running_loop()
    rows = [
        {
            "id": f"d-{i}",
            "path": routes[i % len(routes)],
            "scheduled_at": i / rps,
            "emitted_at": None,
            "ended_at": None,
        }
        for i in range(int(duration * rps))
    ]
    uploads = [
        {
            "id": f"u-{i}",
            "path": spec["path"],
            "scheduled_at": spec["at"],
            "emitted_at": None,
            "ended_at": None,
        }
        for i, spec in enumerate(upload_specs)
    ]
    start = loop.time()
    end = start + duration
    deadline = end + policy["drain_seconds"]
    sealed = False

    async def worker(row, extra):
        if sealed or loop.time() >= end:
            row["not_emitted_reason"] = "arrival_window_closed"
            return
        row["emitted_at"] = loop.time() - start
        try:
            async with asyncio.timeout(policy["request_timeout_seconds"]):
                payload = await fetch(
                    row["path"],
                    benchmark_id=row["id"],
                    scheduled=start + row["scheduled_at"],
                    **extra,
                )
        except Exception as error:
            payload = dict(
                unexpected=True,
                status=0,
                bytes=0,
                error=type(error).__name__,
                timeout=isinstance(error, TimeoutError),
            )
        if not sealed:
            row.update(payload, ended_at=loop.time() - start)

    tasks = []
    upload_index = 0
    for row in rows:
        await asyncio.sleep(max(0, start + row["scheduled_at"] - loop.time()))
        tasks.append(asyncio.create_task(worker(row, {})))
        while (
            upload_index < len(uploads)
            and uploads[upload_index]["scheduled_at"] <= row["scheduled_at"]
        ):
            spec = upload_specs[upload_index]
            tasks.append(
                asyncio.create_task(
                    worker(
                        uploads[upload_index],
                        {k: v for k, v in spec.items() if k not in ["at", "path"]},
                    )
                )
            )
            upload_index += 1
    await asyncio.sleep(max(0, end - loop.time()))
    window = {
        "dynamic": counts(rows),
        "uploads": counts(uploads),
        "observed_at_seconds": loop.time() - start,
    }
    _, pending = await asyncio.wait(tasks, timeout=max(0, deadline - loop.time()))
    sealed = True
    before = {"dynamic": counts(rows), "uploads": counts(uploads)}
    for row in rows + uploads:
        if row["emitted_at"] is not None and row["ended_at"] is None:
            row.update(
                ended_at=duration + policy["drain_seconds"],
                unexpected=True,
                timeout=True,
                status=0,
                error="drain_deadline",
                forced_terminal=True,
            )
    for task in pending:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    report = review(rows, duration=duration, rps=rps, policy=policy)
    report.update(
        window_close=window,
        final_before_deadline_classification=before,
        final_upload_counts=counts(uploads),
        samples=rows,
        uploads=uploads,
        actual_elapsed_seconds=loop.time() - start,
        policy=dict(policy),
        drain_deadline_seconds=duration + policy["drain_seconds"],
        clock="asyncio loop.time monotonic; all timestamps relative to same start",
        emitter="Async tasks, no pending-request cap; whole-request timeout bounds lifetime",
    )
    if report["final_upload_counts"]["not_emitted"]:
        report["verdict"] = "INVALID"
        report["invalid_reasons"].append("limited_uploads_not_emitted")
    elif report["final_upload_counts"]["failed"] and report["verdict"] != "INVALID":
        report["verdict"] = "FAIL"
    return report


def run_async_open_loop(fetch, routes, *, duration, rps, upload_specs, policy=POLICY):
    return asyncio.run(
        _run(fetch, routes, duration=duration, rps=rps, upload_specs=upload_specs, policy=policy)
    )
