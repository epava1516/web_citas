import collections
import hashlib
import json
import math
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

base = Path("docs/evidencias")
out = {
    "source_received": "8342dbd",
    "no_new_load": True,
    "method": "Independent archive byte/hash, unique IDs, schedule/routes, access correlation and nearest-rank sample calculation",
    "runs": {},
}
for name, duration in [("r5-mod05-intento2", 60), ("r6-mod05-contractual", 900)]:
    index = json.loads((base / f"{name}-artefactos-indice.json").read_text())
    ap = base / index["archive"]
    assert hashlib.sha256(ap.read_bytes()).hexdigest() == index["archive_sha256"]
    with tarfile.open(ap) as tar:
        members = {m.name: tar.extractfile(m).read() for m in tar if m.isfile()}
    assert len(members) == 9
    for row in index["files"]:
        if row["included_in_archive"]:
            data = members[f"{name}/{row['name']}"]
            assert len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"]

    def data(suffix):
        return next(v for k, v in members.items() if k.endswith("/" + suffix))

    manifest = json.loads(data("benchmark-manifest.json"))
    samples = json.loads(data("benchmark-samples.json"))
    dyn = samples["dynamic"]
    ups = samples["uploads"]
    allrows = dyn + ups
    assert len(dyn) == duration * 20 and len({r["id"] for r in allrows}) == len(allrows)
    assert all(
        abs(r["scheduled_at"] - i / 20) < 1e-8 and r["path"] == manifest["routes"][i % 6]
        for i, r in enumerate(dyn)
    )
    assert all(
        r["emitted_at"] is not None
        and r["ended_at"] >= r["emitted_at"] >= r["scheduled_at"]
        and r["status"] == r["expected"] == 200
        and not r["unexpected"]
        and not r["timeout"]
        for r in dyn
    )
    access = [r.split() for r in data("gunicorn-access.log").decode().splitlines()]
    byid = collections.defaultdict(list)
    for r in access:
        if len(r) >= 4:
            byid[r[3]].append(r)
    assert all(
        len(byid[r["id"]]) == 1
        and byid[r["id"]][0][0] == str(r["status"])
        and byid[r["id"]][0][2] == r["path"].split("?")[0]
        for r in allrows
    )
    assert len(ups) == duration // 60 and all(
        u["scheduled_at"] == i * 60 and u["status"] == u["expected"] == 302
        for i, u in enumerate(ups)
    )

    def pct(v, q):
        return sorted(v)[math.ceil(len(v) * q) - 1]

    latency = [r["ended_at"] - r["emitted_at"] for r in dyn]
    delay = [r["emitted_at"] - r["scheduled_at"] for r in dyn]
    pending = sum(r["ended_at"] > duration for r in dyn)
    drain = max(0, max(r["ended_at"] for r in allrows) - duration)
    summary = json.loads(data("load-summary.json"))
    compact = {k: v for k, v in summary.items() if k != "samples"}
    properties = {
        p.get("name"): p.get("value") for p in ET.fromstring(data("pytest.xml")).iter("property")
    }
    # Harness compact JUnit omits only samples; compare actual structure rather than assuming.
    junit = json.loads(properties["load_summary"])
    assert junit == compact
    checks = {
        "generator": pct(delay, 0.95) <= 0.010
        and pct(delay, 0.99) <= 0.025
        and max(delay) <= 0.100,
        "pending_at_close": pending <= 20,
        "drain": drain <= 70,
        "p95": pct(latency, 0.95) < 0.8,
        "zero_errors": True,
        "schedule_and_accounting": True,
        "uploads": True,
    }
    assert all(checks.values())
    out["runs"][name] = {
        "archive_sha256_verified": True,
        "nine_member_hashes_verified": True,
        "source_commit": manifest["source_commit"],
        "dynamic": len(dyn),
        "family_counts": dict(
            collections.Counter(
                "detail"
                if "/listing/" in r["path"]
                else "search"
                if "?" in r["path"]
                else "listing"
                for r in dyn
            )
        ),
        "successful": len(dyn),
        "errors": 0,
        "timeouts": 0,
        "not_emitted": 0,
        "unique_and_correlated_ids": len(allrows),
        "pending_at_close": pending,
        "final_pending": 0,
        "p95_seconds": pct(latency, 0.95),
        "p99_seconds": pct(latency, 0.99),
        "max_seconds": max(latency),
        "generator_p95_seconds": pct(delay, 0.95),
        "generator_p99_seconds": pct(delay, 0.99),
        "generator_max_seconds": max(delay),
        "drain_all_requests_seconds": drain,
        "uploads": len(ups),
        "junit_summary_matches": True,
        "checks": checks,
        "recorded_load_filter": "PASS",
        "limitations": [
            "Original source hashes and clean worktree not recorded",
            "WSGI entry/exit and PID not recorded: service decomposition and D not_measured",
            "Host resource consumption not_measured",
            "Contemporaneous cleanup record absent",
            "This validates recorded load outcomes; functional equivalence remains FAIL in separate Codex reproduction",
        ],
    }
(base / "revision-codex-mod05-auditoria-originales0110.json").write_text(
    json.dumps(out, indent=2) + "\n"
)
print(json.dumps(out, indent=2))
