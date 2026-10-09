"""Recalculate the prefixed dirty-scope intervention criteria from original TCP samples.

Usage: python mod05-sucios-acotados-analisis-script0110.py JUNIT.xml RAW_ROOT OUTPUT.json
"""
import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

junit, raw_root, destination = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
cases = []
for testcase in ET.parse(junit).getroot().iter("testcase"):
    assert testcase.find("failure") is None and testcase.find("error") is None, testcase.get("name")
    props = {p.get("name"): p.get("value") for p in testcase.iter("property")}
    d = json.loads(props["tcp_matrix"])
    rows = d["samples"]
    events = {e["id"]: e for e in d["wsgi_events"]}
    assert len(events) == len(rows) == len({s["id"] for s in rows}) == 240
    assert d["dirty_scope_contrast"] and d["controls_per_route_per_block"] == 10 and d["workers"] == 4
    assert d["blocks"] == ["before", "after", "after", "before"]
    raw = []
    for raw_file in (raw_root / f"order-tcp-{d['fixture']}-10000").glob("worker-*.jsonl"):
        for line in raw_file.read_text().splitlines():
            event = json.loads(line)
            assert event["pid"] == int(raw_file.stem.split("-")[1])
            raw.append(event)
    assert len(raw) == len({e["id"] for e in raw}) == 240
    assert sorted(raw, key=lambda e: e["id"]) == sorted(d["wsgi_events"], key=lambda e: e["id"])

    def family(path):
        return "detail" if "/listing/" in path else "search" if "?" in path else "listing"

    for s in rows:
        e = events[s["id"]]
        assert s["status"] == 200 and e["order_variant"] == s["phase"]
        assert s["emission"] <= e["entry"] <= e["exit"] and s["end"] >= e["entry"]
        if family(s["path"]) != "detail":
            assert e["route"] == {"route": "state", "reason": "trusted_state", "native_unknown": 1}
    pids = {e["pid"] for e in events.values()}
    assert not any(Path(f"/proc/{pid}").exists() for pid in pids)

    def population(f, phase=None, block=None):
        pop = [s for s in rows if family(s["path"]) == f
               and (phase is None or s["phase"] == phase) and (block is None or s["block"] == block)]
        assert len(pop) == (20 if block is not None else 40)
        return pop

    def mean(metric, f, phase=None, block=None):
        # Two ES/EN routes per family with equal counts: the plain mean weighs each 1/2.
        return statistics.mean(
            s["end"] - s["emission"] if metric == "http" else events[s["id"]]["exit"] - events[s["id"]]["entry"]
            for s in population(f, phase, block))

    families = {f: {"population_per_variant": 40,
                    **{f"{v}_{m}_mean_seconds": mean(m, f, v) for v in ["before", "after"] for m in ["http", "wsgi"]},
                    "observed_wsgi_delta_seconds": mean("wsgi", f, "before") - mean("wsgi", f, "after")}
                for f in ["listing", "search", "detail"]}
    pairs = []
    for b, a in [(0, 1), (3, 2)]:
        for f in ["listing", "search", "detail"]:
            old, new = mean("http", f, block=b), mean("http", f, block=a)
            delta = old - new
            target = f != "detail"
            met = (delta >= .02 and delta / old >= .05) if target else new - old <= max(.01, .05 * old)
            pairs.append({"before_block": b, "after_block": a, "family": f, "population_per_cell": 20,
                          "target": target, "before_mean_seconds": old, "after_mean_seconds": new,
                          "improvement_seconds": delta, "improvement_fraction": delta / old,
                          "allowed_regression_seconds": None if target else max(.01, .05 * old),
                          "criterion_met": met})
    plans = []
    unknown_state_after = None
    for p in json.loads(props["order_plans"]):
        plan = p["plan"][0] if isinstance(p["plan"], list) else p["plan"]
        sql = p["normalized"]
        operation = ("state_check" if sql.startswith("SELECT NOT EXISTS") else "count"
                     if sql.startswith("SELECT COUNT") else "unknown" if sql.startswith("SELECT DISTINCT")
                     or "LIMIT 49" in sql else "page")
        scans = []

        def walk(node):
            if node.get("Relation Name") == "listings_publicationstate":
                scans.append({k: node.get(k, "not_measured") for k in [
                    "Node Type", "Actual Rows", "Actual Loops", "Shared Hit Blocks",
                    "Shared Read Blocks", "Parent Relationship", "Subplan Name"]})
            for child in node.get("Plans", []):
                walk(child)

        walk(plan["Plan"])
        if p["variant"] == "after" and operation == "unknown":
            unknown_state_after = bool(scans)
        plans.append({"variant": p["variant"], "operation": operation, "normalized": sql,
                      "driver_execute_seconds": p["driver_execute_seconds"], "jit": p["jit"],
                      "planning_ms": plan.get("Planning Time", "not_measured"),
                      "execution_ms": plan.get("Execution Time", "not_measured"),
                      "state_scans": scans, "root_actual_rows": plan["Plan"].get("Actual Rows", "not_measured"),
                      "root_shared_hits": plan["Plan"].get("Shared Hit Blocks", "not_measured"),
                      "root_shared_reads": plan["Plan"].get("Shared Read Blocks", "not_measured")})
    ops = sorted((p["variant"], p["operation"]) for p in plans)
    assert ops == sorted([("before", o) for o in ["unknown", "count", "page"]]
                         + [("after", o) for o in ["state_check", "unknown", "count", "page"]]), ops
    delta_d = sum(x["observed_wsgi_delta_seconds"] for x in families.values()) / 3
    cases.append({
        "fixture": d["fixture"], "families": families, "pairs": pairs,
        "effect_criteria_met": all(p["criterion_met"] for p in pairs),
        "after_unknown_reads_publicationstate": unknown_state_after,
        "D_before_seconds": sum(x["before_wsgi_mean_seconds"] for x in families.values()) / 3,
        "D_after_seconds": sum(x["after_wsgi_mean_seconds"] for x in families.values()) / 3,
        "observed_delta_D_seconds": delta_d, "observed_20delta_D_worker_seconds_per_second": 20 * delta_d,
        "plans": plans, "worker_pids_absent": sorted(pids),
        "wsgi_exit_after_client_end": {
            "count": sum(events[s["id"]]["exit"] > s["end"] for s in rows),
            "max_seconds": max(0, max(events[s["id"]]["exit"] - s["end"] for s in rows))},
    })
mechanism = all(c["after_unknown_reads_publicationstate"] is False for c in cases)
keep = mechanism and all(c["effect_criteria_met"] for c in cases)
output = {"raw_worker_logs_match_junit": True, "cases": cases, "sql_mechanism_demonstrated": mechanism,
          "effect_pass": keep, "decision": "retain" if keep else "withdraw",
          "scope": ("480 sequential TCP controls, 4 own sync workers, repeated/diverse 10000, one dirty "
                    "candidate off the first page (native_unknown=1). No load/capacity. Per-family means and "
                    "balanced pairs. Same route/WSGI middleware without intrusive profiler; overhead not_measured. "
                    "Separate EXPLAIN probes warm caches before controls; observed JIT kept. Driver execute is "
                    "neither CPU nor planning. Actual Rows/Loops are plan-node observations, not global rows or ORM "
                    "objects. DeltaD descriptive includes detail fluctuation not assigned to the unchanged detail "
                    "path. Upload/DeltaU not_measured. No savings extrapolated to loaded cohorts or clean routes.")}
destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"decision": output["decision"], "mechanism": mechanism,
                  "cases": [{k: v for k, v in c.items() if k != "plans"} for c in cases]}, indent=1))
