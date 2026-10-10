"""Pure SHA-256 reuse only after an exact comparison with freshly read bytes."""

import hashlib
import os
from contextlib import contextmanager
from contextvars import ContextVar
from threading import get_ident
from uuid import UUID

from django.db import transaction
from django.views.decorators.debug import sensitive_variables

MAX_ENTRIES = 16
MAX_BYTES = 64 * 1024 * 1024
_current = ContextVar("rights_operation_content_digests", default=None)


@contextmanager
@sensitive_variables()
def operation_content_digests():
    connection = transaction.get_connection()
    if not connection.in_atomic_block:
        raise RuntimeError("Content digest operation requires an atomic transaction")
    state = {"connection": connection, "atomic": connection.atomic_blocks[-1],
             "thread": get_ident(), "pid": os.getpid(), "entries": {}, "bytes": 0}
    token = _current.set(state)
    try:
        yield
    finally:
        state["entries"].clear()
        state["bytes"] = 0
        _current.reset(token)


def _supported_key(key):
    # Bounded immutable metadata: three IDs, no caller-defined hash/equality.
    # At most 16 triples and 16 hex digests supplement the 64MiB byte limit.
    if type(key) is not tuple or len(key) != 3:
        return False
    for value in key:
        if type(value) is UUID:
            continue
        if type(value) in (str, bytes) and len(value) <= 128:
            continue
        if type(value) is int and value.bit_length() <= 128:
            continue
        return False
    return True


def _native_sha256(content):
    return hashlib.sha256(content).hexdigest()


@sensitive_variables()
def content_digest(key, content):
    """IDs locate old bytes; only complete equality permits pure digest reuse.

    Caller MUST supply bytes from its current physical read, never metadata or
    a presumed immutable source. This function validates no access or evidence.
    """
    state = _current.get()
    if (state is None or type(content) is not bytes or not _supported_key(key)
            or state["pid"] != os.getpid() or state["thread"] != get_ident()
            or transaction.get_connection() is not state["connection"]
            or not state["connection"].in_atomic_block
            or not any(block is state["atomic"] for block in state["connection"].atomic_blocks)):
        return _native_sha256(content)
    old = state["entries"].get(key)
    if old is not None:
        if content == old[0]:
            return old[1]
        # Different bytes always get a fresh native hash; never replace the
        # retained original, including changes with the same length or SHA.
        return _native_sha256(content)
    digest = _native_sha256(content)
    if len(state["entries"]) < MAX_ENTRIES and len(content) <= MAX_BYTES - state["bytes"]:
        state["entries"][key] = (content, digest)
        state["bytes"] += len(content)
    return digest
