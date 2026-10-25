"""Fixed grouped timing contrast; previous inconclusive results stay preserved."""

import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import pytest
from django.db import connection
from test_held_seal_image_batch import (
    BASELINE_SHA256,
    _assert_locks_held,
    _audit_counts,
    _baseline_guard,
    _generated_two,
)
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_validation_seal import check

from apps.safety import rights_exports, rights_portability_export

pytestmark = pytest.mark.django_db(transaction=True)


def test_grouped_held_seal_guard_reference(
    request, settings, monkeypatch, record_property
):
    if not any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
               for arg in request.config.args):
        pytest.skip("Explicit paired held-seal diagnostic; not default functional coverage")
    assert not os.environ.get("PYTEST_XDIST_WORKER"), "Paired measurement requires serial execution"
    (case, author, export, _), expected = _generated_two(request, settings, monkeypatch)
    candidate = rights_portability_export._verify_current_images
    baseline = _baseline_guard()
    original_read = rights_exports._read_image_blob
    active = None

    def read(blob):
        content = original_read(blob)
        if active is not None:
            active.append((blob.pk, hashlib.sha256(content).hexdigest(), len(content)))
        return content

    monkeypatch.setattr(rights_exports, "_read_image_blob", read)
    expected_reads = [(blob_id, digest, size) for _, blob_id, digest, size in expected]
    manifest_digest = hashlib.sha256("".join(row[2] for row in expected).encode()).hexdigest()
    before = _audit_counts()
    samples = []
    for round_index in range(6):
        order = ("baseline", "candidate") if round_index % 2 == 0 else ("candidate", "baseline")
        for method in order:
            for repetition in range(10):
                observations = []
                implementation = baseline if method == "baseline" else candidate

                def guarded(current_export, person):
                    nonlocal active
                    assert current_export.pk == export.pk
                    lock_count = _assert_locks_held(expected)
                    counters = {"sql_queries": 0, "sql_execute_seconds": 0.0}

                    def observe(execute, sql, params, many, context):
                        assert sql.lstrip().upper().startswith("SELECT") and not many
                        counters["sql_queries"] += 1
                        started = time.perf_counter()
                        try:
                            return execute(sql, params, many, context)
                        finally:
                            counters["sql_execute_seconds"] += time.perf_counter() - started

                    active = []
                    with connection.execute_wrapper(observe):
                        started = time.perf_counter()
                        cpu_started = time.thread_time()
                        implementation(current_export, person)
                        cpu = time.thread_time() - cpu_started
                        wall = time.perf_counter() - started
                    reads = active
                    active = None
                    assert reads == expected_reads
                    assert counters["sql_queries"] == (7 if method == "baseline" else 4)
                    observations.append({"round": round_index, "repetition": repetition, "method": method,
                                         "phase": "first" if round_index == 0 else "warm",
                                         "django_debug": settings.DEBUG, "wall_seconds": wall,
                                         "thread_cpu_seconds": cpu, **counters,
                                         "reads": len(reads), "bytes": sum(row[2] for row in reads),
                                         "pre_guard_locks": lock_count,
                                         "manifest_digest": manifest_digest})

                with monkeypatch.context() as patch:
                    patch.setattr(rights_portability_export, "_verify_current_images", guarded)
                    assert check(case, author, export) is True
                assert len(observations) == 1  # No fallback/full validation or duplicate guard.
                samples.extend(observations)
    assert len(samples) == 120 and _audit_counts() == before
    groups = []
    for round_index in range(6):
        for method in ("baseline", "candidate"):
            selected = [sample for sample in samples
                        if sample["round"] == round_index and sample["method"] == method]
            assert len(selected) == 10 and {sample["repetition"] for sample in selected} == set(range(10))
            groups.append({"round": round_index, "method": method,
                           "phase": "first" if round_index == 0 else "warm", "count": 10,
                           "mean_guard_seconds": statistics.fmean(sample["wall_seconds"] for sample in selected),
                           "total_guard_seconds": sum(sample["wall_seconds"] for sample in selected),
                           "mean_cpu_seconds": statistics.fmean(sample["thread_cpu_seconds"] for sample in selected),
                           "mean_sql_execute_seconds": statistics.fmean(sample["sql_execute_seconds"] for sample in selected)})
    assert len(groups) == 12
    record_property("n02c_guard_samples", json.dumps(samples, sort_keys=True))
    record_property("n02c_guard_groups", json.dumps(groups, sort_keys=True))
    record_property("n02c_baseline_sha256", BASELINE_SHA256)
    record_property("n02c_scope", "Actual held-seal caller2smallimages;120freshnativechecktransactions/guards,12groups10calls alternating;firstgroupseparate. Everycall7/4SELECT,2fullreads/hash,4preexistingPGlocks.NoHTTP/fullsizeMOD09/p95acceptance. Allsamplespreserved;temporaldeclarationrequiresall5warmpairsgroupmeansbetter.")

