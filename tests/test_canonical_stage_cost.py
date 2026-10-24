"""Current canonical encoder stage only; never a repeat of the MOD08 delivery gate."""

import hashlib
import json
import resource
import time
import tracemalloc

import pytest

from apps.safety.canonical_kernel_loader import validated_kernel
from apps.safety.fast_canonical import CANONICAL_SCHEMA
from apps.safety.rights_exports import canonical


@pytest.mark.parametrize("rows", [100, 1500])
def test_current_structured_canonical_stage(request, record_property, rows):
    if not any(str(arg).split("::")[0] == "tests/test_canonical_stage_cost.py" for arg in request.config.args):
        pytest.skip("Explicit structured canonical-stage diagnostic only")
    description = ("Synthetic retained historical description. " * 150)[:5400]
    assert len(description) <= 6000
    value = {"schema": "synthetic-canonical-stage-v1", "revisions": [
        {"id": f"synthetic-{i}", "title": f"Synthetic revision {i} á e\u0301",
         "description": description, "description_alternative": description,
         "languages": ["es", "en"], "available": False, "extra": None}
        for i in range(rows)
    ]}
    reference = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    kernel_available = validated_kernel() is not None
    tracemalloc.start()
    started, cpu_started = time.perf_counter(), time.thread_time()
    try:
        encoded = canonical(value)
        elapsed, cpu = time.perf_counter() - started, time.thread_time() - cpu_started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert encoded == reference and json.loads(encoded) == value
    body = encoded.encode()
    assert len(body) < 17 * 1024 * 1024
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss < 1024 * 1024
    record_property("canonical_stage_diagnostic", dict(
        rows=rows, ordinary_field_length=len(description), document_bytes=len(body),
        document_sha256=hashlib.sha256(body).hexdigest(), canonical_schema=CANONICAL_SCHEMA,
        validated_kernel_available=kernel_available, elapsed_seconds=elapsed,
        python_thread_cpu_seconds=cpu, operation_python_peak_bytes=peak, process_maxrss_kib=rss,
        limits="One isolated active-encoder call, warmed reference; not source_copy, generation, encryption, coverage, package delivery, full request, p95 or MOD09 reassessment",
    ))
