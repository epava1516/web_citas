"""Recalculate clean/dirty TCP controls from original JUnit properties."""

import json
import statistics
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(sys.argv[1])
cases = []
for t in ET.parse(root / "pytest.xml").findall(".//testcase"):
    for p in t.findall("./properties/property"):
        if p.get("name") != "tcp_matrix":
            continue
        d = json.loads(p.get("value"))
        events = {e["id"]: e for e in d["wsgi_events"]}
        assert len(events) == len(d["samples"]) == 120

        def family(path):
            return "detail" if "/listing/" in path else "search" if "?" in path else "listing"

        def mean(metric, f, phase=None, block=None):
            rows = [
                r
                for r in d["samples"]
                if family(r["path"]) == f
                and (phase is None or r["phase"] == phase)
                and (block is None or r["block"] == block)
            ]
            return statistics.mean(
                r["end"] - r["emission"]
                if metric == "http"
                else events[r["id"]]["exit"] - events[r["id"]]["entry"]
                for r in rows
            )

        families = {
            f: {
                "population_per_phase": 20,
                "clean_wsgi_mean_seconds": mean("wsgi", f, "clean"),
                "dirty_wsgi_mean_seconds": mean("wsgi", f, "dirty"),
                "dirty_minus_clean_wsgi_seconds": mean("wsgi", f, "dirty")
                - mean("wsgi", f, "clean"),
                "dirty_minus_clean_http_seconds": mean("http", f, "dirty")
                - mean("http", f, "clean"),
            }
            for f in ["listing", "search", "detail"]
        }
        comparisons = []
        for clean, dirty in [(0, 1), (3, 2)]:
            for f in ["listing", "search"]:
                baseline = mean("http", f, block=clean)
                penalty = mean("http", f, block=dirty) - baseline
                comparisons.append(
                    {
                        "clean_block": clean,
                        "dirty_block": dirty,
                        "family": f,
                        "http_penalty_seconds": penalty,
                        "http_penalty_fraction": penalty / baseline,
                        "criterion_met": penalty >= 0.02 and penalty / baseline >= 0.1,
                    }
                )
        delta = sum(v["dirty_minus_clean_wsgi_seconds"] for v in families.values()) / 3
        cases.append(
            {
                "fixture": d["fixture"],
                "families": families,
                "pair_comparisons": comparisons,
                "prefixed_material_criterion_met": all(x["criterion_met"] for x in comparisons),
                "observed_condition_delta_D_seconds": delta,
                "observed_condition_20delta_D_worker_seconds_per_second": 20 * delta,
                "observed_worker_pids": sorted({e["pid"] for e in events.values()}),
            }
        )
print(
    json.dumps(
        {
            "cases": cases,
            "diagnostic_hypothesis_accepted": all(
                c["prefixed_material_criterion_met"] for c in cases
            ),
            "scope": "Condition contrast, not backend before/after improvement; sequential TCP not capacity. Different authority/listing than unidentified upload candidate prevents exact causal savings extrapolation. Details fluctuation retained but not assigned to optimization. No uploads or concurrency in these controls.",
            "decision": "One dirty candidate has material reproducible cost by prefixed HTTP criterion. Preserve native fallback/invalidation; next isolate duplicated work in unknown-candidate preparation versus selected-page guard with equivalent profile before selecting minimal change. Existing operational refresh evidence reusable; do not enable read-repair/cache or another load automatically.",
        },
        indent=2,
    )
)
