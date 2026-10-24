"""Bounded pure HMAC reuse within one atomic coverage operation only."""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import get_ident

from django.db import transaction
from django.views.decorators.debug import sensitive_variables

from apps.core.domain_signing import domain_signing_key

MAX_ENTRIES = 128
MAX_INPUT_BYTES = 32 * 1024 * 1024
LARGE_INPUT = 64 * 1024
INDEX_EDGE = 32
# Conservative extra charge for edge slices, index/entry tuples, bucket/list and
# digest per large entry. Small entries retain the existing exact-key layout.
INDEX_OVERHEAD = 2048
_LARGE = object()
_current = ContextVar("rights_operation_fingerprints", default=None)


@contextmanager
@sensitive_variables()
def operation_fingerprints():
    connection = transaction.get_connection()
    if not connection.in_atomic_block:
        raise RuntimeError("Fingerprint operation requires an atomic transaction")
    state = {
        "connection": connection,
        "atomic": connection.atomic_blocks[-1],
        "thread": get_ident(),
        "entries": {},
        "buckets": {},
        "bytes": 0,
    }
    token = _current.set(state)
    try:
        yield
    finally:
        state["entries"].clear()
        state["buckets"].clear()
        _current.reset(token)


@sensitive_variables()
def fingerprint(value, native):
    """Reuse only the fixed rights-request-v1/SHA-256 native producer.

    ``native`` must implement that exact producer; it is an internal adapter,
    not a general callable memo. Callable identity is deliberately excluded:
    rights.fingerprint creates a new equivalent lambda on every invocation.
    """
    state = _current.get()
    if (
        state is None
        or state["thread"] != get_ident()
        or transaction.get_connection() is not state["connection"]
        or not state["connection"].in_atomic_block
        or not any(block is state["atomic"] for block in state["connection"].atomic_blocks)
        or type(value) not in (str, bytes)
    ):
        return native(value)
    # Read the current secret on EVERY invocation, including cache hits. Exact
    # immutable types alone avoid conversions and custom equality/hash behavior.
    secret = domain_signing_key()
    if type(secret) not in (str, bytes):
        return native(value)
    large = len(value) > LARGE_INPUT or len(secret) > LARGE_INPUT
    entries = state["entries"]
    if large:
        # No full input hash here; collisions only locate candidates, never hits.
        index = (type(value), len(value), value[:INDEX_EDGE], value[-INDEX_EDGE:],
                 type(secret), len(secret), secret[:INDEX_EDGE], secret[-INDEX_EDGE:])
        bucket = state["buckets"].get(index)
        if type(bucket) is dict:
            # Promoted collision buckets use full exact hash/equality, just as
            # the original memo. Index types already distinguish str/bytes.
            candidate = bucket.get((value, secret))
            if candidate is not None:
                return entries[candidate][2]
        elif bucket:
            original, original_secret, digest = entries[bucket[0]]
            if value == original and secret == original_secret:
                return digest
    else:
        key = (type(value), value, type(secret), secret)
        if key in entries:
            return entries[key]
    result = native(value)
    # Native reads its own settings: do not retain a result if those changed
    # during computation. Unicode upper bounds avoid allocating encoded inputs.
    current_secret = domain_signing_key()
    if type(current_secret) is not type(secret) or current_secret != secret:
        return result
    size = len(value) * (4 if type(value) is str else 1)
    size += len(secret) * (4 if type(secret) is str else 1)
    if large:
        size += INDEX_OVERHEAD
    if len(entries) < MAX_ENTRIES and size <= MAX_INPUT_BYTES - state["bytes"]:
        if large:
            key = (_LARGE, len(entries))
            entries[key] = (value, secret, result)
            bucket = state["buckets"].get(index)
            if bucket is None:
                state["buckets"][index] = [key]
            elif type(bucket) is dict:
                bucket[(value, secret)] = key
            else:
                previous = bucket[0]
                original, original_secret, _ = entries[previous]
                state["buckets"][index] = {(original, original_secret): previous,
                                          (value, secret): key}
        else:
            entries[key] = result
        state["bytes"] += size
    return result
