"""Bounded physical census; opaque review never attributes global keys to a subject."""

import hashlib
import json
import re
from collections import Counter

from .retained_redis_metadata import review_material
from .rights import fingerprint
from .rights_exports import canonical

COLLECTOR_SOURCE_SHA256 = "9d9699d1ec9c9f4f665d7cdfdc6a0e1c0aeb474dda0e26d6250cc8c5921b6c9a"
FIELDS = frozenset("schema source_sha256 source_origin_sha256 captured_at source_bytes events events_sha256 collector_source_sha256 collector_binary_sha256 partial".split())
SPECIAL = frozenset("function module module_aux stream array hash_field_expiry cluster_slot".split())
EVENT_FIELDS = {
    "header": {"version"}, "database": {"database"},
    "database_size": {"database", "keys", "expires"},
    "aux": {"field_hex", "value_hex"},
    "key": {"database", "key_hex", "expiry", "lru_idle", "lfu_freq", "opcode", "data_type", "num_metadata"},
    "complete": {"source_bytes"},
} | {kind: set() for kind in SPECIAL}


def integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("Bounded physical metadata integer required")


def hex_bytes(value, limit):
    if not isinstance(value, str) or len(value) % 2 or len(value) > limit * 2 or not re.fullmatch(r"[0-9a-f]*", value):
        raise ValueError("Bounded exact physical metadata bytes required")
    return len(value) // 2


def checked_physical(metadata, origin):
    if (
        not isinstance(metadata, dict) or set(metadata) != FIELDS
        or metadata["schema"] != "local-redis-rdb-physical-metadata-v1"
        or metadata["partial"] is not True
        or any(metadata[field] != origin[field] for field in ["source_sha256", "source_origin_sha256", "captured_at"])
        or metadata["collector_source_sha256"] != COLLECTOR_SOURCE_SHA256
        or not isinstance(metadata["collector_binary_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", metadata["collector_binary_sha256"])
        or not isinstance(metadata["events"], list) or not 2 <= len(metadata["events"]) <= 8192
        or hashlib.sha256(json.dumps(metadata["events"], sort_keys=True).encode()).hexdigest() != metadata["events_sha256"]
    ):
        raise ValueError("Exact physical metadata provenance required")
    integer(metadata["source_bytes"], 1, 64 * 1024 * 1024)
    events, database, keys, auxes, aux_bytes, identities = metadata["events"], None, 0, 0, 0, set()
    for position, row in enumerate(events):
        if not isinstance(row, dict) or not isinstance(row.get("event"), str):
            raise ValueError("Exact physical metadata event required")
        event = row["event"]
        if event not in EVENT_FIELDS or set(row) != EVENT_FIELDS[event] | {"event"}:
            raise ValueError("Unknown physical metadata event")
        if position == 0 and event != "header" or position == len(events) - 1 and event != "complete":
            raise ValueError("Complete physical metadata envelope required")
        if event == "header":
            if position != 0:
                raise ValueError("Duplicate RDB header")
            integer(row["version"], 1, 12)
        elif event == "complete":
            if position != len(events) - 1 or type(row["source_bytes"]) is not int or row["source_bytes"] != metadata["source_bytes"]:
                raise ValueError("Exact physical byte consumption required")
        elif event == "database":
            integer(row["database"], 0, 2147483647)
            database = row["database"]
        elif event in {"database_size", "key"}:
            if database is None or type(row["database"]) is not int or row["database"] != database:
                raise ValueError("Physical database context required")
            if event == "database_size":
                integer(row["keys"], 0, 2**64 - 1)
                integer(row["expires"], 0, row["keys"])
            else:
                keys += 1
                hex_bytes(row["key_hex"], 4096)
                identity = (database, row["key_hex"])
                if keys > 4096 or identity in identities:
                    raise ValueError("Bounded distinct physical keys required")
                identities.add(identity)
                integer(row["expiry"], -1, 2**63 - 1)
                integer(row["lru_idle"], -1, 2**63 - 1)
                integer(row["lfu_freq"], -1, 255)
                integer(row["opcode"], 0, 255)
                integer(row["data_type"], 0, 255)
                integer(row["num_metadata"], 0, 2147483647)
        elif event == "aux":
            auxes += 1
            aux_bytes += hex_bytes(row["field_hex"], 4096) + hex_bytes(row["value_hex"], 262144)
            if auxes > 64 or aux_bytes > 1024 * 1024:
                raise ValueError("Physical AUX aggregate limit exceeded")
    return metadata


def physical_review(metadata, origin_digest):
    events = metadata["events"]
    aux = [{key: row[key] for key in ["field_hex", "value_hex"]} for row in events if row["event"] == "aux"]
    review = review_material(metadata | {"entries": aux}, origin_digest)
    records = []
    for position, row in enumerate(events):
        if row["event"] == "aux":
            continue
        records.append({
            "reference": fingerprint(canonical({"origin": origin_digest, "physical_position": position})),
            "category": row["event"], "content_digest": fingerprint(canonical(row)),
            "association": "infrastructure_scope_unreviewed",
        })
    return review | {
        "physical_records": records,
        "physical_summary": {
            "source_bytes": metadata["source_bytes"],
            "consumed_bytes": events[-1]["source_bytes"],
            "rdb_version": events[0]["version"],
            "event_counts": dict(sorted(Counter(row["event"] for row in events).items())),
            "additional_formats_pending": sorted({row["event"] for row in events} & SPECIAL),
        },
    }
