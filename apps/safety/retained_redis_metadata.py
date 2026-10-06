"""Opaque AUX review material, bound to an original physical RDB capture."""

import hashlib
import json
import re

from .rights import fingerprint
from .rights_exports import canonical

COLLECTOR_SOURCE_SHA256 = "41825a8c72d6171881ea36221419d2561cf2c52b1549bbec59cfcd0a7a38c318"
FIELDS = frozenset("schema source_sha256 source_origin_sha256 captured_at entries entries_sha256 collector_source_sha256 collector_binary_sha256 partial".split())
KNOWN = {b"redis-ver", b"redis-bits", b"ctime", b"used-mem", b"aof-base"}


def checked_aux(metadata, origin):
    if (
        not isinstance(metadata, dict) or set(metadata) != FIELDS
        or metadata["schema"] != "local-redis-rdb-aux-v1" or metadata["partial"] is not True
        or metadata["source_sha256"] != origin["source_sha256"]
        or metadata["source_origin_sha256"] != origin["source_origin_sha256"]
        or metadata["captured_at"] != origin["captured_at"]
        or metadata["collector_source_sha256"] != COLLECTOR_SOURCE_SHA256
        or not isinstance(metadata["collector_binary_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", metadata["collector_binary_sha256"])
        or not isinstance(metadata["entries"], list) or len(metadata["entries"]) > 64
        or hashlib.sha256(json.dumps(metadata["entries"], sort_keys=True).encode()).hexdigest() != metadata["entries_sha256"]
    ):
        raise ValueError("Exact AUX provenance required")
    total = 0
    for row in metadata["entries"]:
        if not isinstance(row, dict) or set(row) != {"field_hex", "value_hex"}:
            raise ValueError("Exact AUX record required")
        for field, limit in [("field_hex", 4096), ("value_hex", 262144)]:
            value = row[field]
            if not isinstance(value, str) or len(value) % 2 or len(value) > limit * 2 or not re.fullmatch(r"[0-9a-f]*", value):
                raise ValueError("Bounded exact AUX bytes required")
            total += len(value) // 2
        if total > 1024 * 1024:
            raise ValueError("AUX aggregate limit exceeded")
    return metadata


def review_material(metadata, origin_digest):
    rows = []
    for index, entry in enumerate(metadata["entries"]):
        field = bytes.fromhex(entry["field_hex"])
        rows.append({
            "reference": fingerprint(canonical({"origin": origin_digest, "aux_position": index})),
            "recognized_field": field.decode("ascii") if field in KNOWN else None,
            "field_digest": fingerprint(canonical({"field_hex": entry["field_hex"]})),
            "content_digest": fingerprint(canonical(entry)),
            "content": entry,
            "association": "infrastructure_scope_unreviewed",
        })
    return {
        "source_digest": origin_digest, "source_sha256": metadata["source_sha256"],
        "captured_at": metadata["captured_at"], "records": rows,
        "partial": True, "decision": "pending_independent_review",
    }
