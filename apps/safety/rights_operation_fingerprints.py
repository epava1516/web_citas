"""Bounded pure HMAC reuse within one atomic coverage operation only."""

from contextlib import contextmanager
from contextvars import ContextVar
from threading import get_ident

from django.conf import settings
from django.db import transaction
from django.views.decorators.debug import sensitive_variables

MAX_ENTRIES = 128
MAX_INPUT_BYTES = 32 * 1024 * 1024
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
        "bytes": 0,
    }
    token = _current.set(state)
    try:
        yield
    finally:
        state["entries"].clear()
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
    key = (type(value), value, type(secret), secret)
    entries = state["entries"]
    if key in entries:
        return entries[key]
    result = native(value)
    # Native reads its own settings: do not retain a result if those changed
    # during computation. Unicode upper bounds avoid allocating encoded inputs.
    if type(settings.SECRET_KEY) is not type(secret) or settings.SECRET_KEY != secret:
        return result
    size = len(value) * (4 if type(value) is str else 1)
    size += len(secret) * (4 if type(secret) is str else 1)
    if len(entries) < MAX_ENTRIES and size <= MAX_INPUT_BYTES - state["bytes"]:
        entries[key] = result
        state["bytes"] += size
    return result
