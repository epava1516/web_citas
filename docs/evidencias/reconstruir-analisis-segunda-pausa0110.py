"""Derive the pause analysis from reviewed files; never execute a benchmark or SQL."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = [
    ("Antes de MOD-04", "uuid-array-matriz"),
    ("Bindings y construcción diferida", "bindings-coste"),
    ("JIT acotado, controles", "jit-scope-controles"),
    ("Reglas compartidas, controles", "valores-controles"),
    ("Reglas compartidas, perfil", "valores-perfil"),
    ("Kernel de modelo, controles", "kernel-valores-controles"),
    ("Kernel de modelo, perfil", "kernel-valores-perfil"),
    ("Kernel de entrada, controles", "input-kernel-controles"),
    ("Perfil final de entrada/lectura/claves", "input-kernel-perfil"),
]
GATES = ["bindings-n1-", "jit-scope-n1-", "valores-n1-", "kernel-valores-n1-",
         "input-kernel-n1-", "freeze-boundary"]


def path_for(suffix):
    return HERE / ("listado-proyeccion-" + suffix + "0110.json")


def read(path, sources):
    raw = path.read_bytes()
    sources[path.name] = hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def main():
    sources, stages, gates = {}, [], []
    for label, suffix in STAGES:
        path = path_for(suffix)
        data = read(path, sources)
        cases = data.get("diagnostic_cases", data.get("reports", []))
        result = {"stage": label, "evidence": path.name,
                  "source_commit": data["source_commit"], "samples": []}
        for variant in ("contractual", "diverse"):
            rows = [c for c in cases if c["variant"] == variant and c["count"] == 10000]
            if "projected_control_seconds" in rows[0]:
                assert len(rows) == 1
                row = rows[0]
                sample = {"variant": variant,
                          "native_control_seconds": row["native_control_seconds"],
                          "projected_control_seconds": row["projected_control_seconds"],
                          "projected_observed_seconds": row["projected_SQL_observed_request_seconds"],
                          "observed_instruments": "SQL execute wrapper only",
                          "queries": row["query_count"],
                          "sql_execute_seconds": row["sql_execute_seconds"]}
            else:
                native = next(c for c in rows if c["mode"] == "native")
                row = next(c for c in rows if c["mode"] == "projected")
                sample = {"variant": variant,
                          "native_control_seconds": native["control_request_seconds"],
                          "projected_control_seconds": row["control_request_seconds"],
                          "projected_observed_seconds": row["request_seconds"],
                          "observed_instruments": "source-specific rule profiler, SQL wrapper, model signals",
                          "queries": row["queries"],
                          "sql_execute_seconds": row["sql_execute_seconds"],
                          "model_constructions": sum(row["objects"].values()),
                          "objects": row["objects"], "projection_stats": row["projection_stats"]}
            assert sample["queries"] == sum(q["calls"] for q in row["dominant_sql"])
            assert abs(sample["sql_execute_seconds"] - sum(q["total_time"] for q in row["dominant_sql"])) < 1e-6
            result["samples"].append(sample)
        stages.append(result)

    for suffix in GATES:
        path = path_for(suffix)
        data = read(path, sources)
        assert data["pytest_exit"] == 0 and data["sources_unchanged"] and data["cleanup_verified"]
        count = len(data["cases"]) if "cases" in data else data["review"]["terminal_passes"]
        gates.append({"evidence": path.name, "source_commit": data["source_commit"],
                      "passed_cases": count, "scope": data["review"]})

    latest = read(path_for("input-kernel-perfil"), sources)
    profiles = []
    for row in latest["diagnostic_cases"]:
        if row["mode"] != "projected":
            continue
        for rule in row["rules"]:
            assert abs(rule["inclusive_time"] - rule["exclusive_time"] - sum(rule["instrumented_children"].values())) < 1e-6
            assert abs(rule["mean_exclusive_time"] - rule["exclusive_time"] / rule["calls"]) < 1e-8
        top_sql = []
        for sql in row["dominant_sql"][:5]:
            assert abs(sql["mean_time"] - sql["total_time"] / sql["calls"]) < 1e-8
            top_sql.append({**sql, "fraction_of_SQL_execute": sql["total_time"] / row["sql_execute_seconds"]})
        freeze = next(r for r in row["rules"] if r["rule"] == "apps.listings.projected_publication.freeze")
        profiles.append({"variant": row["variant"], "route": row["route"],
                         "rules": row["rules"], "top5_SQL": top_sql,
                         "top5_SQL_fraction": sum(s["fraction_of_SQL_execute"] for s in top_sql),
                         "freeze_calls_per_candidate": freeze["calls"] / row["count"],
                         "objects": row["objects"],
                         "model_constructions": sum(row["objects"].values())})

    artifact = {
        "schema": "performance-second-pause-derived-v1",
        "source_commit": latest["source_commit"],
        "goal_status_at_review": "paused",
        "method": "Read reviewed JSON and check arithmetic. No requests, tests, SQL, load, or backend edits.",
        "sources_sha256": sources,
        "historical_controls": stages, "functional_gates_separate_sources": gates,
        "latest_profile": profiles,
        "unchanged_verdicts": {"short_20RPS_60s": "FAIL", "historical_contractual_900s": "INVALID",
                               "current_source_capacity": "not_measured", "delivery_closed": False},
        "occupancy_reference": {"workers": 4, "dynamic_RPS": 20,
                                "necessary_mean_service_seconds_before_margin": 4 / 20,
                                "scope": "Theoretical mixed workload budget; not a new SLO or measured capacity."},
        "not_measured": ["causal gain across code versions", "causal profiler overhead",
                         "unprofiled per-rule time", "driver decoding separately",
                         "SQL rows_returned", "SQL rows_affected", "SQL rows_scanned",
                         "DB CPU/RSS/waits/locks/IO", "current 100/1000/10000 common matrix",
                         "current search/detail mixed mean service", "current concurrent capacity",
                         "PRODUCTION/checked/promotions current cost and full acceptance"],
        "limits": ["One control per mode per run, fixed order, warmed shared caches. Historical rows are observations, not an A/B series.",
                   "Functional suites on different sources overlap; never sum them as a common N2 battery.",
                   "Rules have direct-child exclusive scope; recursion, lazy SQL and rendering overlap. SQL is execute, not PostgreSQL CPU.",
                   "820000 profiled freeze calls identify repeated work, not its unprofiled cost or achievable saving.",
                   "Latest DjangoClient request excludes network/Gunicorn; no extrapolated concurrent p95 or PASS.",
                   "Old 1000-native 350.422714s observation and ambiguous wrapper metrics retain their original evidence and limitations."]}
    destination = HERE / "analisis-rendimiento-segunda-pausa0110.json"
    destination.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n")
    print(f"Derived {len(stages)} historical stages, {len(gates)} separate functional gates, {len(profiles)} current profiles: {destination.name}")


if __name__ == "__main__":
    main()
