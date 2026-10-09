import json
import statistics
from pathlib import Path

root = Path("/home/felidae/proyectos/web_modelos")
r = json.loads((root / "docs/evidencias/mod05-orden-desconocidos-ab-revisada0110.json").read_text())
cases = []
for c in r["cases"]:
    d = c["properties"]["tcp_matrix"]
    ev = {e["id"]: e for e in d["wsgi_events"]}
    rows = d["samples"]
    assert len(ev) == len(rows) == len({s["id"] for s in rows}) == 120

    def family(p):
        return "detail" if "/listing/" in p else "search" if "?" in p else "listing"

    for s in rows:
        e = ev[s["id"]]
        assert s["status"] == 200 and e["order_variant"] == s["phase"]
        assert s["emission"] <= e["entry"] <= e["exit"]
        assert s["end"] >= e["entry"]
        if family(s["path"]) != "detail":
            assert e["route"] == {"route": "state", "reason": "trusted_state", "native_unknown": 1}
    for pid in {e["pid"] for e in ev.values()}:
        assert not Path(f"/proc/{pid}").exists()

    def mean(metric, f, phase=None, block=None):
        pop = [
            s
            for s in rows
            if family(s["path"]) == f
            and (phase is None or s["phase"] == phase)
            and (block is None or s["block"] == block)
        ]
        assert len(pop) == (10 if block is not None else 20)
        return statistics.mean(
            s["end"] - s["emission"]
            if metric == "http"
            else ev[s["id"]]["exit"] - ev[s["id"]]["entry"]
            for s in pop
        )

    families = {
        f: {
            "population_per_variant": 20,
            **{
                v + "_" + m + "_mean_seconds": mean(m, f, v)
                for v in ["before", "after"]
                for m in ["http", "wsgi"]
            },
            "observed_wsgi_delta_seconds": mean("wsgi", f, "before") - mean("wsgi", f, "after"),
        }
        for f in ["listing", "search", "detail"]
    }
    pairs = []
    for b, a in [(0, 1), (3, 2)]:
        for f in ["listing", "search"]:
            old = mean("http", f, block=b)
            new = mean("http", f, block=a)
            delta = old - new
            pairs.append(
                {
                    "before_block": b,
                    "after_block": a,
                    "family": f,
                    "population_per_cell": 10,
                    "before_mean_seconds": old,
                    "after_mean_seconds": new,
                    "improvement_seconds": delta,
                    "improvement_fraction": delta / old,
                    "criterion_met": delta >= 0.02 and delta / old >= 0.05,
                }
            )
    plans = []
    for p in c["properties"]["order_plans"]:
        plan = p["plan"]
        plan = plan[0] if isinstance(plan, list) else plan
        plans.append(
            {
                "variant": p["variant"],
                "normalized": p["normalized"],
                "driver_execute_seconds": p["driver_execute_seconds"],
                "jit": p["jit"],
                "planning_ms": plan.get("Planning Time", "not_measured"),
                "execution_ms": plan.get("Execution Time", "not_measured"),
                "root_node": plan["Plan"]["Node Type"],
                "root_actual_rows": plan["Plan"].get("Actual Rows", "not_measured"),
                "shared_hit_blocks": plan["Plan"].get("Shared Hit Blocks", "not_measured"),
                "shared_read_blocks": plan["Plan"].get("Shared Read Blocks", "not_measured"),
            }
        )
    delta = sum(x["observed_wsgi_delta_seconds"] for x in families.values()) / 3
    cases.append(
        {
            "fixture": d["fixture"],
            "families": families,
            "pairs": pairs,
            "criteria_met": all(p["criterion_met"] for p in pairs),
            "observed_delta_D_seconds": delta,
            "observed_20delta_D_worker_seconds_per_second": 20 * delta,
            "plans": plans,
            "wsgi_exit_after_client_end": {
                "count": sum(ev[s["id"]]["exit"] > s["end"] for s in rows),
                "max_seconds": max(0, max(ev[s["id"]]["exit"] - s["end"] for s in rows)),
            },
        }
    )
keep = all(c["criteria_met"] for c in cases)
out = {
    "cases": cases,
    "effect_pass": keep,
    "decision": "retain" if keep else "withdraw",
    "functional": "31 PG PASS; 2 TCP fixture cases PASS, equivalent response/route; not full N3",
    "scope": "240 sequential TCP controls, 4 synchronous workers, repeated/diverse 10000. No saturation/load or capacity accreditation. Native unknown1 intentionally preserved. Means and explicit populations; balanced pairs prefixed20ms AND5percent in all8 cells. Controls have common route/WSGI adapter, no intrusive profiler; overhead not_measured. Separate Client SQL probes and EXPLAIN warm caches before TCP; current observed JIT reused. Driver execute includes server/wait/transfer and is not CPU/planning. Plans have genuine independent planning/execution. No params persisted. Details fluctuation included in descriptive DeltaD, not assigned causally to intervention; uploads and DeltaU not_measured.",
}
(root / "docs/evidencias/mod05-orden-desconocidos-analisis0110.json").write_text(
    json.dumps(out, indent=2) + "\n"
)
print(
    json.dumps(
        {
            "decision": out["decision"],
            "fixtures": [{k: v for k, v in c.items() if k not in ["plans"]} for c in cases],
        },
        indent=2,
    )
)
