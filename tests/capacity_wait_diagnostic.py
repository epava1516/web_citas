"""Finite owned-worker driver spans; no SQL text, payload or authority retained."""
import sys
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from functools import wraps
from unittest.mock import patch

from tests.capacity_chain_diagnostic import Collector

_active = ContextVar("capacity_wait_diagnostic", default=None)


def measured(function, name, *, phase=False, fetch=False):
    @wraps(function)
    def wrapped(*args, **kwargs):
        state = _active.get()
        if state is None:
            return function(*args, **kwargs)
        collector, phases = state
        label = name if phase else (phases[-1] if phases else "outside") + "." + name
        if phase:
            phases.append(name)
        try:
            with collector.span(label):
                result = function(*args, **kwargs)
            if fetch:
                collector.fetch_counts.setdefault(label, []).append(
                    len(result) if isinstance(result, list) else int(result is not None))
            return result
        finally:
            if phase:
                phases.pop()
    wrapped.__wait_original__ = function
    return wrapped


@contextmanager
def scope():
    import psycopg
    from django.db import connection

    from apps.listings.models import Revision
    from apps.safety import evidence_chain, rights_exports, rights_portability_review

    if _active.get() is not None:
        raise RuntimeError("Nested wait diagnosis forbidden")
    collector = Collector()
    collector.fetch_counts = {}
    targets = [(rights_exports.source_copy, "source"),
               (rights_portability_review.validate_approved_assessment, "validate_assessment"),
               (evidence_chain.require_runtime_chain, "require_runtime_chain"),
               (evidence_chain.validate_chain, "validate_chain"),
               (evidence_chain._runtime_is_trusted, "runtime_trust"),
               (evidence_chain._source_rows, "chain_sources")]
    replacements = [(fn, measured(fn, name, phase=True)) for fn, name in targets]
    with ExitStack() as restore:
        for module_name, module in tuple(sys.modules.items()):
            if not module_name.startswith("apps.safety.") or module is None:
                continue
            for name, value in tuple(vars(module).items()):
                for original, wrapper in replacements:
                    if value is original:
                        restore.enter_context(patch.object(module, name, wrapper))
        # ServerCursor overrides execute/fetch: patch its own implementations too.
        # Inherited methods stay patched once through Cursor; avoid double counting.
        methods = [(cls, name, getattr(cls, name))
                   for cls in (psycopg.Cursor, psycopg.ServerCursor)
                   for name in ("execute", "executemany", "fetchone", "fetchmany", "fetchall")
                   if name in cls.__dict__]
        for cls, name, original in methods:
            restore.enter_context(patch.object(cls, name,
                measured(original, ("server_" if cls is psycopg.ServerCursor else "driver_") + name,
                         fetch=name.startswith("fetch"))))
        restore.enter_context(patch.object(Revision, "from_db",
            classmethod(measured(Revision.from_db.__func__, "revision_hydrate"))))
        for name in ("sync", "__exit__"):
            restore.enter_context(patch.object(psycopg.Pipeline, name,
                measured(getattr(psycopg.Pipeline, name), "pipeline_" + name)))
        restore.enter_context(patch.object(connection, "get_new_connection",
            measured(connection.get_new_connection, "connection_open")))
        token = _active.set((collector, []))
        try:
            yield collector
        finally:
            _active.reset(token)
            for module_name, module in tuple(sys.modules.items()):
                if module_name.startswith("apps.safety.") and module is not None:
                    for name, value in tuple(vars(module).items()):
                        original = getattr(value, "__wait_original__", None)
                        if original is not None:
                            setattr(module, name, original)
