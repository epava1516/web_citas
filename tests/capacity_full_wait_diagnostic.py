"""Owned sync-worker diagnosis: full domain phases and server row adaptation."""
import importlib
import sys
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

from tests.capacity_phase_spans import PHASE_TARGETS
from tests.capacity_wait_diagnostic import _active, measured
from tests.capacity_wait_diagnostic import scope as driver_scope


class AdaptationProxy:
    def __init__(self, original):
        self.original = original

    def __getattr__(self, name):
        return getattr(self.original, name)

    def load_rows(self, *args, **kwargs):
        return measured(self.original.load_rows, "server_adapt_rows")(*args, **kwargs)

    def set_pgresult(self, *args, **kwargs):
        return measured(self.original.set_pgresult, "server_set_result")(*args, **kwargs)


def adapted_fetch(original):
    def wrapped(cursor, *args, **kwargs):
        if _active.get() is None:
            return (yield from original(cursor, *args, **kwargs))
        previous = cursor._tx
        cursor._tx = AdaptationProxy(previous)
        try:
            return (yield from original(cursor, *args, **kwargs))
        finally:
            cursor._tx = previous
    return wrapped


@contextmanager
def scope():
    import psycopg

    # Load only the fixed diagnostic inventory; no domain operation or authority read.
    targets = [(getattr(importlib.import_module(module), name), phase)
               for phase, (module, name) in PHASE_TARGETS.items()
               if phase not in ("source", "validate_assessment")]
    with driver_scope() as collector, ExitStack() as restore:
        for module_name, module in tuple(sys.modules.items()):
            if not module_name.startswith("apps.safety.") or module is None:
                continue
            for name, value in tuple(vars(module).items()):
                for original, phase in targets:
                    if value is original:
                        restore.enter_context(patch.object(module, name, measured(original, phase, phase=True)))
        restore.enter_context(patch.object(psycopg.ServerCursor, "_fetch_gen",
                                          adapted_fetch(psycopg.ServerCursor._fetch_gen)))
        try:
            yield collector
        finally:
            # Restore aliases imported while the scope was active as well.
            for module_name, module in tuple(sys.modules.items()):
                if module_name.startswith("apps.safety.") and module is not None:
                    for name, value in tuple(vars(module).items()):
                        original = getattr(value, "__wait_original__", None)
                        if original is not None:
                            setattr(module, name, original)
