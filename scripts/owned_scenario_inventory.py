"""Observe owned CI resources; inventories never attest recipient coverage."""
import hashlib
import json
import os
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def capture(runner_path, roots):
    runner_path = Path(runner_path)
    runner = json.loads(runner_path.read_text())
    run = runner["id"]
    ancestor = os.getpid()
    for _ in range(32):
        if ancestor == runner["pid"]:
            break
        data = Path(f"/proc/{ancestor}/stat").read_text()
        ancestor = int(data[data.rfind(")") + 2:].split()[1])
    else:
        raise RuntimeError("Inventory must execute inside its own live CI runner")
    data = Path(f"/proc/{runner['pid']}/stat").read_text()
    if int(data[data.rfind(")") + 2:].split()[19]) != runner["start_ticks"]:
        raise RuntimeError("Runner process identity changed")
    temporary = Path(runner["temporary"]).resolve(strict=True)
    if temporary.parent != Path("/tmp") or not temporary.name.startswith("web-modelos-local-ci-"):
        raise RuntimeError("Unrecognized disposable resource root")
    containers = []
    for service in ["pg", "redis"]:
        name = f"web-modelos-ci-{service}-{run}"
        if name not in runner["containers"]:
            raise RuntimeError("Container missing from runner inventory")
        info = json.loads(subprocess.check_output(["docker", "inspect", name], text=True))[0]
        if not info["State"]["Running"] or info["Config"]["Labels"].get("web-modelos-local-ci-run") != run:
            raise RuntimeError("Container identity mismatch")
        containers.append({"name": name, "id": info["Id"], "image_id": info["Image"],
                           "created": info["Created"], "ports": info["NetworkSettings"]["Ports"],
                           "mounts": [{"type": m["Type"], "destination": m["Destination"]}
                                      for m in info["Mounts"]]})
    files = []
    seen = set()
    total_bytes = 0
    for declared in roots:
        root = Path(declared).resolve(strict=True)
        if not root.is_relative_to(temporary):
            raise RuntimeError("Resource root is outside the disposable scenario")
        for path in sorted(root.rglob("*")):
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                raise RuntimeError("Symlink needs separate resource classification")
            if not stat.S_ISREG(mode) or path in seen:
                continue
            seen.add(path)
            size = path.stat().st_size
            total_bytes += size
            if len(files) >= 10000 or total_bytes > 128 * 1024 * 1024:
                raise RuntimeError("Bounded scenario inventory exceeded")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(65536), b""):
                    digest.update(chunk)
            files.append({"relative_path": str(path.relative_to(temporary)), "size": size,
                          "sha256": digest.hexdigest(), "subject_binding": "not_established"})
    return {"schema": "owned-scenario-observation-v1", "run": run, "head": runner["head"],
            "captured_at": datetime.now(timezone.utc).isoformat(), "containers": containers,
            "roots": [str(Path(root).relative_to(temporary)) for root in roots], "files": files,
            "coverage_complete": False,
            "pending": ["subject association and inclusion/redaction decisions", "logs/mail/cache/backups outside declared roots", "historical import/restore provenance"],
            "scope": "Observed live own CI containers and declared fixture file roots only. No content bodies exported; hashes do not prove subject ownership or global exhaustiveness."}
