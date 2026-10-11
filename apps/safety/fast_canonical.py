"""Versioned canonical JSON for rights; content hashes never authorize an action."""

import math
import sys

import orjson
from blake3 import blake3

CANONICAL_SCHEMA = "rights-canonical-json-v2"
CONTENT_REFERENCE_SCHEMA = "b3v2"


def reference_check(value, depth=0):
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
            reference_check(item, depth + 1)
        return
    if kind in (list, tuple):
        for item in value:
            reference_check(item, depth + 1)
        return
    raise TypeError("Canonical JSON requires explicit JSON values")


def _check(value, depth=0):
    # Keep the original Python body in this frame at recursion-budget edges.
    # Do not call the Python loader where its own frames could change acceptance.
    if type(depth) is int and depth == 0:
        threshold = sys.getrecursionlimit() - 512
        frame_count = 0
        frame = None
        if threshold > 0:
            frame = sys._getframe()
            try:
                while frame is not None and frame_count < threshold:
                    frame_count += 1
                    if frame_count >= threshold:
                        break
                    frame = frame.f_back
            finally:
                # Never retain the caller chain in fallback/error tracebacks.
                frame = None
        if frame_count < threshold:
            try:
                from .canonical_kernel_loader import validated_kernel
            except ModuleNotFoundError as error:
                if error.name != 'apps.safety.canonical_kernel_loader':
                    raise
            else:
                kernel = validated_kernel()
                if kernel is not None and kernel.try_check(value, depth):
                    return
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
