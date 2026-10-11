"""Bounded pure HMAC reuse within one atomic coverage operation only."""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import get_ident

from django.conf import settings
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

MAX_ENTRIES = 128
MAX_INPUT_BYTES = 32 * 1024 * 1024
LARGE_INPUT = 4096
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
    secret = settings.SECRET_KEY
    if type(secret) not in (str, bytes):
        return native(value)
    large = len(value) > LARGE_INPUT or len(secret) > LARGE_INPUT
    entries = state["entries"]
    if large:
        # No full input hash here; collisions only locate candidates, never hits.
        index = (type(value), len(value), value[:INDEX_EDGE], value[-INDEX_EDGE:],
                 type(secret), len(secret), secret[:INDEX_EDGE], secret[-INDEX_EDGE:])
        for candidate in state["buckets"].get(index, ()):
            original, original_secret, digest = entries[candidate]
            if value == original and secret == original_secret:
                return digest
    else:
        key = (type(value), value, type(secret), secret)
        if key in entries:
            return entries[key]
    result = native(value)
    # Native reads its own settings: do not retain a result if those changed
    # during computation. Unicode upper bounds avoid allocating encoded inputs.
    if type(settings.SECRET_KEY) is not type(secret) or settings.SECRET_KEY != secret:
        return result
    size = len(value) * (4 if type(value) is str else 1)
    size += len(secret) * (4 if type(secret) is str else 1)
    if large:
        size += INDEX_OVERHEAD
    if len(entries) < MAX_ENTRIES and size <= MAX_INPUT_BYTES - state["bytes"]:
        if large:
            key = (_LARGE, len(entries))
            entries[key] = (value, secret, result)
            state["buckets"].setdefault(index, []).append(key)
        else:
            entries[key] = result
        state["bytes"] += size
    return result
