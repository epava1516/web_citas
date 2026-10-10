"""Operation-local transport borrowing; never cache object responses or authority."""

import os
from contextlib import contextmanager
from contextvars import ContextVar
from threading import get_ident

from django.conf import settings
from django.views.decorators.debug import sensitive_variables

_current = ContextVar("rights_object_read_clients", default=None)
MAX_CLIENTS = 4
SETTINGS = (
    "RIGHTS_OBJECT_ENDPOINT",
    "RIGHTS_OBJECT_REGION",
    "RIGHTS_OBJECT_ACCESS_KEY",
    "RIGHTS_OBJECT_SECRET_KEY",
    "RIGHTS_OBJECT_BUCKET",
    "RIGHTS_OBJECT_KEYS",
    "RIGHTS_OBJECT_ACTIVE_KEY",
    "SAFETY_ENCRYPTION_KEY",
    "SECRET_KEY",
    "PRODUCTION",
    "RIGHTS_OBJECT_STORAGE_ENABLED",
)


@contextmanager
@sensitive_variables()
def read_clients():
    """Own at most four clients; close best-effort without masking domain errors.

    Unsupported settings and overflow use the existing native factory lifecycle.
    Close failures are suppressed even on success: transport teardown cannot
    invalidate bytes already independently authenticated by the repository.
    """
    state = {"pid": os.getpid(), "thread": get_ident(), "clients": {}}
    token = _current.set(state)
    try:
        yield
    finally:
        clients = list(state["clients"].values())
        state["clients"].clear()
        _current.reset(token)
        for client in clients:
            try:
                client.close()
            except Exception:
                pass


@sensitive_variables()
def client(create):
    """Borrow transport only; factory must still recreate crypto on every call."""
    state = _current.get()
    if state is None or state["pid"] != os.getpid() or state["thread"] != get_ident():
        return create()
    values = tuple(getattr(settings, name) for name in SETTINGS)
    if any(type(value) not in (str, bytes, bool, int, type(None)) for value in values):
        return create()
    key = tuple((type(value), value) for value in values)
    if key in state["clients"]:
        return state["clients"][key]
    created = create()
    current = tuple(getattr(settings, name) for name in SETTINGS)
    if (
        any(type(value) not in (str, bytes, bool, int, type(None)) for value in current)
        or tuple((type(value), value) for value in current) != key
        or _current.get() is not state
        or state["pid"] != os.getpid()
        or state["thread"] != get_ident()
    ):
        # The native constructor can observe newer settings than our initial
        # snapshot. Never attach that transport to the previous configuration.
        return created
    if len(state["clients"]) < MAX_CLIENTS:
        state["clients"][key] = created
    return created
