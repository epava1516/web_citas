"""Fingerprint explicitly supplied retained ciphertexts; never infer subject or coverage."""

import argparse
import hashlib
import json
import os
import stat
import time
from datetime import UTC, datetime
from pathlib import Path

MAX_BYTES = 256 * 1024 * 1024
MAX_EVIDENCE_BYTES = 8 * 1024 * 1024


def log_capture_references(path):
    """Read declared capture metadata only; never search or decrypt the host."""
    path = Path(path)
    with path.open("rb") as stream:
        raw = stream.read(MAX_EVIDENCE_BYTES + 1)
    if len(raw) > MAX_EVIDENCE_BYTES:
        raise ValueError("Evidence exceeds inventory limit")
    body = json.loads(raw)
    references = []

    def visit(value, pointer):
        if isinstance(value, dict):
            if {"encrypted_artifact", "captured_at", "services"} <= value.keys():
                from scripts.collect_access_resource_logs import SERVICES

                captured = datetime.fromisoformat(value["captured_at"])
                origin = value["encrypted_artifact"]
                if (
                    captured.tzinfo is None
                    or not isinstance(origin, str)
                    or not Path(origin).is_absolute()
                ):
                    raise ValueError("Exact absolute capture path and aware cutoff required")
                services = value["services"]
                if (
                    not isinstance(services, list)
                    or len(services) != len(SERVICES)
                    or any(
                        not isinstance(row, dict)
                        or set(row) != {"service", "stdout_bytes", "stderr_bytes"}
                        or row["service"] not in SERVICES
                        or any(
                            type(row[key]) is not int or row[key] < 0
                            for key in ("stdout_bytes", "stderr_bytes")
                        )
                        for row in services
                    )
                    or {row["service"] for row in services} != set(SERVICES)
                ):
                    raise ValueError("Exact service byte metadata required; no log content allowed")
                references.append(
                    {
                        "path": origin,
                        "captured_at": value["captured_at"],
                        "evidence": str(path),
                        "evidence_sha256": hashlib.sha256(raw).hexdigest(),
                        "pointer": pointer,
                        "declared_services": value["services"],
                        "declaration_verified_against_content": False,
                    }
                )
            for key, item in value.items():
                escaped = key.replace("~", "~0").replace("/", "~1")
                visit(item, pointer + "/" + escaped)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, pointer + "/" + str(index))

    visit(body, "")
    return references


def inventory_log_captures(evidence_paths):
    """Keep missing/unsafe sources visible; duplicate references are not new sources."""
    declarations = {}
    evidence = []
    for path in evidence_paths:
        references = log_capture_references(path)
        evidence.append({"path": str(path), "capture_references": len(references)})
        for reference in references:
            declarations.setdefault(reference["path"], []).append(reference)
    origins = []
    for path, references in sorted(declarations.items()):
        row = {"path": path, "declarations": references, "pending": []}
        try:
            row.update(inspect_origin(path))
            row["status"] = "ciphertext_inventoried"
        except FileNotFoundError:
            row["status"] = "missing"
            row["pending"].append("declared_origin_missing")
        except (OSError, ValueError):
            row["status"] = "unreadable_or_unsafe"
            row["pending"].append("declared_origin_not_safely_inventoried")
        if len({reference["captured_at"] for reference in references}) != 1:
            row["pending"].append("conflicting_capture_declarations")
        if (
            len(
                {
                    json.dumps(reference["declared_services"], sort_keys=True)
                    for reference in references
                }
            )
            != 1
        ):
            row["pending"].append("conflicting_service_declarations")
        origins.append(row)
    return {
        "schema": "retained-log-capture-inventory-v1",
        "evidence": evidence,
        "origins": origins,
        "capture_references": sum(len(row["declarations"]) for row in origins),
        "unique_origins": len(origins),
        "declared_sources_inventoried": bool(origins)
        and all(
            row["status"] == "ciphertext_inventoried" and not row["pending"] for row in origins
        ),
        "partial": True,
        "subject_association_verified": False,
        "pending": [
            "capture_metadata_and_original_content_validation",
            "historical_content_differences_and_subject_association",
            "independent_disclosure_review",
            "other_retained_host_mail_cache_backup_sources",
            "retention_authority",
        ],
    }


def inspect_origin(path):
    path = Path(path)
    if path.suffix != ".encrypted":
        raise ValueError("Only explicit encrypted origins are supported")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or stat.S_IMODE(before.st_mode) & 0o077
            or before.st_size > MAX_BYTES
        ):
            raise ValueError("Unsafe or oversized retained origin")
        digest = hashlib.sha256()
        size = 0
        while block := source.read(64 * 1024):
            size += len(block)
            if size > MAX_BYTES:
                raise ValueError("Retained origin grew beyond limit")
            digest.update(block)
        after = os.fstat(source.fileno())

        def identity(row):
            return (row.st_dev, row.st_ino, row.st_size, row.st_mtime_ns, row.st_ctime_ns)

        if identity(before) != identity(after) or size != before.st_size:
            raise ValueError("Retained origin changed during inventory")
        if identity(after) != identity(path.lstat()):
            raise ValueError("Retained origin path changed during inventory")
    return {"path": str(path.absolute()), "bytes": size, "sha256": digest.hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--origin", type=Path, action="append")
    inputs.add_argument(
        "--evidence",
        type=Path,
        action="append",
        help="Exact JSON acta declaring retained log captures; repeatable",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    rows = [inspect_origin(path) for path in args.origin or []]
    body = (
        inventory_log_captures(args.evidence)
        if args.evidence
        else {
            "schema": "retained-origin-inventory-v1",
            "observed_at": datetime.now(UTC).isoformat(),
            "origins": rows,
            "partial": True,
            "subject_association_verified": False,
            "pending": ["other_retained_sources", "subject_association", "retention_authority"],
        }
    )
    body["observed_at"] = datetime.now(UTC).isoformat()
    body["observed_seconds"] = time.monotonic() - started
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(body, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    print(
        json.dumps(
            {
                "origins": len(body["origins"]),
                "bytes": sum(row.get("bytes", 0) for row in body["origins"]),
                "partial": True,
                "observed_seconds": body["observed_seconds"],
            }
        )
    )


if __name__ == "__main__":
    main()
