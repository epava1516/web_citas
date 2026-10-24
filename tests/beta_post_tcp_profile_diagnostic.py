"""Separate sequential attribution after the valid promotional TCP short failure."""

import cProfile
import json
import math
import os
import pstats
import time
from contextlib import ExitStack
from functools import wraps
from pathlib import Path

import pytest
from beta_promotion_plans_diagnostic import redact
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog import promotion_paging
from apps.listings import discovery, public_validation, publication_state
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def distribution(values):
    values = sorted(values)
    return {f"p{p}": values[math.ceil(len(values) * p / 100) - 1] for p in [50, 95, 99]}


def function_rows(profile, root, sort_index):
    rows = []
    for (filename, line, name), (primitive, total, own, cumulative, _) in pstats.Stats(profile).stats.items():
        path = Path(filename)
        source = str(path.relative_to(root)) if path.is_relative_to(root) else filename
        rows.append({"source": source, "line": line, "function": name,
                     "primitive_calls": primitive, "total_calls": total,
                     "self_seconds": own, "inclusive_seconds": cumulative})
    return sorted(rows, key=lambda row: row[sort_index], reverse=True)[:60]


@pytest.mark.parametrize("count", [1000, 10000])
def test_post_tcp_sequential_attribution(request, settings, monkeypatch, record_property, count):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id and connection.vendor == "postgresql" and not settings.PRODUCTION
    settings.PROMOTION_TEST_MODE = True
    assert not publication_state.READ_REPAIR
    dataset = prepare_promotional_load(request, count)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    client = request.getfixturevalue("directory")
    routes = [
        ("directory_es", "/es/"), ("directory_en", "/en/"),
        ("search_es", "/es/?q=photography"), ("search_en", "/en/?q=synthetic"),
        ("detail_es", "/es/listing/" + dataset["sample_ids"][0] + "/"),
        ("detail_en", "/en/listing/" + dataset["sample_ids"][-1] + "/"),
    ]

    def read(label, path):
        response = client.get(path)
        assert response.status_code == 200
        if label.startswith("detail"):
            return {"status": response.status_code, "surface": "native_detail"}
        page = response.context["page"]
        assert response.wsgi_request._publication_route["route"] == "state"
        ids = [str(row.pk) for row in page.object_list]
        sponsorship = [card["sponsorship"] for card in response.context["cards"]]
        assert ids and len(ids) == len(set(ids)) and any(sponsorship)
        if label.startswith("directory"):
            assert page.paginator.count == count
        return {"count": page.paginator.count, "ids": ids, "sponsorship": sponsorship}

    observations = []
    for label, path in routes:
        expected = read(label, path)
        controls, cpu = [], []
        for _ in range(5):
            start, process_start = time.perf_counter(), time.process_time()
            signature = read(label, path)
            controls.append(time.perf_counter() - start)
            cpu.append(time.process_time() - process_start)
            assert signature == expected
        queries, query_phases, stack = [], [], []

        def observe(owner, name, phase):
            original = getattr(owner, name)

            @wraps(original)
            def call(*args, **kwargs):
                stack.append(phase)
                try:
                    return original(*args, **kwargs)
                finally:
                    assert stack.pop() == phase

            return owner, name, call

        def sql_event(execute, sql, params, many, context):
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                queries.append(time.perf_counter() - start)
                query_phases.append(stack[-1] if stack else "other")

        with ExitStack() as scopes:
            patch = scopes.enter_context(monkeypatch.context())
            for owner, name, phase in [
                (publication_state, "_state_page", "state_membership_page_guard"),
                (promotion_paging, "_snapshot_order_population", "commercial_rights"),
                (public_validation.PublicationContext, "__init__", "publication_context"),
                (public_validation, "read_publication_values", "context_hydration"),
                (discovery.PagePresentation, "__init__", "presentation"),
                (discovery, "render", "render_search_form_and_cards"),
            ]:
                owner, name, call = observe(owner, name, phase)
                patch.setattr(owner, name, call)
            scopes.enter_context(connection.execute_wrapper(sql_event))
            assert read(label, path) == expected
        profile = cProfile.Profile()
        profile.enable()
        try:
            signature = read(label, path)
        finally:
            profile.disable()
        assert signature == expected
        observations.append({
            "route": label, "controls_wall_seconds": controls,
            "controls_process_cpu_seconds": cpu, "wall_descriptive": distribution(controls),
            "cpu_descriptive": distribution(cpu), "sql_driver_seconds": queries,
            "sql_innermost_phases": query_phases,
            "sql_calls": len(queries), "sql_driver_total_seconds": sum(queries),
            "profile_top_self": function_rows(profile, settings.BASE_DIR, "self_seconds"),
            "profile_top_inclusive": function_rows(profile, settings.BASE_DIR, "inclusive_seconds"),
            "signature_stable": True, "page_count": expected.get("count"),
        })
    plans = {}
    if count == 10000:
        for label, data in [("directory_es", {}), ("search_en", {"q": "synthetic"})]:
            form = discovery.SearchForm(data)
            assert form.is_valid()

            def capture_order(population, identifier, *, trusted_snapshot):
                assert trusted_snapshot
                captured = []

                def capture(execute, sql, params, many, context):
                    captured.append((sql, params))
                    return execute(sql, params, many, context)

                with connection.execute_wrapper(capture):
                    ordered = promotion_paging._snapshot_order_population(
                        population, identifier, text_search=bool(data.get("q")),
                    )
                assert len(captured) == 1
                with connection.cursor() as cursor:
                    cursor.execute("SHOW transaction_isolation")
                    assert cursor.fetchone()[0] == "repeatable read"
                    cursor.execute("SHOW transaction_read_only")
                    assert cursor.fetchone()[0] == "on"
                    sql, params = captured[0]
                    cursor.execute("EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) " + sql, params)
                    plan = cursor.fetchone()[0]
                    rights_plan = json.loads(plan) if isinstance(plan, str) else plan
                plans[label] = {"rights": rights_plan, "page": json.loads(
                    ordered.values_list(identifier, "_promotion_priority")[:24].explain(
                        analyze=True, buffers=True, timing=False, format="json",
                    ),
                )}
                return ordered

            page = publication_state.state_page(
                discovery.candidates(form.cleaned_data), 1, promotion_order=capture_order,
            )
            assert page and len(page.object_list) == 24 and page.sponsorship
    result = {
        "run_id": run_id, "result": "ATTRIBUTION_COMPLETE", "count": count,
        "rights": dataset["promotions"]["count"], "requests": len(routes) * 8,
        "observations": observations,
        "read_only_plans_after_controls": redact(plans),
        "limits": ["Sequential in-process, no TCP/concurrency/capacity acceptance",
                   "Five controls give descriptive percentiles; process CPU is pytest only",
                   "SQL observation and cProfile are separate requests, not clean controls",
                   "SQL phase labels are exclusive to innermost wrapper, no inclusive time sum",
                   "Optional warm plans execute after all controls, no HTTP or CPU attribution",
                   "Inclusive profile times overlap and include instrumentation/waits; do not add",
                   "No raw SQL, parameters, profile arguments or real-provider verification",
                   "Same synthetic generator/cohort as TCP; shared agency/photo/geography"],
    }
    folder = settings.BASE_DIR / "artifacts/local-ci" / run_id
    (folder / "beta-post-tcp-profile.json").write_text(json.dumps(result, indent=2) + "\n")
    record_property("beta_post_tcp_attribution", json.dumps(result))
