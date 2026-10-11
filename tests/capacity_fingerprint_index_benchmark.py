"""Finite synthetic pure-HMAC comparison, no request/capacity acceptance."""

import statistics
import time
from threading import get_ident

from django.conf import settings
from django.db import transaction
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables

from apps.safety import rights_operation_fingerprints as memo


@sensitive_variables()
def reference_fingerprint(value, native):
    """Reuse only the fixed rights-request-v1/SHA-256 native producer.

    ``native`` must implement that exact producer; it is an internal adapter,
    not a general callable memo. Callable identity is deliberately excluded:
    rights.fingerprint creates a new equivalent lambda on every invocation.
    """
    state = memo._current.get()
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
    if len(entries) < memo.MAX_ENTRIES and size <= memo.MAX_INPUT_BYTES - state["bytes"]:
        entries[key] = result
        state["bytes"] += size
    return result


def _fresh(value):
    if type(value) is bytes:
        return bytes(bytearray(value))
    return "".join((value[:-1], value[-1:]))


def measure(function, kind, size, scenario):
    base = "a" * 32 + "x" * max(0, size - 64) + "z" * 32 if size >= 64 else "x" * size
    if kind is bytes:
        base = base.encode()
    calls = []
    for index in range(8):
        value = base
        if scenario in {"miss", "collision", "late-collision"}:
            marker = str(index) if kind is str else str(index).encode()
            if scenario == "collision":
                value = base[:32] + marker + base[33:]
            elif scenario == "late-collision":
                value = base[:-33] + marker + base[-32:]
            else:
                value = marker + base[1:]
        calls.append(value if scenario == "same-object" else _fresh(value))
    native_calls = 0

    def native(value):
        nonlocal native_calls
        native_calls += 1
        return salted_hmac("rights-request-v1", value, algorithm="sha256").hexdigest()

    with transaction.atomic(), memo.operation_fingerprints():
        effective = None
        if scenario == "saturated-bucket":
            charge = len(base) * (4 if kind is str else 1)
            secret = settings.SECRET_KEY
            charge += len(secret) * (4 if type(secret) is str else 1)
            if function is memo.fingerprint:
                charge += memo.INDEX_OVERHEAD
            effective = min(memo.MAX_ENTRIES, memo.MAX_INPUT_BYTES // charge)
            for index in range(effective):
                marker = f"{index:04d}"
                if kind is bytes:
                    marker = marker.encode()
                function(base[:-36] + marker + base[-32:], native)
            marker = "9999" if kind is str else b"9999"
            overflow = base[:-36] + marker + base[-32:]
            calls = [_fresh(overflow) for _ in range(8)]
            native_calls = 0
        begin_wall, begin_cpu = time.perf_counter(), time.process_time()
        results = [function(value, native) for value in calls]
        cpu, wall = time.process_time() - begin_cpu, time.perf_counter() - begin_wall
        state = memo._current.get()
        entries, retained = len(state["entries"]), state["bytes"]
        candidates = max((len(bucket) for bucket in state["buckets"].values()), default=0)
    assert all(result == salted_hmac("rights-request-v1", value, algorithm="sha256").hexdigest()
               for result, value in zip(results, calls, strict=True))
    return {"wall": wall, "cpu": cpu, "native_calls": native_calls,
            "entries": entries, "retained_bytes": retained,
            "bucket_candidates": candidates, "effective_saturation": effective}


def benchmark():
    rows = []
    for kind in (str, bytes):
        for size in (128, 4097, 65537, 1024 * 1024):
            for scenario in ("same-object", "fresh-hit", "miss", "collision", "late-collision",
                             *(("saturated-bucket",) if size > memo.LARGE_INPUT else ())):
                measure(reference_fingerprint, kind, size, scenario)
                measure(memo.fingerprint, kind, size, scenario)
                pairs = []
                for index in range(9):
                    ordered = (("reference", reference_fingerprint), ("candidate", memo.fingerprint))
                    if index % 2:
                        ordered = ordered[::-1]
                    pair = {name: measure(function, kind, size, scenario) for name, function in ordered}
                    pairs.append(pair)
                rows.append({"type": kind.__name__, "size": size, "scenario": scenario,
                             "pairs": pairs,
                             "median_cpu_delta": statistics.median(
                                 pair["candidate"]["cpu"] - pair["reference"]["cpu"] for pair in pairs)})
    return {"status": "DIAGNOSTIC_NOT_REQUEST_GAIN", "warmup_per_mode": 1,
            "pairs_per_scenario": 9, "rows": rows}
