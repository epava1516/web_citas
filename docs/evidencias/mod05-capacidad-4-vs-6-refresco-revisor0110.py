"""Independent per-block release review for the authorized 4/6/6/4 normal_worker_beat run.

Releases the next planned block only when the terminal block shows its owned web, worker
and Beat processes absent, its database, media and owned Redis keys removed, no resource
stop, and repository sources identical to the frozen manifest. Writes review-release.json
only on success; otherwise writes review-blocked.json and the harness stops by timeout.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import psycopg
import redis

root = Path("/home/felidae/proyectos/web_modelos")
out = Path(sys.argv[1])
env = {}
for line in (root / ".env").read_text().splitlines():
    key, sep, value = line.partition("=")
    if sep and key in {"POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"}:
        env[key] = value.strip().strip("\"'")
deadline = time.monotonic() + 3600
reviewed = set()
while time.monotonic() < deadline:
    if (out / "result.json").exists():
        break
    for folder in sorted(out.glob("block-*w")):
        summary_path = folder / "load-summary.json"
        if folder.name in reviewed or not summary_path.exists():
            continue
        time.sleep(1)  # let the harness finish writing the terminal summary
        summary = json.loads(summary_path.read_text())
        manifest = json.loads((out / "frozen-manifest.json").read_text())
        changed = [p for p, h in manifest["source_sha256"].items()
                   if not (root / p).is_file() or hashlib.sha256((root / p).read_bytes()).hexdigest() != h]
        pids = [int(p.split("-")[1]) for p in summary.get("worker_pid_absence", {})]
        pids += [int(p) for p in summary.get("celery_pid_absence", {})]
        with psycopg.connect(dbname=env["POSTGRES_DB"], user=env["POSTGRES_USER"], password=env["POSTGRES_PASSWORD"],
                             host="127.0.0.1", port=55432) as admin:
            owned_dbs = admin.execute("SELECT datname FROM pg_database WHERE datname LIKE 'test_promotion_gate_workers_%'").fetchall()
        checks = {
            "refresh_mode_normal": summary.get("refresh_mode") == "normal_worker_beat",
            "gunicorn_stopped": summary.get("gunicorn_stopped") is True,
            "celery_worker_stopped": summary.get("celery_worker_stopped") is True,
            "celery_beat_stopped": summary.get("celery_beat_stopped") is True,
            "web_and_celery_pids_absent": bool(pids) and not any(Path(f"/proc/{pid}").exists() for pid in pids),
            "block_database_absent": summary.get("database_absence") is True and not owned_dbs,
            "media_absent": summary.get("media_absence") is True,
            "owned_redis_empty": summary.get("owned_redis_empty") is True
                                 and redis.Redis.from_url("redis://127.0.0.1:56379/15").dbsize() == 0,
            "no_resource_stop": not summary.get("trial_stop"),
            "completed": summary.get("completed") is True,
            "sources_unchanged": not changed,
            "beat_aligned": bool(summary.get("beat_alignment")),
        }
        record = {"block": folder.name, "checks": checks, "changed_sources": changed,
                  "reviewed_monotonic": time.monotonic()}
        name = "review-release.json" if all(checks.values()) else "review-blocked.json"
        (folder / name).write_text(json.dumps(record, indent=2))
        print(folder.name, name, json.dumps(checks), flush=True)
        reviewed.add(folder.name)
    time.sleep(1)
