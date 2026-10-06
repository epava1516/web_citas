"""Capture actual local Compose logs privately; never attest full access coverage.

Run on the operator host, without mounting the Docker socket into the web app.
The encrypted bundle contains originals for subsequent scoped review. It is
not a recipient copy and does not account for removed containers or backups.
"""

import argparse
import hashlib
import json
import os
import stat
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

PROJECT = "web-modelos"
SERVICES = ("app", "worker", "beat", "caddy", "db", "redis")
MAX_SERVICE_BYTES = 32 * 1024 * 1024


def scoped_origin_name(kind, case_id, inventory_id):
    """Immutable per-case/inventory slots; never accept arbitrary path components."""
    if kind not in {"logs", "resources", "redis-history"} or type(inventory_id) is not int or inventory_id < 1:
        raise ValueError("Exact resource kind and positive inventory required")
    case_id = UUID(str(case_id))
    return f"access-{kind}-{case_id}-{inventory_id}.encrypted"


def subject_log_signature(event):
    from apps.safety.rights import fingerprint

    return fingerprint(
        "subject-operation-log-v1:"
        + json.dumps(
            {key: value for key, value in event.items() if key != "signature"},
            sort_keys=True,
            ensure_ascii=False,
        )
    )


def signed_subject_log_event(kind, subject_id, operation, outcome, created_at):
    """Server-side producer format; no public signing endpoint is provided."""
    if created_at.tzinfo is None:
        raise ValueError("Aware event time required")
    event = {
        "schema": "subject-operation-v1",
        "subject_kind": kind,
        "subject_id": str(subject_id),
        "operation": operation,
        "outcome": outcome,
        "created_at": created_at.isoformat(),
    }
    event["signature"] = subject_log_signature(event)
    return event


def docker_output(arguments):
    completed = subprocess.run(["docker", *arguments], capture_output=True, timeout=30, check=False)
    if completed.returncode:
        raise RuntimeError("Local Docker resource capture failed")
    return completed.stdout, completed.stderr


def collect():
    records = []
    for service in SERVICES:
        name = f"{PROJECT}-{service}-1"
        metadata, _ = docker_output(["inspect", name])
        container = json.loads(metadata)[0]
        if container["Config"]["Labels"].get("com.docker.compose.project") != PROJECT:
            raise RuntimeError("Resource belongs to another project")
        stdout, stderr = docker_output(["logs", "--timestamps", name])
        if len(stdout) + len(stderr) > MAX_SERVICE_BYTES:
            raise RuntimeError("Local resource exceeds capture limit")
        # Retain streams separately: concatenation cannot prove interleaving.
        records.append(
            {
                "service": service,
                "container": container["Id"],
                "image": container["Image"],
                "container_created_at": container["Created"],
                "stdout": stdout.decode("utf-8", errors="strict"),
                "stderr": stderr.decode("utf-8", errors="strict"),
                "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
                "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
            }
        )
    return {
        "schema": "local-access-log-origins-v1",
        "project": PROJECT,
        "captured_at": datetime.now(UTC).isoformat(),
        "records": records,
        "partial": True,
        "pending": [
            "subject_association_and_disclosure_review",
            "historical_or_removed_containers",
            "host_logs_and_mail_retention",
            "cache_and_backup_content_accounting",
        ],
    }


def write_bundle(directory, body, *, case_id=None, inventory_id=None, kind="logs"):
    from apps.safety.crypto import seal

    directory = Path(directory)
    metadata = directory.lstat()
    if not stat.S_ISDIR(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) & 0o077:
        raise ValueError("Existing private directory with mode0700 required")
    if (case_id is None) != (inventory_id is None):
        raise ValueError("Case and inventory must be supplied together")
    if kind != "logs" and (kind != "redis-history" or case_id is None or metadata.st_uid != os.geteuid()):
        raise ValueError("Owned directory and exact scoped Redis history required")
    name = (
        scoped_origin_name(kind, case_id, inventory_id)
        if case_id is not None
        else "access-log-origins.encrypted"
    )
    path = directory / name
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(seal(body))
        stream.flush()
        os.fsync(stream.fileno())
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--request", type=UUID)
    parser.add_argument("--inventory", type=int)
    arguments = parser.parse_args()
    if (arguments.request is None) != (arguments.inventory is None):
        parser.error("--request and --inventory must be supplied together")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    body = collect()
    path = write_bundle(
        arguments.output_directory,
        body,
        case_id=arguments.request,
        inventory_id=arguments.inventory,
    )
    print(
        json.dumps(
            {
                "encrypted_artifact": str(path),
                "captured_at": body["captured_at"],
                "services": [
                    {
                        "service": row["service"],
                        "stdout_bytes": len(row["stdout"].encode()),
                        "stderr_bytes": len(row["stderr"].encode()),
                    }
                    for row in body["records"]
                ],
                "partial": body["partial"],
                "pending": body["pending"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
