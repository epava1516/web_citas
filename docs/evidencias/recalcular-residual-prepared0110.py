"""Offline review of raw paired TCP/WSGI ledgers; no DB/network or code execution."""

import hashlib
import json
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/residual-prepared-tcp-ready0110")
results = []
for fixture in ["contractual", "diverse"]:
    x = json.loads((root / (fixture + ".json")).read_text())
    samples = x["samples"]
    assert len(samples) == 64
    assert len({s["id"] for s in samples}) == 64
    ends = [r for r in x["observer_records"] if r["event"] == "wsgi_end"]
    assert len({r["id"] for r in ends}) == len(ends)
    by_id = {r["id"]: r for r in ends}
    starts = {r["id"]: r for r in x["observer_records"] if r["event"] == "wsgi_start"}
    for s in samples:
        event = by_id[s["id"]]
        assert (
            event["pid"] == s["worker_pid"]
            and event["status"] == 200
            and event["error_type"] is None
        )
        assert event["monotonic"] >= starts[s["id"]]["monotonic"]
        assert s["wsgi_seconds"] == event["wall"]
        assert (
            s["positive"] == 10000 and s["unknown"] == 0 and s["reason"] == "audited_current_values"
        )
        if s["mode"] == "B":
            assert s["prepared_count"] > 0
    medians = {
        f: {
            m: statistics.median(
                s["seconds"] for s in samples if s["family"] == f and s["mode"] == m
            )
            for m in "AB"
        }
        for f in x["medians"]
    }
    deltas = [
        statistics.mean(
            next(
                s["seconds"]
                for s in samples
                if s["pair"] == pair and s["family"] == f and s["mode"] == "A"
            )
            - next(
                s["seconds"]
                for s in samples
                if s["pair"] == pair and s["family"] == f and s["mode"] == "B"
            )
            for f in medians
        )
        for pair in range(8)
    ]
    threshold = max(0.05, 0.08 * statistics.mean(v["A"] for v in medians.values()))
    regress = {f: v["B"] - v["A"] for f, v in medians.items()}
    means = {
        f: {
            m: statistics.mean(
                by_id[s["id"]]["wall"] for s in samples if s["family"] == f and s["mode"] == m
            )
            for m in "AB"
        }
        for f in medians
    }
    family_means = {
        f: {m: statistics.mean(v[m] for k, v in means.items() if k.startswith(f)) for m in "AB"}
        for f in ["listing", "search"]
    }
    family_delta = {f: v["A"] - v["B"] for f, v in family_means.items()}
    contribution = sum(family_delta.values()) / 3
    effect = (
        statistics.median(deltas) >= threshold
        and sum(d > 0 for d in deltas) >= 6
        and all(regress[f] <= max(0.025, 0.05 * medians[f]["A"]) for f in medians)
    )
    assert effect == x["prepared_effect"]["effect"] and not effect
    assert abs(contribution - x["delta_D_observed_affected_routes"]) < 1e-12
    sessions = {
        str(pid): sorted(
            {s["postgres_pid"] for s in x["warmup"] + samples if s["worker_pid"] == pid}
        )
        for pid in {s["worker_pid"] for s in samples}
    }
    plans = []
    for f, data in x["session_diagnosis"]["families"].items():
        for mode, p in data["plans_separate"].items():
            indexes = []

            def walk(n):
                if "Index Name" in n:
                    indexes.append(n["Index Name"])
                for child in n.get("Plans", []):
                    walk(child)

            walk(p[0]["Plan"])
            plans.append(
                {
                    "family": f,
                    "mode": mode,
                    "planning_ms": p[0]["Planning Time"],
                    "execution_ms": p[0]["Execution Time"],
                    "indexes_used": sorted(set(indexes)),
                    "scope": "Owned parent session before ANALYZE; forced plan modes diagnostic only, not the HTTP worker plans. Runtime custom/generic worker counts not_measured.",
                }
            )
    results.append(
        {
            "fixture": fixture,
            "HTTP_samples": 64,
            "pairs": 8,
            "family_WSGI_population_per_mode": 16,
            "means_WSGI_seconds": family_means,
            "HTTP_medians_seconds": medians,
            "median_paired_HTTP_saving_seconds": statistics.median(deltas),
            "required_saving_seconds": threshold,
            "favorable_pairs": sum(d > 0 for d in deltas),
            "family_HTTP_regressions_seconds": regress,
            "effect_accepted": effect,
            "delta_WSGI_mean_seconds_by_family": family_delta,
            "delta_D_contribution_measured_listing_search": contribution,
            "delta_W20_contribution_measured_listing_search": 20 * contribution,
            "total_delta_D_contractual_mixture": "not_measured; detail not sampled, no serial-to-saturated extrapolation",
            "uploads": "not_measured; no uploads in serial controls, not assigned dynamic savings",
            "sessions_by_worker": sessions,
            "warmup_requests": len(x["warmup"]),
            "real_prepared_names": x["session_diagnosis"],
            "separate_index_and_plan_review": plans,
            "equivalence": x["driver_equivalence"],
            "statistic_endpoints_equal": x["statistics_endpoints_equal"],
            "server_stopped": x["own_server_stopped"],
        }
    )
result = {
    "decision": "REJECTED_NOT_ADOPTED",
    "fixtures": results,
    "scope": "One server-binding named prepared scalar-read intervention, current SQL/binds unchanged. Functional checks pass, material HTTP effect fails both fixtures. No backend adoption, no force-custom retry, no load/gates.",
    "limits": [
        "Parent custom/generic plans precede ANALYZE, HTTP workers run after ANALYZE. Do not attribute regression exclusively to a plan/index change; worker runtime plan choice not_measured.",
        "Server binding and preparation together form the candidate; HTTP difference is not pure planning savings.",
        "Independent construction vs compilation vs document metadata not_measured in simple captured-constructor timer; cProfile events nested/lazy and overhead substantial.",
        "WSGI observer wall includes matched instrumentation; causal overhead not_measured. Current means are serial diagnostic populations distinct from postcleanup200/family.",
        "SQL rows_returned only direct fetched vectors. rows_affected/globalrows_scanned/PG CPU/wait duration not_measured.",
        "CONN_MAX_AGE60 retained; actual session replacement visible in per-worker backend IDs. Do not pretend every request reuses one plan.",
    ],
    "raw_sha256": {
        f: hashlib.sha256((root / f).read_bytes()).hexdigest()
        for f in ["contractual.json", "diverse.json"]
    },
}
print(json.dumps(result, ensure_ascii=False, indent=2))
