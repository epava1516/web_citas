"""Versioned canonical JSON for rights; content hashes never authorize an action."""

import math

import orjson
from blake3 import blake3

CANONICAL_SCHEMA = "rights-canonical-json-v2"
CONTENT_REFERENCE_SCHEMA = "b3v2"


def _check(value, depth=0):
    # orjson otherwise silently converts nonfinite floats to null and accepts UUID,
    # dataclass and datetime values that the former JSON encoder rejected.
    if depth > 200:
        raise ValueError("Canonical JSON exceeds maximum nesting")
    kind = type(value)
    if value is None or kind in (str, bool, int):
        return
    if kind is float:
        if not math.isfinite(value):
            raise ValueError("Canonical JSON requires finite numbers")
        return
    if kind is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("Canonical JSON requires string keys")
            _check(item, depth + 1)
        return
    if kind in (list, tuple):
        for item in value:
            _check(item, depth + 1)
        return
    raise TypeError("Canonical JSON requires explicit JSON values")


def canonical_bytes(value):
    """Sorted UTF-8, compact JSON; no implicit conversion or Unicode normalization."""
    _check(value)
    return orjson.dumps(value, option=orjson.OPT_SORT_KEYS)


def canonical(value):
    return canonical_bytes(value).decode("utf-8")


def content_reference(value):
    """Unkeyed, domain/version-separated content identity; NOT a secret signature."""
    payload = CANONICAL_SCHEMA.encode() + b"\0" + canonical_bytes(value)
    return CONTENT_REFERENCE_SCHEMA + ":" + blake3(payload).hexdigest()
