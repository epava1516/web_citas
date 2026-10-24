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
    trace_phases=False,
):
    target = urlsplit(origin)
    if target.scheme != "http" or target.hostname != "127.0.0.1":
        raise ValueError("Benchmark transport is restricted to local plain HTTP")
    writer = None
    result = {"path": path, "expected": expected}
    phase_clock = asyncio.get_running_loop().time if trace_phases else None
    phase_start = phase_clock() if phase_clock else None
    phases = {"connect_started": 0.0} if phase_clock else None
    try:
        async with asyncio.timeout(timeout_seconds):
            reader, writer = await asyncio.open_connection(target.hostname, target.port)
            if phases is not None:
                phases["connected"] = phase_clock() - phase_start
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
            if phases is not None:
                phases["request_drained"] = phase_clock() - phase_start
            status = int((await reader.readline()).split()[1])
            if phases is not None:
                phases["status_line_received"] = phase_clock() - phase_start
            response_headers = {}
            while True:
                line = await reader.readline()
                if line == b"\r\n":
                    break
                if not line:
                    raise ConnectionError("Response headers ended early")
                name, value = line.decode("latin1").split(":", 1)
                response_headers[name.lower()] = value.strip()
            if phases is not None:
                phases["headers_received"] = phase_clock() - phase_start
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
            if phases is not None:
                phases["body_received"] = phase_clock() - phase_start
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
        if phases is not None:
            phases["terminal"] = phase_clock() - phase_start
            result["client_phases"] = {
                "clock": "asyncio loop.time; seconds relative to fetch connection start",
                "timestamps_seconds": phases,
                "origin_monotonic_seconds": phase_start,
                "complete_body": "body_received" in phases,
                "scope": "Client boundaries only; drain is local buffering, status line is not first byte; no exact server admission or socket queue time; causal overhead not measured",
            }
        if writer is not None:
            writer.close()
    return result


async def _run(fetch, routes, *, duration, rps, upload_specs, policy, stop_requested=None,
               trace_scheduler=False):
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

    # The ledger retains every result; finished Task objects need not live for
    # the whole arrival window. Keep strong references only while in flight.
    tasks = set()

    def finished(task):
        tasks.discard(task)
        if not task.cancelled():
            task.exception()  # Same exception consumption as terminal gather.

    def launch(row, extra):
        if trace_scheduler:
            row["task_queued_at"] = loop.time() - start
        task = asyncio.create_task(worker(row, extra))
        tasks.add(task)
        task.add_done_callback(finished)

    upload_index = 0
    for row in rows:
        await asyncio.sleep(max(0, start + row["scheduled_at"] - loop.time()))
        if trace_scheduler:
            row["scheduler_awoke_at"] = loop.time() - start
        if stop_requested is not None and stop_requested.is_set():
            break
        launch(row, {})
        while (
            upload_index < len(uploads)
            and uploads[upload_index]["scheduled_at"] <= row["scheduled_at"]
        ):
            spec = upload_specs[upload_index]
            if trace_scheduler:
                uploads[upload_index]["scheduler_awoke_at"] = row["scheduler_awoke_at"]
            launch(
                uploads[upload_index],
                {k: v for k, v in spec.items() if k not in ["at", "path"]},
            )
            upload_index += 1
    if stop_requested is None:
        await asyncio.sleep(max(0, end - loop.time()))
    else:
        while loop.time() < end and not stop_requested.is_set():
            await asyncio.sleep(min(0.05, end - loop.time()))
    window = {
        "dynamic": counts(rows),
        "uploads": counts(uploads),
        "observed_at_seconds": loop.time() - start,
    }
    if stop_requested is None:
        pending = set()
        if tasks:
            _, pending = await asyncio.wait(tasks, timeout=max(0, deadline - loop.time()))
    else:
        pending = set(tasks)
        while pending and loop.time() < deadline and not stop_requested.is_set():
            _, pending = await asyncio.wait(pending, timeout=min(0.05, deadline - loop.time()))
    resource_stopped = stop_requested is not None and stop_requested.is_set()
    sealed = True
    before = {"dynamic": counts(rows), "uploads": counts(uploads)}
    for row in rows + uploads:
        if row["emitted_at"] is not None and row["ended_at"] is None:
            row.update(
                ended_at=loop.time() - start if resource_stopped else duration + policy["drain_seconds"],
                unexpected=True,
                timeout=not resource_stopped,
                status=0,
                error="trial_resource_stop" if resource_stopped else "drain_deadline",
                forced_terminal=True,
            )
    for task in pending:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    report = review(rows, duration=duration, rps=rps, policy=policy)
    if resource_stopped:
        report["verdict"] = "INVALID"
        report["invalid_reasons"].append("trial_resource_stop")
    report.update(
        window_close=window,
        final_before_deadline_classification=before,
        final_upload_counts=counts(uploads),
        samples=rows,
        uploads=uploads,
        actual_elapsed_seconds=loop.time() - start,
        monotonic_origin_seconds=start,
        policy=dict(policy),
        drain_deadline_seconds=duration + policy["drain_seconds"],
        clock="asyncio loop.time monotonic; all timestamps relative to same start",
        emitter="Async tasks, no pending-request cap; whole-request timeout bounds lifetime",
        trial_resource_stopped=resource_stopped,
    )
    if report["final_upload_counts"]["not_emitted"]:
        report["verdict"] = "INVALID"
        report["invalid_reasons"].append("limited_uploads_not_emitted")
    elif report["final_upload_counts"]["failed"] and report["verdict"] != "INVALID":
        report["verdict"] = "FAIL"
    if trace_scheduler:
        report["scheduler_trace"] = {
            "clock": "asyncio loop.time; seconds relative to monotonic_origin_seconds",
            "scope": "Optional client boundaries; scheduler_awoke_at follows the slot sleep; "
                     "task_queued_at precedes create_task; emitted_at remains the whole-request "
                     "coroutine start. Uploads share their dispatching dynamic slot wake. "
                     "No exclusive OS, event-loop, CPU or broker cause; causal overhead not measured.",
            "emission_and_validity_policy_unchanged": True,
        }
    return report


def run_async_open_loop(fetch, routes, *, duration, rps, upload_specs, policy=POLICY,
                        stop_requested=None, trace_scheduler=False):
    return asyncio.run(
        _run(fetch, routes, duration=duration, rps=rps, upload_specs=upload_specs, policy=policy,
             stop_requested=stop_requested, trace_scheduler=trace_scheduler)
    )
