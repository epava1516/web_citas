"""Read-only diagnosis: cohort correlations and measured resource scope."""

import json
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

p = Path(sys.argv[1])
s = json.loads((p / "load-summary.json").read_text())
rows = json.loads((p / "benchmark-samples.json").read_text())["dynamic"]
events = json.loads((p / "benchmark-worker-events.json").read_text())
groups = defaultdict(lambda: defaultdict(list))
for e in events["events"]:
    groups[e["id"]][e["event"]].append(e)
assert not s["invalid_reasons"] and s["counts"]["reconciled"]
assert all(
    s["generator_delay_seconds"][k] <= v for k, v in [("p95", 0.01), ("p99", 0.025), ("max", 0.1)]
)
assert not events["parse_errors"] and len(rows) == 600 and len({r["id"] for r in rows}) == 600
origin = s["monotonic_origin_seconds"]
families = defaultdict(list)
before = []
intervals = defaultdict(list)
routes = Counter()
after_deadline = 0
cpu_sum = 0
for r in rows:
    g = groups[r["id"]]
    assert len(g["wsgi_start"]) == len(g["wsgi_end"]) == 1
    a, b = g["wsgi_start"][0], g["wsgi_end"][0]
    assert a["pid"] == b["pid"]
    entry = a["started"]
    exit = entry + b["wall"]
    assert entry >= origin + r["emitted_at"] and exit >= entry
    f = "detail" if "/listing/" in r["path"] else "search" if "?" in r["path"] else "listing"
    families[f].append(b)
    before.append(entry - origin - r["emitted_at"])
    intervals[a["pid"]].append((entry, exit))
    cpu_sum += b["thread_cpu"]
    after_deadline += entry > origin + r["emitted_at"] + 65
    for route in g["publication_route"]:
        routes[(route["route"], route.get("reason"), route.get("native_unknown"))] += 1
for items in intervals.values():
    items.sort()
    assert all(a[1] <= b[0] + 0.002 for a, b in zip(items, items[1:]))
means = {
    k: {
        "population": len(v),
        "wsgi_mean_seconds": statistics.mean(x["wall"] for x in v),
        "thread_cpu_mean_seconds": statistics.mean(x["thread_cpu"] for x in v),
    }
    for k, v in families.items()
}
assert all(v["population"] == 200 for v in means.values())
D = sum(v["wsgi_mean_seconds"] for v in means.values()) / 3
u = groups["u-0"]
assert len(u["wsgi_end"]) == 1
U = u["wsgi_end"][0]["wall"] / 60
resources = [json.loads(line) for line in (p / "resource-samples.jsonl").read_text().splitlines()]
em = [r for r in resources if origin <= r["monotonic"] <= origin + 30]
a, b = em[0], em[-1]
dt = b["monotonic"] - a["monotonic"]
hz = os.sysconf("SC_CLK_TCK")
host = sum(b["host_cpu_ticks"][i] - a["host_cpu_ticks"][i] for i in [0, 1, 2, 5, 6]) / hz / dt
old = {x["pid"]: x for x in a["processes"]}
pgscope = next(iter(a["pg_cgroups"]))
pgscope = "/" + pgscope
workerpids = set(intervals)
appcpu = pgcpu = 0
other = []
for x in b["processes"]:
    prev = old.get(x["pid"])
    if not prev or prev["start_ticks"] != x["start_ticks"]:
        continue
    cpu = (x["cpu_ticks"] - prev["cpu_ticks"]) / hz / dt
    if x["pid"] in workerpids:
        appcpu += cpu
    elif x["cgroup"] == pgscope:
        pgcpu += cpu
    else:
        other.append({"pid": x["pid"], "comm": x["comm"], "cpu_cores": cpu})
occupied = {
    str(pid): sum(max(0, min(end, origin + 30) - max(start, origin)) for start, end in values) / 30
    for pid, values in intervals.items()
}
# Upload occupancy is separately included in the relevant worker.
ua, ub = u["wsgi_start"][0], u["wsgi_end"][0]
occupied[str(ua["pid"])] += (
    max(0, min(ua["started"] + ub["wall"], origin + 30) - max(ua["started"], origin)) / 30
)
waits = Counter(
    str((x[2], x[3], x[4], x[5]))
    for r in em
    for x in r["pg_activity"]
    if isinstance(r["pg_activity"], list)
)
result = {
    "validity": "VALID",
    "workload_filter": "FAIL",
    "diagnostic_collection": "complete",
    "families": means,
    "D_seconds": D,
    "20D_worker_seconds_per_second": 20 * D,
    "U_worker_seconds_per_second": U,
    "W_worker_seconds_per_second": 20 * D + U,
    "pre_wsgi_seconds": {
        "population": len(before),
        "mean": statistics.mean(before),
        "median": statistics.median(before),
    },
    "request_thread_cpu_total_seconds": cpu_sum,
    "worker_occupancy_during_emission_including_upload": occupied,
    "requests_entering_wsgi_after_client_deadline": after_deadline,
    "route_counts": [
        {"route": k[0], "reason": k[1], "native_unknown": k[2], "calls": v}
        for k, v in routes.items()
    ],
    "resource_emission_interval": {
        "seconds": dt,
        "samples": len(em),
        "host_execution_cpu_cores": host,
        "four_workers_stable_process_cpu_cores": appcpu,
        "postgres_shared_stable_process_cpu_cores": pgcpu,
        "other_top_stable_processes": sorted(other, key=lambda x: x["cpu_cores"], reverse=True)[:8],
        "pg_state_samples": dict(waits),
    },
    "collector": json.loads((p / "resource-samples.jsonl.summary.json").read_text()),
    "limits": {
        "resource_stop_observed": any(x["trial_stop"] for x in resources),
        "memavailable_min_bytes": min(r["meminfo"]["MemAvailable"] for r in resources),
    },
    "limitations": [
        "WSGI/threadCPU not SQL/validation breakdown; residual WSGI wall includes waits, scheduling and all other work",
        "Request threadCPU excludes other threads; process CPU endpoints omit transient processes",
        "Process resource scope sampled over interior emission interval, not exact full window",
        "PostgreSQL counters shared; wait-state sample counts are not duration",
        "Pre-WSGI does not identify socket/Gunicorn queue",
        "Upload U N1 estimate at contractual one/minute",
        "Observer overhead not causally quantified; collector CPU reported",
        "No causal improvement versus separate 60s gate or laptop; no capacity acceptance",
    ],
    "decision": "Observed worker occupancy/service demand exceeds four workers at 20RPS; request threadCPU is lower than WSGI wall. Investigate measured waits/scheduling/shared resources before selecting further refactor or concurrency. No automatic new load or 900s.",
}
print(json.dumps(result, indent=2))
