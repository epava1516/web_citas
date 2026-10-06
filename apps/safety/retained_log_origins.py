"""Validate selected historical captures without claiming complete log coverage."""

import hashlib
import re
from datetime import datetime

from scripts.collect_access_resource_logs import MAX_SERVICE_BYTES, PROJECT, SERVICES

from .rights_exports import canonical

MAX_CAPTURES = 32
MAX_CONTENT_BYTES = 64 * 1024 * 1024
MAX_CIPHERTEXT_BYTES = 128 * 1024 * 1024
PENDING = [
    "subject_association_and_disclosure_review",
    "historical_or_removed_containers",
    "host_logs_and_mail_retention",
    "cache_and_backup_content_accounting",
]


def checked_capture(body, cutoff):
    if (
        not isinstance(body, dict)
        or set(body) != {"schema", "project", "captured_at", "records", "partial", "pending"}
        or body["schema"] != "local-access-log-origins-v1"
        or body["project"] != PROJECT
        or body["partial"] is not True
        or body["pending"] != PENDING
        or not isinstance(body["records"], list)
        or len(body["records"]) != len(SERVICES)
    ):
        raise ValueError("Exact partial historical capture required")
    captured = datetime.fromisoformat(body["captured_at"])
    if captured.tzinfo is None or captured > cutoff:
        raise ValueError("Historical capture outside inventory cutoff")
    seen, size = set(), 0
    for row in body["records"]:
        if (
            not isinstance(row, dict)
            or set(row)
            != {
                "service",
                "container",
                "image",
                "container_created_at",
                "stdout",
                "stderr",
                "stdout_sha256",
                "stderr_sha256",
            }
            or not all(isinstance(row[key], str) for key in row)
            or row["service"] not in SERVICES
            or row["service"] in seen
            or not row["container"]
            or not row["image"]
        ):
            raise ValueError("Exact retained service metadata required")
        created = datetime.fromisoformat(row["container_created_at"])
        if created.tzinfo is None or created > captured:
            raise ValueError("Container creation outside capture cutoff")
        seen.add(row["service"])
        for stream in ("stdout", "stderr"):
            raw = row[stream].encode()
            size += len(raw)
            if (
                len(raw) > MAX_SERVICE_BYTES
                or size > MAX_CONTENT_BYTES
                or hashlib.sha256(raw).hexdigest() != row[stream + "_sha256"]
            ):
                raise ValueError("Historical content altered or exceeds byte limit")
    return size


def checked_scoped_captures(body, case, inventory, cutoff):
    if (
        not isinstance(body, dict)
        or set(body)
        != {
            "schema",
            "project",
            "request",
            "inventory",
            "source_digest",
            "cutoff",
            "origins",
            "partial",
        }
        or body["schema"] != "local-log-retained-origins-scoped-v1"
        or body["project"] != PROJECT
        or body["partial"] is not True
        or case is None
        or inventory is None
        or inventory.request_id != case.pk
        or body["request"] != str(case.pk)
        or type(body["inventory"]) is not int
        or body["inventory"] != inventory.pk
        or body["source_digest"] != inventory.source_digest
        or body["cutoff"] != inventory.created_at.isoformat()
        or cutoff != inventory.created_at
        or not isinstance(body["origins"], list)
        or not 1 <= len(body["origins"]) <= MAX_CAPTURES
    ):
        raise ValueError("Exact historical log inventory scope required")
    seen, size, records = set(), 0, []
    for origin in body["origins"]:
        if (
            not isinstance(origin, dict)
            or set(origin) != {"capture", "capture_sha256", "ciphertext_sha256"}
            or not isinstance(origin["ciphertext_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", origin["ciphertext_sha256"]) is None
        ):
            raise ValueError("Historical origin identity required")
        capture = origin["capture"]
        size += checked_capture(capture, cutoff)
        digest = hashlib.sha256(canonical(capture).encode()).hexdigest()
        if digest != origin["capture_sha256"] or digest in seen or size > MAX_CONTENT_BYTES:
            raise ValueError("Duplicate, altered or oversized historical captures")
        seen.add(digest)
        records.extend(
            row | {"capture_digest": digest, "captured_at": capture["captured_at"]}
            for row in capture["records"]
        )
    return records
