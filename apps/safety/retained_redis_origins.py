"""Scoped partial Redis sources; RDB reconstruction is not command history."""

import base64
import hashlib
import math
import re
from datetime import UTC, datetime
from io import BytesIO
from urllib.parse import urlparse

from django.conf import settings

from .redis_history_scope import scoped_history
from .redis_retained_history import MAX_BYTES, inspect_aof
from .rights import fingerprint
from .rights_exports import canonical

PARSER_COMMIT = "bc5f295c98b40c2c33099d9d72ab30ce9e595dc7"
RDB_FIELDS = frozenset(
    "schema source_kind source_schema source_sha256 source_origin_sha256 captured_at representation "
    "content_base64 sha256 decoder partial pending decoder_observed_seconds".split()
)
AOF_FIELDS = frozenset("schema project captured_at sha256 content_base64 partial".split())


def transport_scope():
    options = settings.CELERY_BROKER_TRANSPORT_OPTIONS
    if (
        urlparse(settings.CELERY_BROKER_URL).path not in {"", "/0"}
        or set(options) != {"global_keyprefix"}
        or not isinstance(options.get("global_keyprefix"), str)
        or not options["global_keyprefix"]
        or not isinstance(settings.CELERY_TASK_DEFAULT_QUEUE, str)
        or not settings.CELERY_TASK_DEFAULT_QUEUE
        or getattr(settings, "CELERY_TASK_ROUTES", None)
        or getattr(settings, "CELERY_TASK_QUEUES", None)
    ):
        raise ValueError("Exact broker scope required")
    return options["global_keyprefix"], settings.CELERY_TASK_DEFAULT_QUEUE


def checked_origin(origin, cutoff):
    if not isinstance(origin, dict) or origin.get("partial") is not True:
        raise ValueError("Partial retained origin required")
    rdb = origin.get("schema") == "local-redis-rdb-reconstruction-v1"
    if set(origin) != (RDB_FIELDS if rdb else AOF_FIELDS):
        raise ValueError("Exact retained origin fields required")
    captured = datetime.fromisoformat(origin["captured_at"])
    if captured.tzinfo is None or captured > cutoff:
        raise ValueError("Origin outside inventory cutoff")
    if not re.fullmatch(r"[0-9a-f]{64}", origin["sha256"]):
        raise ValueError("Origin hash required")
    raw = base64.b64decode(origin["content_base64"], validate=True)
    if len(raw) > (8 * 1024 * 1024 if rdb else MAX_BYTES) or hashlib.sha256(raw).hexdigest() != origin["sha256"]:
        raise ValueError("Origin reconstruction changed")
    if not rdb:
        if origin["schema"] != "local-redis-aof-origin-v1" or origin["project"] != "web-modelos":
            raise ValueError("Original partial AOF required")
        return raw, "aof_command_history", (origin["sha256"], captured.isoformat())
    decoder = origin["decoder"]
    duration = origin["decoder_observed_seconds"]
    if (
        origin["source_kind"] != "rdb_snapshot_state"
        or origin["source_schema"] not in {"local-redis-snapshot-origin-v1", "local-redis-base-origin-v1"}
        or origin["representation"] != "reconstructed-resp-not-original-command-history"
        or origin["pending"] != ["snapshot_metadata_scope_review", "historical_redis_coverage"]
        or not isinstance(decoder, dict)
        or set(decoder) != {"version", "source_commit", "binary_sha256"}
        or decoder["version"] != "2.4.0"
        or decoder["source_commit"] != PARSER_COMMIT
        or type(duration) not in {int, float}
        or not math.isfinite(duration)
        or not 0 <= duration <= 3600
        or any(not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value) for value in [
            origin["source_sha256"], origin["source_origin_sha256"], decoder["binary_sha256"],
        ])
    ):
        raise ValueError("RDB reconstruction provenance changed")
    return raw, "rdb_snapshot_state", (origin["source_origin_sha256"], captured.isoformat())


def snapshot_expirations(raw, result, digest):
    locations, expires, blocked = {}, {}, []
    database = 0

    def visit(offset, command, args):
        nonlocal database
        if command == "SELECT":
            try:
                database = int(args[1]) if len(args) == 2 else None
            except (TypeError, ValueError):
                database = None
            return
        if database != 0 or len(args) < 2 or not isinstance(args[1], bytes):
            return
        key = args[1]
        if command == "PEXPIREAT":
            try:
                if len(args) != 3 or len(expires) >= 1000:
                    raise ValueError
                expires[key] = datetime.fromtimestamp(int(args[2]) / 1000, UTC).isoformat()
            except (TypeError, ValueError, OverflowError, OSError):
                blocked.append("snapshot_expiration_unavailable")
        references = []
        if command in {"LPUSH", "RPUSH", "HSET", "HMSET"}:
            count = len(args) - 2 if command in {"LPUSH", "RPUSH"} else (len(args) - 2) // 2
            references = [fingerprint(canonical({"origin": digest, "offset": offset, "position": i})) for i in range(count)]
        elif command in {"SET", "SETEX", "PSETEX"}:
            references = [fingerprint(canonical({"origin": digest, "result_offset": offset}))]
        for reference in references:
            if len(locations) >= 1000:
                blocked.append("snapshot_reference_limit")
                break
            locations[reference] = key

    inspection = inspect_aof(BytesIO(raw), on_command=visit)
    blocked.extend(inspection["pending"])
    for row in result["records"] + result["result_records"]:
        key = locations.get(row["reference"])
        row["data"] = row["data"] | {
            "source_kind": "rdb_snapshot_state",
            "snapshot_expiration_at": expires.get(key),
        }
    return blocked


def read_bundle(body, blob_ids, cutoff, *, case, inventory):
    if (
        set(body) != {"schema", "project", "request", "inventory", "source_digest", "cutoff", "origins", "partial"}
        or body["schema"] != "local-redis-retained-origins-scoped-v1"
        or body["project"] != "web-modelos" or body["partial"] is not True
        or case is None or inventory is None or inventory.request_id != case.pk
        or body["request"] != str(case.pk) or type(body["inventory"]) is not int
        or body["inventory"] != inventory.pk or body["source_digest"] != inventory.source_digest
        or body["cutoff"] != inventory.created_at.isoformat() or cutoff != inventory.created_at
        or not isinstance(body["origins"], list) or not 1 <= len(body["origins"]) <= 16
    ):
        raise ValueError("Exact scoped retained source bundle required")
    prefix, queue = transport_scope()
    combined = {"records": [], "result_records": [], "technical_result_evidence": [], "blocked": [], "origins": []}
    pending, identities, total = {"historical_redis_coverage"}, set(), 0
    for origin in body["origins"]:
        raw, kind, identity = checked_origin(origin, cutoff)
        identity = kind, identity
        if identity in identities:
            raise ValueError("Duplicate retained physical source")
        identities.add(identity)
        total += len(raw)
        if total > MAX_BYTES:
            raise ValueError("Retained origin aggregate byte limit")
        digest = fingerprint(canonical(origin))
        result = scoped_history(raw, blob_ids, prefix=prefix, queue=queue, origin_digest=digest)
        if kind == "rdb_snapshot_state":
            result["blocked"].extend(snapshot_expirations(raw, result, digest))
            for row in result["records"] + result["result_records"]:
                row["data"]["snapshot_captured_at"] = origin["captured_at"]
            pending.update(origin["pending"])
        else:
            for row in result["records"] + result["result_records"]:
                row["data"]["source_kind"] = kind
        for field in ["records", "result_records", "technical_result_evidence", "blocked"]:
            combined[field].extend(result[field])
        if sum(len(combined[k]) for k in ["records", "result_records", "technical_result_evidence"]) > 1000:
            raise ValueError("Retained origin aggregate record limit")
        pending.update(result["pending"])
        combined["origins"].append({"kind": kind, "digest": digest, "captured_at": origin["captured_at"], "representation_sha256": origin["sha256"]})
    return combined | {"configured": True, "partial": True, "origin_digest": fingerprint(canonical(body)), "pending": sorted(pending), "blocked": sorted(set(combined["blocked"]))}
