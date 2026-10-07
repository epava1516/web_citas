"""Open-loop benchmark accounting with a fixed window and final drain deadline."""

import concurrent.futures
import copy
import math
import threading
import time

POLICY = {
    "generator_p95_seconds_max": 0.010,
    "generator_p99_seconds_max": 0.025,
    "generator_max_seconds_max": 0.100,
    "not_emitted_fraction_max": 0.0,
    "request_timeout_seconds": 65.0,
    "drain_seconds": 70.0,
    "latency_p95_seconds_strict_max": 0.800,
    "error_fraction_strict_max": 0.01,
    "late_emission": "Never emit after the arrival window; count as not emitted",
    "final_pending": "Classify as failed/timeout at fixed drain deadline",
    "emission": "Worker begins urllib call, before connection/open/read; executor wait included only in generator delay",
    "justification": "20rps gives 50ms intervals: p95 jitter 1/5 interval, p99 1/2 interval, max two intervals; zero missing arrivals preserves full18000. Drain70s=timeout65s+5s margin.",
}


def distribution(values):
    values = sorted(values)
    return {
        **{
            f"p{p}": values[max(0, math.ceil(len(values) * p / 100) - 1)] if values else None
            for p in [50, 90, 95, 99]
        },
        "max": values[-1] if values else None,
        "population": len(values),
    }


def counts(rows):
    emitted = [r for r in rows if r.get("emitted_at") is not None]
    ended = [r for r in emitted if r.get("ended_at") is not None]
    failures = [r for r in ended if r["unexpected"]]
    result = {
        "scheduled": len(rows),
        "emitted": len(emitted),
        "not_emitted": len(rows) - len(emitted),
        "successful": len(ended) - len(failures),
        "failed": len(failures),
        "pending": len(emitted) - len(ended),
        "timeouts": sum(bool(r.get("timeout")) for r in failures),
    }
    result["other_errors"] = result["failed"] - result["timeouts"]
    result["reconciled"] = (
        result["scheduled"] == result["emitted"] + result["not_emitted"]
        and result["emitted"] == result["successful"] + result["failed"] + result["pending"]
        and result["failed"] == result["timeouts"] + result["other_errors"]
    )
    return result


def review(rows, *, duration, rps, policy, scenario_valid=True):
    accounting = counts(rows)
    emitted = [r for r in rows if r.get("emitted_at") is not None]
    ended = [r for r in emitted if r.get("ended_at") is not None]
    lag = distribution([r["emitted_at"] - r["scheduled_at"] for r in emitted])
    latency = distribution([r["ended_at"] - r["emitted_at"] for r in ended])
    total_delay = distribution([r["ended_at"] - r["scheduled_at"] for r in ended])
    invalid = []
    if not scenario_valid or len(rows) != int(duration * rps):
        invalid.append("scenario_or_scheduled_population")
    if not accounting["reconciled"]:
        invalid.append("accounting")
    missing = accounting["not_emitted"] / accounting["scheduled"] if rows else 1
    if missing > policy["not_emitted_fraction_max"]:
        invalid.append("not_emitted_fraction")
    for key in ["p95", "p99", "max"]:
        threshold = policy[f"generator_{key}_seconds_max"]
        if lag[key] is None or lag[key] > threshold:
            invalid.append("generator_delay_" + key)
    if accounting["pending"]:
        invalid.append("unclassified_final_pending")
    if any(r["ended_at"] < r["emitted_at"] or r["emitted_at"] < r["scheduled_at"] for r in ended):
        invalid.append("monotonic_time_order")
    error_fraction = accounting["failed"] / accounting["emitted"] if emitted else None
    verdict = (
        "INVALID"
        if invalid
        else (
            "PASS"
            if latency["p95"] is not None
            and latency["p95"] < policy["latency_p95_seconds_strict_max"]
            and error_fraction < policy["error_fraction_strict_max"]
            else "FAIL"
        )
    )
    bins = []
    for second in range(math.ceil(duration)):
        bins.append(
            {
                "second": second,
                "emitted": sum(second <= r["emitted_at"] < second + 1 for r in emitted),
                "completed": sum(second <= r["ended_at"] < second + 1 for r in ended),
            }
        )
    return {
        "verdict": verdict,
        "invalid_reasons": invalid,
        "counts": accounting,
        "generator_delay_seconds": lag,
        "observable_latency_seconds": latency,
        "total_delay_seconds": total_delay,
        "error_fraction_emitted": error_fraction,
        "not_emitted_fraction_scheduled": missing,
        "requested_rps": rps,
        "emitted_per_window_second": accounting["emitted"] / duration,
        "completed_per_window_second": sum(r["ended_at"] <= duration for r in ended) / duration,
        "arrival_second_bins": bins,
        "percentile_population": "All emitted terminated requests, including errors/timeouts; no successful-only filter",
    }


def run_open_loop(fetch, routes, *, duration, rps, upload_specs, policy=POLICY):
    """Fetch accepts path, benchmark_id, scheduled; uploads additionally accept data/headers/expected."""
    start = time.monotonic()
    end = start + duration
    drain_deadline = end + policy["drain_seconds"]
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
    lock = threading.Lock()
    sealed = False

    def worker(row, extra):
        nonlocal sealed
        now = time.monotonic()
        with lock:
            if sealed or now >= end:
                row["not_emitted_reason"] = "arrival_window_closed"
                return
            row["emitted_at"] = now - start
        try:
            payload = fetch(
                row["path"], benchmark_id=row["id"], scheduled=start + row["scheduled_at"], **extra
            )
        except Exception as error:
            payload = {
                "unexpected": True,
                "status": 0,
                "error": type(error).__name__,
                "timeout": isinstance(error, TimeoutError),
            }
        ended = time.monotonic() - start
        with lock:
            if not sealed:
                row.update(payload, ended_at=ended)

    dynamic_pool = concurrent.futures.ThreadPoolExecutor(max_workers=80)
    upload_pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    active = set()
    futures = []
    upload_index = 0
    for row in rows:
        target = start + row["scheduled_at"]
        time.sleep(max(0, target - time.monotonic()))
        active = {future for future in active if not future.done()}
        if len(active) >= 80 or time.monotonic() >= end:
            with lock:
                row["not_emitted_reason"] = "emitter_capacity_or_window"
        else:
            future = dynamic_pool.submit(worker, row, {})
            active.add(future)
            futures.append(future)
        while (
            upload_index < len(uploads)
            and uploads[upload_index]["scheduled_at"] <= row["scheduled_at"]
        ):
            spec = upload_specs[upload_index]
            futures.append(
                upload_pool.submit(
                    worker,
                    uploads[upload_index],
                    {k: v for k, v in spec.items() if k not in ["at", "path"]},
                )
            )
            upload_index += 1
    time.sleep(max(0, end - time.monotonic()))
    with lock:
        window = {
            "dynamic": counts(rows),
            "uploads": counts(uploads),
            "observed_at_seconds": time.monotonic() - start,
        }
    concurrent.futures.wait(futures, timeout=max(0, drain_deadline - time.monotonic()))
    with lock:
        sealed = True
        pending_before_classification = {"dynamic": counts(rows), "uploads": counts(uploads)}
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
        final_rows, final_uploads = copy.deepcopy(rows), copy.deepcopy(uploads)
    for pool in [dynamic_pool, upload_pool]:
        pool.shutdown(wait=False, cancel_futures=True)
    report = review(final_rows, duration=duration, rps=rps, policy=policy)
    report.update(
        window_close=window,
        final_before_deadline_classification=pending_before_classification,
        final_upload_counts=counts(final_uploads),
        samples=final_rows,
        uploads=final_uploads,
        actual_elapsed_seconds=time.monotonic() - start,
        policy=dict(policy),
        drain_deadline_seconds=duration + policy["drain_seconds"],
        clock="time.monotonic; all recorded timestamps relative to same start",
    )
    if report["final_upload_counts"]["not_emitted"]:
        report["verdict"] = "INVALID"
        report["invalid_reasons"].append("limited_uploads_not_emitted")
    elif report["final_upload_counts"]["failed"] and report["verdict"] != "INVALID":
        report["verdict"] = "FAIL"
    return report
