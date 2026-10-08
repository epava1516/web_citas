"""Code-local stage observation after common matrix and valid short FAIL."""

import json
import os
import statistics
import time
from contextlib import nullcontext
from pathlib import Path

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_projection_cost_cycle import alpha
from test_projection_http_jit_context import stats_snapshot

from apps.listings import discovery, moderation
from apps.listings import projected_publication as projection
from apps.listings.models import Revision
from apps.listings.presentation_reads import PagePresentation
from apps.listings.public_validation import PublicationContext
from apps.listings.sql_publication import SQLPublication, read_ordered_scalar_population
from scripts.benchmark_local_monitor import LocalCallMonitor
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        not os.getenv("READING_STAGE_OUTPUT"),
        reason="Explicit isolated code-local attribution only",
    ),
]


@pytest.mark.parametrize("variant", ["contractual", "diverse"])
def test_reading_code_local_stages(request, record_property, variant):
    client = request.getfixturevalue("directory")
    populate(10000)
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
    functions = [
        projection.definitions_digest,
        projection.projected_page,
        SQLPublication.__init__,
        read_ordered_scalar_population,
        SQLPublication.visible_keys,
        PublicationContext.__init__,
        moderation.validate_submission,
        discovery.render,
        PagePresentation.__init__,
    ]
    bodies = {}
    routes = {}
    samples = []
    cache = {}
    families = [("listing-es", "/es/"), ("search-en", "/en/?q=synthetic")]

    def fetch(family, path, mode):
        profile = LocalCallMonitor(functions)
        patterns = {}

        def sql_timer(execute, sql, params, many, context):
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                elapsed = time.perf_counter() - start
                if sql not in cache:
                    cache[sql] = query_pattern(sql)
                b = patterns.setdefault(cache[sql], {"calls": 0, "total_time": 0.0})
                b["calls"] += 1
                b["total_time"] += elapsed

        assert projection.supported() and projection.definitions_digest() == digest
        with profile if mode == "observed" else nullcontext():
            with connection.execute_wrapper(sql_timer) if mode == "observed" else nullcontext():
                start = time.perf_counter()
                response = client.get(path)
                elapsed = time.perf_counter() - start
        assert response.status_code == 200 and response.context["page"].paginator.count == 10000
        bodies.setdefault(family, response.content)
        route = response.wsgi_request._publication_route
        routes.setdefault(family, route)
        assert response.content == bodies[family] and route == routes[family]
        assert route["route"] == "projection" and route["candidate_stats"]["native_fallback"] == 0
        assert projection.supported() and projection.definitions_digest() == digest
        rules = profile.report()
        if mode == "observed":
            counts = {r["rule"]: r["calls"] for r in rules}
            assert counts["apps.listings.projected_publication.definitions_digest"] == 2
            assert counts["apps.listings.submissions.validate_submission"] == 24
        return {
            "family": family,
            "mode": mode,
            "request_seconds": elapsed,
            "rules": rules,
            "queries": sum(v["calls"] for v in patterns.values())
            if mode == "observed"
            else "not_measured",
            "sql_execute_seconds": sum(v["total_time"] for v in patterns.values())
            if mode == "observed"
            else "not_measured",
            "dominant_sql": [
                {"query_pattern": p, **v, "mean_time": v["total_time"] / v["calls"]}
                for p, v in sorted(
                    patterns.items(), key=lambda item: item[1]["total_time"], reverse=True
                )
            ],
        }

    warm = [fetch(f, path, m) for f, path in families for m in ["plain", "observed"]]
    before = stats_snapshot()
    output = Path(os.environ["READING_STAGE_OUTPUT"], variant + ".json")
    for pair, order in enumerate([["plain", "observed"], ["observed", "plain"]] * 4):
        for family, path in families:
            for mode in order:
                samples.append({"pair": pair, **fetch(family, path, mode)})
        output.write_text(
            json.dumps({"stage": "controls", "variant": variant, "samples": samples}, indent=2)
            + "\n"
        )
    after = stats_snapshot()
    medians = {
        f: {
            m: statistics.median(
                s["request_seconds"] for s in samples if s["family"] == f and s["mode"] == m
            )
            for m in ["plain", "observed"]
        }
        for f, _ in families
    }
    deltas = [
        statistics.mean(
            next(
                s["request_seconds"]
                for s in samples
                if s["pair"] == p and s["family"] == f and s["mode"] == "observed"
            )
            - next(
                s["request_seconds"]
                for s in samples
                if s["pair"] == p and s["family"] == f and s["mode"] == "plain"
            )
            for f, _ in families
        )
        for p in range(8)
    ]
    baseline = statistics.mean(v["plain"] for v in medians.values())
    compatible = abs(statistics.median(deltas)) <= max(0.025, 0.05 * baseline) and all(
        abs(v["observed"] - v["plain"]) <= max(0.04, 0.10 * v["plain"]) for v in medians.values()
    )
    report = {
        "stage": "complete",
        "variant": variant,
        "samples": samples,
        "warm": warm,
        "medians": medians,
        "paired_observed_minus_plain_mean_family_deltas": deltas,
        "numerical_compatibility": compatible,
        "stats_before": before,
        "stats_after": after,
        "statistics_endpoints_equal": before == after,
        "definition_digest": digest,
        "routes": routes,
        "scope": "DjangoClient full request, no TCP/capacity;8AB/BApairs×listingES/searchEN bothfixtures, no profiler in plaincontrols. sys.monitoring per-code start/return of9ordinaryfunctions plus globalexceptionunwind filtered to those; no callable replacement or cached rules. SQLexecute wrapper observedonly, normalization outside execute timer but inside request/stages. Direct24nativevalidation calls; nested/lazy/SQL overlap, nearest observed child deducted once. ThreadCPU only observing requestthread, not PG. Compatibility numeric threshold predeclared, not causal overhead; missing fine per-rule/modelcounts reuse separate commonmatrix, not imputed here.",
        "not_measured": [
            "TCPcapacity",
            "SQLrowsaffected/scanned",
            "modelconstructions in this coarse probe",
            "fineformrules in this probe",
            "PGCPU/RSS/waits/locks/IO",
            "causaloverhead",
            "p95exclusive",
        ],
    }
    output.write_text(json.dumps(report, indent=2) + "\n")
    record_property("local_stages", json.dumps(report))
