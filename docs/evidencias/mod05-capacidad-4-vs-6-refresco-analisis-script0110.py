"""Read-only recalculation of the authorized 4/6/6/4 normal_worker_beat comparison.

Argument: raw experiment directory. No DB, HTTP, workload or source mutation.
Adapted from recalcular-comparacion-capacidad0110.py: owned Celery worker/Beat CPU is
removed from the unrelated-host residual, and MOD05 refresh metrics are added.
"""
import collections
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

out = Path(sys.argv[1])
result = json.loads((out / "result.json").read_text())
for name, digest in result["artifact_sha256"].items():
    assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest, name


def family(path):
    return "search" if "?q=" in path else "detail" if "/listing/" in path else "listing"


def percentile(values, ratio):
    return sorted(values)[max(0, math.ceil(len(values) * ratio) - 1)]


def numbers(value):
    return {line.split()[0]: int(line.split()[1]) for line in value.splitlines()
            if len(line.split()) == 2 and line.split()[1].isdigit()}


blocks = []
for folder in sorted(out.glob("block-*")):
    summary = json.loads((folder / "load-summary.json").read_text())
    assert summary["refresh_mode"] == "normal_worker_beat"
    raw = json.loads((folder / "benchmark-samples.json").read_text())
    events = json.loads((folder / "benchmark-worker-events.json").read_text())["events"]
    probe = json.loads((folder / "resource-samples.jsonl.summary.json").read_text())
    snapshots = [json.loads(line) for line in (folder / "resource-samples.jsonl").read_text().splitlines()]
    ends, routes = {}, {}
    for event in events:
        if event["event"] == "wsgi_end":
            assert event["id"] not in ends
            ends[event["id"]] = event
        elif event["event"] == "publication_route":
            routes[event["id"]] = event
    rows = raw["dynamic"]
    assert len(rows) == len({r["id"] for r in rows}) == 600
    assert collections.Counter(family(r["path"]) for r in rows) == {"listing": 200, "search": 200, "detail": 200}
    assert all(r["emitted_at"] is not None and r["ended_at"] is not None and r["id"] in ends for r in rows)
    delay = [r["emitted_at"] - r["scheduled_at"] for r in rows]
    generator_valid = percentile(delay, .95) <= .01 and percentile(delay, .99) <= .025 and max(delay) <= .1
    means = {f: statistics.mean(ends[r["id"]]["wall"] for r in rows if family(r["path"]) == f)
             for f in ["listing", "search", "detail"]}
    cpu_means = {f: statistics.mean(ends[r["id"]]["thread_cpu"] for r in rows if family(r["path"]) == f)
                 for f in ["listing", "search", "detail"]}
    D = sum(means.values()) / 3
    upload = raw["uploads"][0]
    assert len(raw["uploads"]) == 1 and upload["status"] == 302
    U_wall = ends[upload["id"]]["wall"]
    W = 20 * D + U_wall / 60
    success_window = sum(r["ended_at"] <= 30 and not r["unexpected"] for r in rows)
    unknown = collections.Counter(
        (routes[r["id"]].get("route"), routes[r["id"]].get("native_unknown"))
        for r in rows if family(r["path"]) != "detail" and r["id"] in routes)
    # Resources over the emission window.
    origin = summary["monotonic_origin_seconds"]
    window = [s for s in snapshots if origin <= s["monotonic"] <= origin + 30]
    a, b = window[0], window[-1]
    dt = b["monotonic"] - a["monotonic"]
    hz, master = probe["clock_ticks_per_second"], probe["app_master_pid"]
    pa = {p["pid"]: p for p in a["processes"]}
    client = pa[master]["ppid"]
    runner = pa[client]["ppid"]
    celery = {pid for pids in summary["celery_pids"].values() for pid in pids}
    app_cpu = own_cpu = celery_cpu = 0
    for x, y in zip(window, window[1:]):
        first, last = {p["pid"]: p for p in x["processes"]}, {p["pid"]: p for p in y["processes"]}
        for pid, p in first.items():
            q = last.get(pid)
            if not q or p["start_ticks"] != q["start_ticks"]:
                continue
            cpu = (q["cpu_ticks"] - p["cpu_ticks"]) / hz
            if pid == master or p["ppid"] == master:
                app_cpu += cpu
            elif pid in celery:
                celery_cpu += cpu
            elif pid in {client, runner}:
                own_cpu += cpu

    def pg_cpu(sample):
        return numbers(next(iter(sample["pg_cgroups"].values()))["cpu.stat"])["usage_usec"] / 1e6

    shared_pg_cpu = pg_cpu(b) - pg_cpu(a)
    host_cpu = sum(b["host_cpu_ticks"][i] - a["host_cpu_ticks"][i] for i in [0, 1, 2, 5, 6]) / hz
    external = (host_cpu - app_cpu - shared_pg_cpu - own_cpu - celery_cpu) / dt
    # Refresh: executions, cost, delay, invalidations.
    celery_events = [json.loads(line) for p in (folder / "celery-events-raw").glob("*.jsonl")
                     for line in p.read_text().splitlines()]
    published = {e["id"]: e["role"] for e in celery_events if e["event"] == "publish"}
    executions = [e for e in celery_events if e["event"] == "execution"]
    refresh = [e for e in executions if e["task"].endswith("refresh_publication_state")]
    load_refresh = [e for e in refresh if origin <= e["start_monotonic"] <= origin + 100]
    delays = [d for e in refresh for d in e.get("mark_to_clear_seconds", [])]
    samples = [json.loads(line) for line in (folder / "publication-samples.jsonl").read_text().splitlines()]
    load_samples = [s for s in samples if s["phase"] == "arrivals_and_drain"]
    p95 = percentile([r["ended_at"] - r["emitted_at"] for r in rows], .95)
    blocks.append(dict(
        index=summary["index"], workers=summary["workers"], harness_verdict=summary["verdict"],
        invalid_reasons=summary.get("invalid_reasons"), generator_valid=generator_valid,
        success_window=success_window, pending_window=600 - success_window,
        p95_observable_seconds=p95, error_fraction=sum(r["unexpected"] for r in rows) / 600,
        wsgi_mean_seconds=means, thread_cpu_mean_seconds=cpu_means, D=D, upload_wall_seconds=U_wall,
        W20_plus_upload_per_minute=W, read_routes=dict((f"{k[0]}/unknown{k[1]}", v) for k, v in unknown.items()),
        cpu_cores_window={"app": app_cpu / dt, "shared_pg": shared_pg_cpu / dt, "owned_celery": celery_cpu / dt,
                          "own_client_runner": own_cpu / dt, "unrelated_host_residual": external},
        refresh={
            "executions_total": len(refresh),
            "executions_by_origin": dict(collections.Counter(published.get(e["id"], "not_observed") for e in refresh)),
            "executions_load_and_drain": len(load_refresh),
            "wall_seconds_sum": sum(e["wall"] for e in refresh),
            "thread_cpu_seconds_sum": sum(e["thread_cpu"] for e in refresh),
            "processed_sum": sum(e["result"] for e in refresh if isinstance(e["result"], int)),
            "cleared_sum": sum(e.get("cleared", 0) for e in refresh),
            "mark_to_clear_seconds_upper_bound": sorted(delays),
            "dirty_samples_load_nonzero": sum(s["dirty"] > 0 for s in load_samples),
            "dirty_samples_load_total": len(load_samples),
            "max_oldest_mark_age_load_seconds": max((s["oldest_mark_age_seconds"] or 0 for s in load_samples), default=None),
            "generation_delta_block": samples[-1]["generation_last_value"] - samples[0]["generation_last_value"],
            "process_blob": [{"wall": e["wall"], "thread_cpu": e["thread_cpu"], "origin": published.get(e["id"])}
                             for e in executions if e["task"].endswith("process_blob")],
            "other_tasks_wall_seconds_sum": sum(e["wall"] for e in executions
                                                if not e["task"].endswith(("refresh_publication_state", "process_blob"))),
        },
        beat_alignment=summary["beat_alignment"],
    ))
assert [b["workers"] for b in blocks] == [4, 6, 6, 4]
spread = max(b["cpu_cores_window"]["unrelated_host_residual"] for b in blocks) - \
    min(b["cpu_cores_window"]["unrelated_host_residual"] for b in blocks)
pairs = []
for four, six in [(blocks[0], blocks[1]), (blocks[3], blocks[2])]:
    pairs.append(dict(
        four_block=four["index"], six_block=six["index"],
        completion_improvement=six["success_window"] / four["success_window"] - 1,
        p95_lower=six["p95_observable_seconds"] < four["p95_observable_seconds"],
        errors_not_higher=six["error_fraction"] <= four["error_fraction"],
        D_ratio=six["D"] / four["D"],
        prefixed_effect_pass=six["success_window"] >= 1.1 * four["success_window"]
        and six["p95_observable_seconds"] < four["p95_observable_seconds"]
        and six["error_fraction"] <= four["error_fraction"] and six["D"] <= 1.1 * four["D"]))
print(json.dumps(dict(
    blocks=blocks, pairs=pairs, unrelated_host_residual_range_cores=spread,
    causal="INCONCLUSIVE" if spread > .5 else "WITHIN_HOST_BOUND",
    scope=("normal_worker_beat, four 30 s blocks, 20 RPS, 10.000 listings, 1 upload per block. Not a 60 s gate "
           "nor the 900 s contract. Sequential blocks on a shared host; resource windows are interior emission "
           "windows; sampled PG states are not durations. Refresh delay is an upper bound on the database clock. "
           "No causal comparison with without_worker_beat_eager_signal results."),
), indent=2))
