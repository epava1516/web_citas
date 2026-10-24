"""Finite A/A/C comparison; candidate only, never a TCP capacity acceptance."""

import gc
import hashlib
import itertools
import json
import os
import statistics
import subprocess
import time
import tracemalloc
from pathlib import Path

import pytest
from beta_promotion_label_projection_diagnostic import label_projection_candidate
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog import promotion_paging
from apps.listings import publication_state
from apps.listings.models import PublicationDirty
from scripts.benchmark_owned_backend_cpu import backend_snapshot, owned_backend

pytestmark = pytest.mark.django_db(transaction=True)


def test_label_projection_balanced_roi(request, settings, monkeypatch, record_property):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id and connection.vendor == "postgresql" and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR
    gc_policy = (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    assert gc_policy[0] and gc_policy[2] == 0
    folder = settings.BASE_DIR / "artifacts/local-ci" / run_id
    runner = json.loads((folder / "runner.json").read_text())
    container = os.environ["LOCAL_CI_POSTGRES_CONTAINER"]
    assert container == "web-modelos-ci-pg-" + run_id
    inspection = json.loads(subprocess.check_output(["docker", "inspect", container], text=True))[0]
    settings.PROMOTION_TEST_MODE = True
    proposed, proposed_page, source_sha, candidate_sha = label_projection_candidate()
    prior = json.loads((settings.BASE_DIR / "docs/evidencias/beta-label-projection-terminal-audit-20261020.json").read_text())
    assert prior["passed"] == 10 and prior["candidate_sha256"] == candidate_sha
    dataset = prepare_promotional_load(request, 10000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    original = promotion_paging._snapshot_order_population
    original_page = publication_state._state_page
    chosen = {"arm": "A"}

    def dispatch_ranking(*args, **kwargs):
        function = proposed if chosen["arm"] == "C" else original
        return function(*args, **kwargs)

    def dispatch_page(*args, **kwargs):
        function = proposed_page if chosen["arm"] == "C" else original_page
        return function(*args, **kwargs)

    monkeypatch.setattr(promotion_paging, "_snapshot_order_population", dispatch_ranking)
    monkeypatch.setattr(publication_state, "_state_page", dispatch_page)
    client = request.getfixturevalue("directory")

    def read(path):
        response = client.get(path)
        assert response.status_code == 200 and response["Cache-Control"] == "no-store"
        assert response.wsgi_request._publication_route["route"] == "state"
        page = response.context["page"]
        return (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                tuple(str(row.pk) for row in page.object_list),
                tuple(card["sponsorship"] for card in response.context["cards"]))

    records = []
    signatures = {}
    for route, path in [("directory_es", "/es/"), ("search_en", "/en/?q=synthetic")]:
        for block, order in enumerate(itertools.permutations("ABC")):
            for arm in order:
                chosen["arm"] = arm
                connection.close()
                signature = read(path)  # One warm read per newly opened backend, outside controls.
                signatures.setdefault(route, signature)
                assert signature == signatures[route] and len(signature[2]) == 24 and any(signature[3])
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid(), current_setting('cursor_tuple_fraction')")
                    sql_pid, cursor_fraction = cursor.fetchone()
                identity = owned_backend(runner, inspection, sql_pid)

                def snapshot():
                    state = backend_snapshot(identity)
                    sched = list(map(int, Path(f"/proc/{identity['pid']}/schedstat").read_text().split()))
                    assert len(sched) == 3 and sched[0] > 0
                    return state | {"runtime_ns": sched[0], "wait_ns": sched[1]}

                before = snapshot()
                samples = []
                for _ in range(3):
                    started, cpu = time.perf_counter(), time.thread_time()
                    current = read(path)
                    samples.append({"wall_seconds": time.perf_counter() - started,
                                    "thread_cpu_seconds": time.thread_time() - cpu})
                    assert current == signature
                after = snapshot()
                assert after["runtime_ns"] >= before["runtime_ns"]
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_backend_pid(), current_setting('cursor_tuple_fraction')")
                    assert cursor.fetchone() == (sql_pid, cursor_fraction)
                assert not PublicationDirty.objects.exists()
                records.append({"route": route, "block": block, "order": "".join(order), "arm": arm,
                                "samples": samples, "backend_cpu_seconds": (
                                    after["runtime_ns"] - before["runtime_ns"]) / 1e9,
                                "backend_wait_seconds": (after["wait_ns"] - before["wait_ns"]) / 1e9,
                                "cursor_tuple_fraction": cursor_fraction,
                                "backend_identity": identity, "before": before, "after": after})
    observations = []
    for route, path in [("directory_es", "/es/"), ("search_en", "/en/?q=synthetic")]:
        for arm in "AC":
            from psycopg.types.json import Jsonb

            chosen["arm"] = arm
            observation = {"route": route, "arm": arm, "sql_execute_calls": 0,
                           "sql_driver_execute_seconds": 0.0, "jsonb_map_parameters": 0,
                           "jsonb_parameter_bytes": 0}

            def execute(query_execute, sql, params, many, context):
                maps = [p for p in (params or ()) if isinstance(p, Jsonb)]
                observation["jsonb_map_parameters"] += len(maps)
                observation["jsonb_parameter_bytes"] += sum(
                    len(json.dumps(p.obj, separators=(",", ":")).encode()) for p in maps
                )
                started = time.perf_counter()
                try:
                    return query_execute(sql, params, many, context)
                finally:
                    observation["sql_execute_calls"] += 1
                    observation["sql_driver_execute_seconds"] += time.perf_counter() - started

            assert not tracemalloc.is_tracing()
            with connection.execute_wrapper(execute):
                assert read(path) == signatures[route]
            # Heap uses a different read: observer json.dumps allocations must
            # not enter the traced application/driver peak.
            try:
                tracemalloc.start()
                assert read(path) == signatures[route]
                retained, peak = tracemalloc.get_traced_memory()
                observation["full_request_python_retained_bytes"] = retained
                observation["full_request_python_peak_bytes"] = peak
            finally:
                tracemalloc.stop()
            observations.append(observation)
        before, after = observations[-2:]
        assert before["arm"] == "A" and after["arm"] == "C"
        assert before["jsonb_map_parameters"] > after["jsonb_map_parameters"] > 0
        assert before["jsonb_parameter_bytes"] > after["jsonb_parameter_bytes"] > 0
    comparisons = {}
    for route in signatures:
        selected = [row for row in records if row["route"] == route]
        metrics = {}
        for arm in "ABC":
            rows = [r for r in selected if r["arm"] == arm]
            metrics[arm] = {"wall": statistics.median(s["wall_seconds"] for r in rows for s in r["samples"]),
                            "app_cpu": statistics.median(s["thread_cpu_seconds"] for r in rows for s in r["samples"]),
                            "pg_cpu_per_read": sum(r["backend_cpu_seconds"] for r in rows) / 18}
        stable = all(abs(metrics["A"][key] / metrics["B"][key] - 1) <= 0.10 for key in metrics["A"])
        reference = {key: (metrics["A"][key] + metrics["B"][key]) / 2 for key in metrics["A"]}
        ratios = {key: metrics["C"][key] / value for key, value in reference.items()}
        nonregressing = 0
        for block in range(6):
            group = {r["arm"]: statistics.median(s["wall_seconds"] for s in r["samples"])
                     for r in selected if r["block"] == block}
            nonregressing += group["C"] <= (group["A"] + group["B"]) / 2
        comparisons[route] = {"metrics": metrics, "ratios_C_to_AB": ratios, "AA_stable": stable,
                              "nonregressing_blocks": nonregressing,
                              "eligible": stable and ratios["wall"] <= 0.90
                              and ratios["app_cpu"] <= 1.05 and ratios["pg_cpu_per_read"] <= 1.05
                              and nonregressing >= 4}
    assert len(records) == 36 and sum(len(r["samples"]) for r in records) == 108
    assert gc_policy == (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    result = {"run_id": run_id, "result": "EXPERIMENT_COMPLETE", "count": dataset["published"],
              "rights": dataset["promotions"]["count"], "source_sha256": source_sha,
              "candidate_sha256": candidate_sha, "records": records, "comparisons": comparisons,
              "gc_policy_unchanged": gc_policy,
              "separate_full_request_observations": observations,
              "eligible": all(c["eligible"] for c in comparisons.values()),
              "requests": 152, "warm_reads": 36, "measured_reads": 108, "observed_reads": 8, "sql_observed_reads": 4, "heap_observed_reads": 4,
              "limits": ["Only experimental label projection changes; original rights filter/iterator/UUID unchanged",
                         "Same authority, population, ordering and native page guard; exact bytes/IDs/count/labels",
                         "A/B identical; six balanced permutations, new owned backend and one warm read per arm",
                         "App thread CPU and identified PG backend schedstat outside control boundaries",
                         "No profiler/SQL wrapper inside controls, normal GC, host shared",
                         "Eight separate reads measure SQL parameter volume and full-request heap independently",
                         "Python heap is not service RSS; execute excludes FETCH; serialized bytes are not TCP traffic",
                         "Single sequential local experiment, not TCP/SLO or whole-service memory acceptance",
                         "PASS pytest means experiment integrity; eligible false rejects adoption",
                         "Eligible true still requires memory review, affected regression and clean TCP before capacity"]}
    (folder / "beta-label-projection-roi.json").write_text(json.dumps(result, indent=2) + "\n")
    record_property("beta_label_projection_eligible", result["eligible"])
    record_property("beta_label_projection_comparisons", json.dumps(comparisons))
