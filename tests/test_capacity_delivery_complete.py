"""Required target flow; opt-in only after own kernel limits are verified."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from capacity_delivery_flow import run_case
from capacity_gunicorn import server
from django.conf import settings as runtime_settings
from django.db import connections
from test_capacity_selection_tcp import prepare_target
from test_reports import directory, photo_environment  # noqa: F401

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(not getattr(runtime_settings, "CAPACITY_ENVIRONMENT_VERIFIED", False),
                      reason="Requires owned capacity runner with verified kernel limits"),
]


@pytest.mark.usefixtures("photo_environment")
def test_owned_complete_target_delivery(request, settings, monkeypatch, record_property):
    results, errors = [], []
    phase = "fixture_preparation"
    with server(settings, record_property) as endpoint:
        barrier = Barrier(2)
        try:
            contexts, targets = [{}, {}], []
            for index, identity in enumerate(["capacity-subject-a", "capacity-subject-b"]):
                target = prepare_target(request, settings, monkeypatch, endpoint, identity,
                    independent_reviewer=True, include_binary=True, details=contexts[index])
                targets.append(target)
                results.append({"fixture": target[5], "build_seconds": target[6],
                                "scalar_preparation_seconds": target[7], "success": False})
            assert targets[0][0].pk != targets[1][0].pk
            phase = "application_stages"

            def worker(index):
                try:
                    run_case(index, targets[index], contexts[index], endpoint, settings,
                             barrier, results[index])
                finally:
                    barrier.abort()
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(worker, index) for index in range(2)]
                for future in futures:
                    try:
                        future.result(timeout=8400)
                    except Exception as error:
                        errors.append(f"{type(error).__name__}: {error}")
        except Exception as error:
            errors.append(f"{type(error).__name__}: {error}")
        finally:
            peak = next(int(line.split()[1]) * 1024
                        for line in Path("/proc/self/status").read_text().splitlines()
                        if line.startswith("VmHWM:"))
            record_property("delivery_measurements", json.dumps({
                "cases": results, "errors": errors, "phase": phase,
                "process_peak_rss_bytes": peak,
                "scope": "Native synthetic1500/16MiB/64MiB cases; simulator identity/media fixture. Actual TCP/CSRF/page saves/reads/final decisions/downloads, whole bodies and hashes. Page-save p95 uses20fresh writes, final decisions timed individually; no replay substitution. Kernel runtime limits separately verified; no complete environment/production/N3 claim.",
            }))
        assert not errors, errors
        assert len(results) == 2 and all(row["success"] for row in results)
        assert peak <= 1024 ** 3
        for name in ["binary_page_save", "selection_page_read", "binary_inspection",
                     "coverage_page_save", "coverage_page_read", "json_download", "binary_download"]:
            first, second = [row[name + "_intervals"] for row in results]
            assert len(first) == len(second)
            assert all(max(a[0], b[0]) < min(a[1], b[1])
                       for a, b in zip(first, second, strict=True)), name
