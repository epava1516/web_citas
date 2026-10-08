"""Preserve and audit original MOD-05 R5 attempt 2 and R6 benchmark artifacts (no new load).

Recomputes accounting from the original per-request samples with the harness definitions
(tests/test_contract_http_load.py at the recorded commit: nearest-rank percentile
ceil(n*q)-1 over all emitted dynamic requests, failures included). Writes one tar.gz per
run plus a JSON index with original path, size, SHA-256, attribution and absences.
"""
import hashlib
import io
import json
import math
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path

SCRATCH = Path("/tmp/claude-1000/-home-eduardo-web-citas/eeb2c24f-16b2-430e-a2b3-463b581c3ef1/scratchpad")
REPO = Path("/home/eduardo/web_citas")
OUT = REPO / "docs/evidencias"
RUNS = {
    "r5-mod05-intento2": {"dir": "r5b_short", "duration": 60, "rps": 20, "uploads": 1,
                          "selection": "test_contract_arrival_rate_http_with_limited_uploads[short]",
                          "summary_file": "r5-mod05-intento2-pass.json"},
    "r6-mod05-contractual": {"dir": "r6_measured", "duration": 900, "rps": 20, "uploads": 15,
                             "selection": "test_contract_arrival_rate_http_with_limited_uploads[measured]",
                             "summary_file": "r6-mod05-contractual-pass.json"},
}
EXCLUDE = {
    "credentials.json": "excluded: synthetic demo credentials (passwords/TOTP); hash kept for traceability",
    "private/": "excluded: private media (fixture/upload originals and derivatives); hash kept",
    "__pycache__/": "excluded: interpreter bytecode cache, not evidence; hash kept",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pct(values, q):
    values = sorted(values)
    return values[max(0, math.ceil(len(values) * q) - 1)] if values else None


def recompute(samples, duration, rps, uploads_expected):
    dyn, ups = samples["dynamic"], samples["uploads"]
    emitted = [r for r in dyn if r.get("emitted_at") is not None]
    finished = [r for r in emitted if r.get("ended_at") is not None]
    ok = [r for r in finished if r.get("status") == r.get("expected") and not r.get("unexpected")]
    timeouts = [r for r in emitted if r.get("timeout")]
    errors = [r for r in emitted if r.get("unexpected")]
    latencies = [r["ended_at"] - r["emitted_at"] for r in finished]
    delays = [r["emitted_at"] - r["scheduled_at"] for r in emitted]
    pending_at_close = [r for r in emitted if r.get("ended_at") is None or r["ended_at"] > duration]
    late_emitted = [r for r in emitted if r["emitted_at"] > duration]
    statuses = {}
    for r in emitted:
        statuses[str(r.get("status"))] = statuses.get(str(r.get("status")), 0) + 1
    upload_rows = [{"id": u["id"], "status": u.get("status"), "expected": u.get("expected"),
                    "scheduled_at": u.get("scheduled_at"),
                    "emission_delay": (u["emitted_at"] - u["scheduled_at"]) if u.get("emitted_at") is not None else None,
                    "seconds": (u["ended_at"] - u["emitted_at"]) if u.get("ended_at") is not None else None}
                   for u in ups]
    return {
        "scheduled_expected": int(duration * rps),
        "scheduled_samples": len(dyn),
        "emitted": len(emitted),
        "not_emitted": len(dyn) - len(emitted),
        "emitted_after_window": len(late_emitted),
        "successful": len(ok),
        "errors_unexpected": len(errors),
        "timeouts": len(timeouts),
        "finished": len(finished),
        "final_pending": len(emitted) - len(finished),
        "pending_at_window_close": len(pending_at_close),
        "status_counts": statuses,
        "error_fraction_emitted": len(errors) / len(emitted) if emitted else None,
        "observable_latency_seconds": {
            "p50": pct(latencies, 0.5), "p95": pct(latencies, 0.95), "p99": pct(latencies, 0.99),
            "max": max(latencies) if latencies else None, "population": len(latencies),
            "failures_included": "all emitted dynamic requests that finished; failed/timeouts would be included with their end time (none observed)",
        },
        "generator_delay_seconds": {"p95": pct(delays, 0.95), "p99": pct(delays, 0.99),
                                    "max": max(delays) if delays else None, "population": len(delays)},
        "observed_drain_seconds_after_window": max(0.0, max((r["ended_at"] for r in finished), default=0) - duration),
        "last_dynamic_end_seconds": max((r["ended_at"] for r in finished), default=None),
        "uploads": {"expected_count": uploads_expected, "samples": len(ups),
                    "conforming_302": sum(1 for u in ups if u.get("status") == 302 and u.get("expected") == 302),
                    "rows": upload_rows},
    }


def access_correlation(log_path, samples):
    rows = [line.split() for line in log_path.read_text().splitlines() if line.strip()]
    by_id = {r[3]: r for r in rows if len(r) >= 4 and r[3] != "-"}
    sample_rows = samples["dynamic"] + samples["uploads"]
    matched = mismatched_status = mismatched_path = 0
    missing = []
    for s in sample_rows:
        row = by_id.get(s["id"])
        if row is None:
            missing.append(s["id"])
            continue
        matched += 1
        if str(s.get("status")) != row[0]:
            mismatched_status += 1
        if s["path"].split("?")[0] != row[2]:
            mismatched_path += 1
    service = [float(r[1]) for r in rows if len(r) >= 4 and r[3].startswith("d-")]
    return {"log_lines": len(rows), "lines_with_benchmark_id": len(by_id),
            "lines_without_id": len(rows) - len(by_id),
            "samples_matched": matched, "samples_missing_in_log": len(missing),
            "missing_ids_first": missing[:20], "status_mismatches": mismatched_status,
            "path_mismatches": mismatched_path,
            "gunicorn_dynamic_service_seconds": {"p50": pct(service, 0.5), "p95": pct(service, 0.95),
                                                 "max": max(service) if service else None,
                                                 "population": len(service)},
            "format": "%(s)s %(L)s %(U)s %({x-benchmark-id}i)s: status, request seconds, path, id. No PID, no entry/exit timestamps."}


def junit_summary(path):
    root = ET.parse(path).getroot()
    out = {}
    for suite in root.iter("testsuite"):
        out = {k: suite.get(k) for k in ("tests", "failures", "errors", "skipped", "time", "timestamp", "hostname")}
    props = {p.get("name"): p.get("value") for p in root.iter("property")}
    claimed = json.loads(props["load_summary"]) if "load_summary" in props else None
    return out, claimed


git_files = ["tests/test_contract_http_load.py", "scripts/benchmark_async_transport.py",
             "scripts/synthetic_load_dataset.py", "apps/listings/publication_state.py",
             "apps/listings/discovery.py", "apps/listings/management/commands/refresh_publication_state.py",
             "config/settings.py"]
audit = {"author": "Claude Code (Claude Opus 5.5, claude-opus-5-5)", "no_new_load_executed": True,
         "percentile_method": "nearest-rank ceil(n*q)-1, as tests/test_contract_http_load.py percentile()",
         "runs": {}}
for name, spec in RUNS.items():
    base = SCRATCH / spec["dir"]
    temp = base / "pytest-temp/test_contract_arrival_rate_htt0"
    files = sorted(p for p in base.rglob("*") if p.is_file())
    index = []
    archive_members = []
    for path in files:
        rel = path.relative_to(base).as_posix()
        reason = next((why for key, why in EXCLUDE.items() if key in rel), None)
        entry = {"original_path": str(path), "name": rel, "bytes": path.stat().st_size, "sha256": sha(path),
                 "run": name, "included_in_archive": reason is None,
                 "attribution": (f"output directory {spec['dir']} passed as --gate-timings-output parent/--basetemp "
                                 f"for the {spec['selection']} invocation; mtime within the run window; "
                                 "manifest source_commit and Gunicorn private log timestamps agree")}
        if reason:
            entry["exclusion"] = reason
        else:
            archive_members.append((path, rel))
        index.append(entry)
    samples = json.loads((base / "benchmark-samples.json").read_text())
    manifest = json.loads((base / "benchmark-manifest.json").read_text())
    junit, claimed = junit_summary(base / "pytest.xml")
    load_summary_file = json.loads((temp / "load-summary.json").read_text())
    recomputed = recompute(samples, spec["duration"], spec["rps"], spec["uploads"])
    correlation = access_correlation(temp / "gunicorn-access.log", samples)
    commit = manifest["source_commit"]
    derived_hashes = {}
    for f in git_files:
        blob = subprocess.run(["git", "-C", str(REPO), "rev-parse", f"{commit}:{f}"], capture_output=True, text=True)
        derived_hashes[f] = blob.stdout.strip() or "not_found"
    comparison = {
        "verdict_claimed": claimed.get("verdict") if claimed else "not_found",
        "claimed_counts": claimed.get("counts") if claimed else "not_found",
        "claimed_observable_latency_seconds": claimed.get("observable_latency_seconds") if claimed else "not_found",
        "claimed_generator_delay_seconds": claimed.get("generator_delay_seconds") if claimed else "not_found",
        "claimed_final_upload_counts": claimed.get("final_upload_counts") if claimed else "not_found",
        "claimed_gunicorn_dynamic_service_p95_seconds": claimed.get("gunicorn_dynamic_service_p95_seconds") if claimed else "not_found",
        "load_summary_file_equals_junit_property_except_samples": (
            {k: v for k, v in load_summary_file.items() if k != "samples"} == claimed
        ),
        "load_summary_relation": "JUnit property is the harness 'compact' summary (record_property); load-summary.json is the full summary including per-request 'samples'",
    }
    policy = manifest["policy"]
    checks = {
        "no_not_emitted": recomputed["not_emitted"] == 0 and recomputed["scheduled_samples"] == recomputed["scheduled_expected"],
        "generator_p95_le_policy": recomputed["generator_delay_seconds"]["p95"] <= policy["generator_p95_seconds_max"],
        "generator_p99_le_policy": recomputed["generator_delay_seconds"]["p99"] <= policy["generator_p99_seconds_max"],
        "generator_max_le_policy": recomputed["generator_delay_seconds"]["max"] <= policy["generator_max_seconds_max"],
        "p95_strictly_below_policy": recomputed["observable_latency_seconds"]["p95"] < policy["latency_p95_seconds_strict_max"],
        "error_fraction_strictly_below_policy": recomputed["error_fraction_emitted"] < policy["error_fraction_strict_max"],
        "final_pending_zero": recomputed["final_pending"] == 0,
        "drain_within_policy": recomputed["observed_drain_seconds_after_window"] <= policy["drain_seconds"],
        "uploads_all_302": recomputed["uploads"]["conforming_302"] == spec["uploads"] == recomputed["uploads"]["samples"],
        "uploads_scheduled_one_per_minute": sorted(u["scheduled_at"] for u in recomputed["uploads"]["rows"]) == [60 * i for i in range(spec["uploads"])],
        "access_log_correlates_all_samples": correlation["samples_missing_in_log"] == 0 and correlation["status_mismatches"] == 0,
    }
    if name.startswith("r5"):
        checks["pending_at_window_close_le_20"] = recomputed["pending_at_window_close"] <= 20
    absences = {
        "manifest_source_file_hashes": "not_found: original manifest records source_commit only; git blob ids at that commit listed separately as derived, not original",
        "wsgi_entry_exit_events_with_pid": "not_measured: worker observer disabled (WEB_MODELOS_BENCHMARK_OBSERVE_WORKERS unset); access log has status/seconds/path/id only",
        "worker_pid_per_request": "not_measured",
        "runner_script_file": "not_found: invoked directly as a pytest command from the Claude Code session (command recorded below); no wrapper script",
        "cleanup_evidence_at_run_time": "not_found: pytest-django dropped its test database at session end; no cleanup record was written. Post-hoc observation (2026-10-08, this audit): no database matching r5mod05 exists",
        "host_resource_sampling": "not_measured (manifest not_measured list)",
        "working_tree_clean_at_launch": "not_recorded by the harness; launch followed a commit in the same session with no intervening edits (session transcript), not independently verifiable from artifacts",
    }
    runner = (f"POSTGRES_DB=promotion_gate_r5mod05 .venv/bin/python -m pytest "
              f"\"tests/test_contract_http_load.py::{spec['selection']}\" -q -p no:cacheprovider "
              f"-p scripts.catalogue_gate_timings --gate-timings-output=<dir>/test-timings.json "
              f"--junitxml=<dir>/pytest.xml --basetemp=<dir>/pytest-temp > <dir>/pytest.log; cwd /home/eduardo/web_citas")
    run_audit = {
        "source_commit": commit, "selection": spec["selection"], "runner_command": runner,
        "manifest_fields_present": sorted(manifest.keys()),
        "manifest_summary": {k: manifest.get(k) for k in ("routes", "mix", "duration_seconds", "arrival_rps",
                                                           "scheduled_dynamic", "uploads_separate", "state", "client",
                                                           "fixture", "worker_observer")},
        "dataset": {k: v for k, v in manifest["dataset"].items() if k != "sample_ids"},
        "workers": "Gunicorn 4 sync (harness command); boot/exit of 4 worker PIDs in gunicorn-private.log",
        "junit": junit, "recomputed": recomputed, "access_log_correlation": correlation,
        "claimed_by_summary": comparison, "criteria_recomputed": checks,
        "derived_git_blob_ids_at_commit": derived_hashes, "absences": absences,
    }
    audit["runs"][name] = run_audit
    tar_path = OUT / f"{name}-artefactos.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for path, rel in archive_members:
            tar.add(path, arcname=f"{name}/{rel}")
    (OUT / f"{name}-artefactos-indice.json").write_text(json.dumps({
        "run": name, "archive": tar_path.name, "archive_bytes": tar_path.stat().st_size,
        "archive_sha256": sha(tar_path), "files": index, "absences": absences,
        "redactions": "none: included files were preserved byte-for-byte; excluded files are listed with hash only",
    }, indent=1))
(OUT / "auditoria-pass-mod05-r5-r6.json").write_text(json.dumps(audit, indent=1, default=str))
for name, run in audit["runs"].items():
    r = run["recomputed"]
    print(name, run["source_commit"][:10], "checks:", all(run["criteria_recomputed"].values()),
          {k: v for k, v in run["criteria_recomputed"].items() if not v})
    print("  emitted", r["emitted"], "ok", r["successful"], "err", r["errors_unexpected"], "timeouts", r["timeouts"],
          "pending_close", r["pending_at_window_close"], "final_pending", r["final_pending"])
    print("  p95 %.4f p99 %.4f max %.4f" % (r["observable_latency_seconds"]["p95"], r["observable_latency_seconds"]["p99"], r["observable_latency_seconds"]["max"]),
          "| gen p95 %.4f p99 %.4f max %.4f" % (r["generator_delay_seconds"]["p95"], r["generator_delay_seconds"]["p99"], r["generator_delay_seconds"]["max"]),
          "| drain %.3f" % r["observed_drain_seconds_after_window"], "| uploads", r["uploads"]["conforming_302"], "/", r["uploads"]["samples"])
    print("  claimed p95", run["claimed_by_summary"]["claimed_observable_latency_seconds"]["p95"], "| summary file == junit (except samples):", run["claimed_by_summary"]["load_summary_file_equals_junit_property_except_samples"])
    print("  access log:", {k: run["access_log_correlation"][k] for k in ("samples_matched", "samples_missing_in_log", "status_mismatches", "path_mismatches")})
