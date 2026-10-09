import collections
import hashlib
import json
import math
from pathlib import Path

out = Path("/tmp/post-cleanup-resource-checkpoint0110")
probe = json.loads((out / "host-idle-samples.jsonl.summary.json").read_text())
s = [json.loads(line) for line in (out / "host-idle-samples.jsonl").read_text().splitlines()]
a, b = s[0], s[-1]
hz = probe["clock_ticks_per_second"]
dt = b["monotonic"] - a["monotonic"]


def numbers(t):
    return {
        line.split()[0]: int(line.split()[1])
        for line in t.splitlines()
        if len(line.split()) == 2 and line.split()[1].isdigit()
    }


hostcpu = sum(b["host_cpu_ticks"][i] - a["host_cpu_ticks"][i] for i in [0, 1, 2, 5, 6]) / hz
other = collections.Counter()
for x, y in zip(s, s[1:]):
    pa = {p["pid"]: p for p in x["processes"]}
    pb = {p["pid"]: p for p in y["processes"]}
    for pid, p in pa.items():
        q = pb.get(pid)
        if q is not None and p["start_ticks"] == q["start_ticks"]:
            other[(p["comm"], p["cgroup"])] += (q["cpu_ticks"] - p["cpu_ticks"]) / hz
limits = {}
for label, key in [("collector", "app_cgroups"), ("sharedPG", "pg_cgroups")]:
    limits[label] = {}
    for group, v in a[key].items():
        z = b[key][group]
        limits[label][group] = {
            k: v[k]
            for k in [
                "cpu.max",
                "cpu.weight",
                "cpuset.cpus.effective",
                "memory.max",
                "memory.high",
                "cpu.pressure",
                "memory.pressure",
                "io.pressure",
            ]
        }
        for name in ["cpu.stat", "memory.events"]:
            before, after = numbers(v[name]), numbers(z[name])
            limits[label][group][name + "_delta"] = (
                {k: after[k] - value for k, value in before.items() if k in after}
                if before
                else "not_measured"
            )
        limits[label][group]["io.stat_first"] = v["io.stat"]
        limits[label][group]["io.stat_last"] = z["io.stat"]
idler = {
    "scope": "HostwithoutownedHTTPload/fixtureprep; ownedemptyDBone metadata connection, normalservicesremain. CPU includes collector, not oldloadbaseline; rootcallerprocess labeledcollector notapplication.",
    "interval_seconds": dt,
    "host_execution_CPU_seconds": hostcpu,
    "host_mean_CPU_cores": hostcpu / dt,
    "mem_available_min_bytes": min(x["meminfo"]["MemAvailable"] for x in s),
    "swap_free_min_bytes": min(x["meminfo"]["SwapFree"] for x in s),
    "vmstat_deltas": {k: b["vmstat"].get(k, v) - v for k, v in a["vmstat"].items()},
    "host_iowait_seconds": (b["host_cpu_ticks"][4] - a["host_cpu_ticks"][4]) / hz,
    "host_steal_seconds": (b["host_cpu_ticks"][7] - a["host_cpu_ticks"][7]) / hz,
    "host_diskstats_first": a["host_diskstats"],
    "host_diskstats_last": b["host_diskstats"],
    "host_PSI": a["host_pressure"],
    "limits": limits,
    "top_persistent_process_CPU_lower_bounds": [
        {"comm": k[0], "cgroup": k[1], "CPU_seconds": v} for k, v in other.most_common(12)
    ],
    "collector": probe,
    "collector_CPU_per_elapsed_second": probe["collector_thread_cpu"] / probe["elapsed"],
    "p95_full_poll_seconds": sorted(probe["sample_durations"])[math.ceil(len(s) * 0.95) - 1],
    "limits_of_measurement": [
        "1Hz sequentialsamples notatomic",
        "CPUtiming collectionoverhead noted; normalservicesactive",
        "IOcounters wholehost/devices/cgroups, sharedlayers notadditive; no individualI/O attribution",
        "UnavailablePSI notzero",
        "CPUidle priorcontextnewonly; never substitute historic6.44/5.95loadCPU",
    ],
}
(out / "host-idle-analysis.json").write_text(json.dumps(idler, indent=2) + "\n")
current = json.loads((out / "block-1-4w/analysis.json").read_text())
historical = json.loads(
    Path("docs/evidencias/comparacion-capacidad-4-vs-6-analisis0110.json").read_text()
)
refs = [h for h in historical["blocks"] if h["workers"] == 4]
comparisons = []
for h in refs:
    c = current["cohort"]
    past = h["cohort"]
    wc = current["window"]
    wh = h["window"]
    comparisons.append(
        {
            "historical_block": h["index"],
            "D_before": past["D_worker_seconds_per_request"],
            "D_after": c["D_worker_seconds_per_request"],
            "D_delta_seconds": c["D_worker_seconds_per_request"]
            - past["D_worker_seconds_per_request"],
            "D_delta_fraction": c["D_worker_seconds_per_request"]
            / past["D_worker_seconds_per_request"]
            - 1,
            "family_mean_delta_seconds": {
                f: c["means_by_family"][f]["mean_wsgi_seconds"]
                - past["means_by_family"][f]["mean_wsgi_seconds"]
                for f in c["means_by_family"]
            },
            "pre_wsgi_mean_delta": c["pre_wsgi_all_entered_mean"]
            - past["pre_wsgi_all_entered_mean"],
            "window_success_delta": wc["counts"]["successful"] - wh["counts"]["successful"],
            "pending_window_delta": wc["counts"]["pending"] - wh["counts"]["pending"],
            "p95_delta": c["observable_latency_seconds"]["p95"]
            - past["observable_latency_seconds"]["p95"],
            "host_load_CPU_before": wh["resources"]["host_mean_CPU_cores"],
            "host_load_CPU_after": wc["resources"]["host_mean_CPU_cores"],
            "host_load_CPU_delta": wc["resources"]["host_mean_CPU_cores"]
            - wh["resources"]["host_mean_CPU_cores"],
            "external_load_CPU_before": wh["resources"]["unrelated_host_residual_mean_CPU_cores"],
            "external_load_CPU_after": wc["resources"]["unrelated_host_residual_mean_CPU_cores"],
            "external_load_CPU_delta": wc["resources"]["unrelated_host_residual_mean_CPU_cores"]
            - wh["resources"]["unrelated_host_residual_mean_CPU_cores"],
        }
    )
D = current["cohort"]["D_worker_seconds_per_request"]
opportunities = []
for f, v in current["cohort"]["means_by_family"].items():
    contribution = v["mean_wsgi_seconds"] / 3
    opportunities.append(
        {
            "family": f,
            "N": v["N"],
            "mean_wsgi_seconds": v["mean_wsgi_seconds"],
            "weight": 1 / 3,
            "D_contribution": contribution,
            "D_fraction": contribution / D,
            "W20_contribution_worker_seconds_per_second": 20 * contribution,
            "direct_mean_thread_CPU_seconds": v["mean_thread_cpu_seconds"],
            "current_SQL_rule_render_breakdown": "not_measured",
            "hypothesis": "Review existingmainSQL/pageconstruction measuredseparately; needcurrentequivalent attribution beforeselectingcodechange"
            if f != "detail"
            else "Lowerabsoluteweightedservice, noextrapolatinglisting/searchgainshere",
        }
    )
valid = all(
    current["checks"][k] for k in ["scenario", "generator", "accounting", "timeout65"]
) and not current.get("trial_stop")
actualparams = json.loads((out / "frozen-manifest.json").read_text())
oldparams = json.loads(
    Path("/tmp/worker-capacity-4-vs-6-ready0110/frozen-manifest.json").read_text()
)
root = Path.cwd()
app = [p for p in oldparams["source_sha256"] if p.startswith(("apps/", "config/"))]
appsame = all(
    hashlib.sha256((root / p).read_bytes()).hexdigest() == oldparams["source_sha256"][p]
    for p in app
)
instrument_names = [
    "scripts/benchmark_accounting.py",
    "scripts/benchmark_async_transport.py",
    "scripts/benchmark_gc_observer.py",
    "scripts/benchmark_resource_observer.py",
    "scripts/benchmark_resource_probe.py",
    "scripts/benchmark_worker_observer.py",
    "scripts/synthetic_load_dataset.py",
]
instrumentsame = all(
    actualparams["source_sha256"][p] == oldparams["source_sha256"][p] for p in instrument_names
)
state1 = json.loads((out / "cleanup-state-before.json").read_text())
state2 = json.loads((out / "cleanup-state-after-idle.json").read_text())
before = {
    r["name"]: [r[k] for k in ["status", "started_at", "finished_at", "restart_count", "host_pid"]]
    for r in state1["containers"]
}
after = {r[0].lstrip("/"): [r[1], r[2], r[3], int(r[4]), int(r[5])] for r in state2["containers"]}
report = {
    "status": "TERMINAL_REVIEWED_ARITHMETIC_PENDING_FINAL_LIVE_REVIEW",
    "validity": "VALID" if valid else "INVALID",
    "historical_comparability": "COMPARABLE" if appsame and instrumentsame else "INCONCLUSIVE",
    "filter_compliance": current["block_verdict"] if valid else "not_applicable_INVALID",
    "interpretation": "COMPARABLEdefensibledescriptivecomparison, neverexclusivecleanupcausality; changedhost intentional. Singlepostblock no causalreplication.",
    "idle": idler,
    "current": current,
    "comparison_to_both_historical4W": comparisons,
    "opportunity_matrix": opportunities,
    "dependency_versions_current": json.loads((out / "dependency-versions.json").read_text()),
    "comparability_evidence": {
        "app_config_matching_files": len(app),
        "app_config_byte_identical": appsame,
        "HTTP_resource_instruments_identical": instrumentsame,
        "fixture": "Sameoriginal10000generator/seedmethods/photo1/upload782134; freshUUID/time-relativevalidity and DBsnapshot notidenticalhistoricremoveddata; noPKsemanticchanges",
        "warmup": "same6cold+30serial and5sidles; PIDpartialcoverageexplicit",
        "harness_changes": "Manifestorders[4]instead4/6/6/4; schemafingerprintcatalogreadbeforewarmup; runneridle30spre-fixture; no requestpath/instruments/backendchange",
        "historical_full_installed_dependency_SHA": "not_measured",
        "historical_direct_schema_fingerprint": "not_measured",
        "current_schema_fingerprint": json.loads((out / "schema-fingerprint.json").read_text())[
            "sha256"
        ],
        "historical_source_dependency_declarations_identical": {
            p: actualparams["source_sha256"][p] == h
            for p, h in oldparams["source_sha256"].items()
            if any(t in p for t in ["requirements", "pyproject.toml", "uv.lock"])
            and p in actualparams["source_sha256"]
        },
    },
    "cleanup_context": {
        "before": state1,
        "after_idle": state2,
        "inventory_stable_over_characterization": before == after,
        "cleanup_exact_completion_time": "not_measured",
        "removed_container_names_and_freed_CPU_memory_IO": "not_measured",
        "observed_noactivecleanup_processes": True,
        "completion_basis": "Userstatescompletedcleanup; currentnoactivecleanup/stableinventory verified, not an operator globalcompletionacta.",
    },
    "upload_frequency": "Contractual1/min only; U=singleuploadWSGI/60 with N1uncertainty. No inferred2/minfrequency.",
    "contract": "CR09open/goalpaused;4reference6candidateNotAdopted;historicFAIL/INVALIDpercentagesunchanged;20RPS900scontractblocked; noauto60/900",
    "decision": "PENDING_ROOT_REVIEW",
}
(out / "post-cleanup-analysis.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n"
)
print(
    json.dumps(
        {
            k: report[k]
            for k in [
                "validity",
                "historical_comparability",
                "filter_compliance",
                "comparison_to_both_historical4W",
                "opportunity_matrix",
            ]
        },
        indent=2,
    )
)
