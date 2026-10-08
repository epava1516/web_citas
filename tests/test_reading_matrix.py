"""Opt-in common source matrix: controls first, equivalent direct observers after."""

import json
import os
import statistics
import time

import pytest
from django.db import connection
from django.db.models.signals import post_init
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha, targets
from test_projection_http_jit_context import stats_snapshot

from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from apps.listings.presentation_reads import PagePresentation
from apps.listings.sql_publication import (
    CapturedSQLRead,
    SQLPublication,
    read_ordered_scalar_population,
)
from scripts.benchmark_call_profile import CallProfile
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        not os.getenv("READING_MATRIX_OUTPUT"), reason="Explicit common source matrix only"
    ),
]


@pytest.mark.parametrize(
    "count,variant",
    [(100, "contractual"), (1000, "contractual"), (10000, "contractual"), (10000, "diverse")],
)
def test_common_reading_matrix(request, monkeypatch, record_property, count, variant):
    client = request.getfixturevalue("directory")
    populate(count)
    if variant == "diverse":
        rows = list(Revision.objects.filter(status="approved").order_by("pk"))
        for index, row in enumerate(rows):
            suffix = alpha(index)
            row.description += " " + suffix
            if row.description_alternative:
                row.description_alternative += " " + suffix
            row.telegram = "bench" + suffix
        Revision.objects.bulk_update(
            rows, ["description", "description_alternative", "telegram"], batch_size=250
        )
    assert connection.vendor == "postgresql" and projection.supported()
    digest = projection.definitions_digest()
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names():
            cursor.execute("ANALYZE " + connection.ops.quote_name(table))
    expected = None
    page_ids = None

    def equivalent(response, mode):
        nonlocal expected, page_ids
        assert response.status_code == 200 and response.context["page"].paginator.count == count
        actual = [str(row.pk) for row in response.context["page"]]
        if expected is None:
            expected = response.content
            page_ids = actual
        assert response.content == expected and actual == page_ids
        route = response.wsgi_request._publication_route
        assert route["route"] == ("projection" if mode == "projected" else "fallback")
        if mode == "projected":
            assert route["candidate_stats"]["positive"] == count
            assert route["candidate_stats"]["native_fallback"] == 0
        return route

    def control(mode):
        with monkeypatch.context() as patch:
            if mode == "native":
                patch.setattr(projection, "supported", lambda **kwargs: False)
            start = time.perf_counter()
            response = client.get("/es/")
            seconds = time.perf_counter() - start
            route = equivalent(response, mode)
        return {"mode": mode, "seconds": seconds, "route": route}

    warm = [control(mode) for mode in ["native", "projected"]]
    before = stats_snapshot()
    controls = []
    for pair, order in enumerate([["native", "projected"], ["projected", "native"]] * 2):
        for mode in order:
            controls.append({"pair": pair, **control(mode)})
    after_controls = stats_snapshot()
    functions = targets() + [read_ordered_scalar_population, CapturedSQLRead.__iter__]
    for cls in [SQLPublication, PagePresentation]:
        for name in [
            "__init__",
            "visible_ids",
            "visible_keys",
            "scalar_page",
            "page",
            "photo",
            "describe",
            "captured_revision",
        ]:
            function = getattr(cls, name, None)
            if callable(function) and hasattr(function, "__code__"):
                functions.append(function)
    reports = []
    for mode in ["native", "projected"]:
        patterns = {}
        cache = {}

        def sql_timer(execute, sql, params, many, context):
            if sql not in cache:
                cache[sql] = query_pattern(sql)
            bucket = patterns.setdefault(cache[sql], {"calls": 0, "total_time": 0.0})
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                bucket["calls"] += 1
                bucket["total_time"] += time.perf_counter() - start

        profile = CallProfile(functions)
        with monkeypatch.context() as patch:
            if mode == "native":
                patch.setattr(projection, "supported", lambda **kwargs: False)
            post_init.connect(profile.objects, weak=False)
            try:
                start = time.perf_counter()
                with profile, connection.execute_wrapper(sql_timer):
                    measured = client.get("/es/")
                elapsed = time.perf_counter() - start
            finally:
                post_init.disconnect(profile.objects)
            route = equivalent(measured, mode)
        plain = statistics.median(s["seconds"] for s in controls if s["mode"] == mode)
        reports.append(
            {
                "mode": mode,
                "count": count,
                "variant": variant,
                "control_median_seconds": plain,
                "request_seconds": elapsed,
                "observed_minus_control_median_seconds": elapsed - plain,
                "route": route,
                "presentation": measured.wsgi_request._presentation_reads,
                "queries": sum(b["calls"] for b in patterns.values()),
                "sql_execute_seconds": sum(b["total_time"] for b in patterns.values()),
                "objects": dict(profile.materialized),
                "objects_provenance": dict(profile.provenance),
                "rules": profile.report(),
                "dominant_sql": [
                    {"query_pattern": p, **b, "mean_time": b["total_time"] / b["calls"]}
                    for p, b in sorted(
                        patterns.items(), key=lambda item: item[1]["total_time"], reverse=True
                    )
                ],
            }
        )
    assert projection.definitions_digest() == digest and projection.supported()
    after = stats_snapshot()
    record_property(
        "common_matrix",
        json.dumps(
            {
                "count": count,
                "variant": variant,
                "warm": warm,
                "controls": controls,
                "observations": reports,
                "stats_before": before,
                "stats_after_controls": after_controls,
                "stats_after_observers": after,
                "statistics_endpoints_equal": before == after_controls == after,
                "definition_digest": digest,
                "plan_reuse": "Main/top5 plans from scalar effect and two new presentation plans from TCP effect; no change in SQL between those and this common matrix, no extra plans between controls.",
                "scope": "DjangoClient end-to-end including render but not TCP/fixtures. One warm request per mode,4AB/BAcontrol pairs, no profiler, then same sys.setprofile/post_init/SQL observer BOTH modes. No model construction equals rows returned/scanned. Execute spans driver/DB/waits/buffering and excludes fetch. Inclusive validation/materialization/lazy/render/SQL overlap; direct nearest observed child discounted once, recursion inclusive not summed. Generator events are resumptions, not object counts. Observer-minus-control is descriptive overhead, not causal cost/saving. CPU values only observer thread; no DB CPU attribution. Controls count/body/orderedpage and routes equivalent; full population/page/revocation oracle tests reused. No SLO gate from150–200ms design guidance.",
                "not_measured": [
                    "SQLrows_returned except explicit scalar fetch count in route; SQLrows_affected/scanned",
                    "PGCPU/RSS/waits/locks/IO",
                    "p95exclusive",
                    "causaloverhead",
                    "concurrentcapacity",
                    "uploads",
                ],
            }
        ),
    )
