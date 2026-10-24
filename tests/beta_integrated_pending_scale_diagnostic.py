"""Explicit integrated-stage scale diagnostic; historical fallback baseline unchanged."""

import cProfile
import gc
import hashlib
import json
import math
import os
import subprocess
import time
from collections import Counter
from pathlib import Path

import pytest
from beta_post_tcp_profile_diagnostic import distribution, function_rows
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, public_validation, publication_state
from apps.listings.models import PublicationDirty
from config.celery import app as celery_app
from scripts.benchmark_owned_backend_cpu import backend_snapshot, owned_backend

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [100, 1000, 10000])
def test_integrated_pending_scale_diagnostic(request, settings, monkeypatch, record_property, count):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id and connection.vendor == "postgresql" and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR and publication_state.NATIVE_UNKNOWN_LIMIT == 48
    assert publication_state.DIRTY_LIMIT == 1000
    assert not celery_app.conf.task_always_eager
    gc_policy = (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    assert gc_policy[0] and gc_policy[2] == 0
    root = settings.BASE_DIR
    source_sha = hashlib.sha256((root / "apps/listings/publication_state.py").read_bytes()).hexdigest()
    assert source_sha == "282f88e5af3c3f49f618aaf9bf3c5949e0d038f7699bfe6ca79ac880998703c6"
    folder = root / "artifacts/local-ci" / run_id
    runner = json.loads((folder / "runner.json").read_text())
    container = os.environ["LOCAL_CI_POSTGRES_CONTAINER"]
    inspection = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, count)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    started_day = timezone.now().date().isoformat()
    client = request.getfixturevalue("directory")
    requests = 0
    route_counts = Counter()

    def read(path, phase):
        nonlocal requests
        requests += 1
        response = client.get(path)
        assert response.status_code == 200 and response["Cache-Control"] == "no-store"
        route = response.wsgi_request._publication_route
        assert route["route"] == "state"
        assert route["reason"] == ("trusted_state" if phase == "fresh" else "trusted_state_extended_unknown")
        if phase == "unknown49":
            assert route["native_unknown"] == 49
        route_counts[(phase, route["route"], route.get("reason", ""))] += 1
        page = response.context["page"]
        return (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                tuple(str(row.pk) for row in page.object_list),
                tuple(card["sponsorship"] for card in response.context["cards"]))

    pages = math.ceil(count / 24)
    expected_pages = [read(f"/es/?page={page}", "fresh") for page in range(1, pages + 1)]
    expected_ids = [pk for signature in expected_pages for pk in signature[2]]
    assert len(expected_ids) == len(set(expected_ids)) == count
    assert all(signature[1] == count for signature in expected_pages)
    form = discovery.SearchForm({"q": "synthetic"})
    assert form.is_valid()
    marked = list(discovery.candidates(form.cleaned_data).values_list("pk", flat=True)[:49])
    assert len(marked) == 49
    middle = max(1, math.ceil(pages / 2))
    routes = [("directory_es", "/es/"), ("directory_en", "/en/"),
              ("search_en", "/en/?q=synthetic"), ("middle_es", f"/es/?page={middle}")]
    signatures, records, observations, unknown_pages = {}, [], [], []
    for phase in ["fresh", "unknown49"]:
        if phase == "unknown49":
            publication_state.mark(marked)
            assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) == set(marked)
            for page, expected in enumerate(expected_pages, 1):
                actual_page = read(f"/es/?page={page}", phase)
                unknown_pages.append(actual_page)
                assert actual_page == expected
        for route, path in routes:
            signature = read(path, phase)  # Warm read outside controls.
            signatures.setdefault(route, signature)
            assert signature == signatures[route]
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                sql_pid = cursor.fetchone()[0]
            identity = owned_backend(runner, inspection, sql_pid)

            def snapshot():
                state = backend_snapshot(identity)
                sched = list(map(int, Path(f"/proc/{identity['pid']}/schedstat").read_text().split()))
                return state | {"runtime_ns": sched[0]}

            before = snapshot()
            samples = []
            for _ in range(5):
                start, cpu = time.perf_counter(), time.thread_time()
                actual = read(path, phase)
                samples.append({"wall_seconds": time.perf_counter() - start,
                                "thread_cpu_seconds": time.thread_time() - cpu})
                samples[-1]["signature_sha256"] = hashlib.sha256(json.dumps(actual).encode()).hexdigest()
                assert actual == signature
            after = snapshot()
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                assert cursor.fetchone()[0] == sql_pid
            records.append({"phase": phase, "route": route, "signature": signature, "samples": samples,
                            "wall": distribution([s["wall_seconds"] for s in samples]),
                            "thread_cpu": distribution([s["thread_cpu_seconds"] for s in samples]),
                            "backend_identity": identity, "before": before, "after": after,
                            "backend_cpu_per_read_seconds": (after["runtime_ns"] - before["runtime_ns"]) / 5e9})
            sql_calls = []

            def execute(real_execute, sql, params, many, context):
                start = time.perf_counter()
                try:
                    return real_execute(sql, params, many, context)
                finally:
                    sql_calls.append(time.perf_counter() - start)

            with connection.execute_wrapper(execute):
                assert read(path, phase) == signature
            contexts = []
            original_init = public_validation.PublicationContext.__init__

            def context_init(context, *args, **kwargs):
                start = time.perf_counter()
                original_init(context, *args, **kwargs)
                contexts.append({"rows": len(context.rows), "inclusive_seconds": time.perf_counter() - start})

            profile = cProfile.Profile()
            with monkeypatch.context() as patch:
                patch.setattr(public_validation.PublicationContext, "__init__", context_init)
                profile.enable()
                try:
                    assert read(path, phase) == signature
                finally:
                    profile.disable()
            observations.append({"phase": phase, "route": route,
                                 "execute_calls": len(sql_calls), "execute_seconds": sum(sql_calls),
                                 "profiled_contexts": contexts,
                                 "self_functions": function_rows(profile, root, "self_seconds"),
                                 "inclusive_functions": function_rows(profile, root, "inclusive_seconds")})
            assert PublicationDirty.objects.count() == (0 if phase == "fresh" else 49)
    assert len(records) == len(observations) == 8 and requests == 64 + 2 * pages
    assert gc_policy == (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    assert timezone.now().date().isoformat() == started_day
    result = {"run_id": run_id, "result": "INTEGRATED_DIAGNOSTIC_COMPLETE", "source_sha256": source_sha, "count": count,
              "promotional_rights": dataset["promotions"]["count"], "dirty_still_public": 49,
              "read_repair": False, "unknown_limit": 48, "requests": requests,
              "all_pages": pages, "all_pages_exact_bytes_ids_count_labels": True,
              "fresh_page_signatures": expected_pages, "unknown_page_signatures": unknown_pages,
              "observed_routes": [{"phase": phase, "route": route, "reason": reason, "requests": n}
                                  for (phase, route, reason), n in sorted(route_counts.items())],
              "measured_reads": 40, "warm_reads": 8, "sql_observed_reads": 8,
              "profiled_reads": 8, "records": records, "observations": observations,
              "gc_policy_unchanged": gc_policy,
              "limits": ["Fresh then unknown49 fixed order; descriptive, not balanced optimization ROI",
                         "Five samples: p95/p99 are maxima, not tail/SLO estimation",
                         "In-process Client; not TCP/capacity, providers or production verification",
                         "Actual mark and exact integrated extended-state reason; no worker/read repair during controls",
                         "Execute timings exclude server cursor FETCH; no SQL/parameters retained",
                         "Contexts and cProfile only in eight observations, never controls; inclusive times overlap",
                         "App thread and one owned PG backend CPU, not whole service RSS/CPU",
                         "Synthetic shared agency/photo/geography, not national distribution",
                         "Integrated candidate source guard; no limit, authority, population or product edits during run; historical baseline remains separate"]}
    (folder / f"beta-integrated-pending-{count}.json").write_text(json.dumps(result, indent=2) + "\n")
    record_property("beta_integrated_pending_requests", requests)
