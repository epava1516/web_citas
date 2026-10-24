"""Attribute legacy collection hydration on current romantic pages before changing it."""

import hashlib
import json
import os
import statistics
import time

import pytest
from django.db import connection
from django.db.models import query as query_module
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation, publication_state
from apps.listings.models import PublicationDirty, Rate, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_current_romantic_page_legacy_prefetch_attribution(request, settings, monkeypatch, record_property):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id and connection.vendor == "postgresql" and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue("directory")
    populate(1000)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    assert Revision.services.through.objects.count() == Revision.travel_areas.through.objects.count() == Rate.objects.count() == 0
    expected_legacy = {"services", "travel_areas", "rates"}
    observations = []

    def read(path):
        response = client.get(path)
        assert response.status_code == 200 and response["Cache-Control"] == "no-store"
        assert response.wsgi_request._publication_route["route"] == "state"
        page = response.context["page"]
        assert len(page.object_list) == 24 and page.paginator.count == 1000
        return (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                tuple(str(row.pk) for row in page.object_list),
                tuple(card["sponsorship"] for card in response.context["cards"]))

    for route, path in (("directory_es", "/es/"), ("search_en", "/en/?q=synthetic")):
        expected = read(path)
        controls = []
        for _ in range(5):
            started, cpu = time.perf_counter(), time.thread_time()
            signature = read(path)
            controls.append({"wall": time.perf_counter() - started, "app_cpu": time.thread_time() - cpu})
            assert signature == expected
        observed = []
        for _ in range(3):
            state = {"contexts": [], "legacy": [], "active_context": False, "active_legacy": None,
                     "sql_calls": 0, "legacy_sql_calls": 0}
            original_init = public_validation.PublicationContext.__init__
            original_prefetch = query_module.prefetch_one_level

            def context_init(self, *args, **kwargs):
                assert not state["active_context"]
                state["active_context"] = True
                started, cpu = time.perf_counter(), time.thread_time()
                try:
                    original_init(self, *args, **kwargs)
                    state["contexts"].append({"rows": len(self.rows), "wall": time.perf_counter() - started,
                                              "app_cpu": time.thread_time() - cpu})
                finally:
                    state["active_context"] = False

            def prefetch(instances, prefetcher, lookup, level):
                parts = lookup.prefetch_to.split("__")
                target = parts[level] if level == len(parts) - 1 else None
                if not state["active_context"] or target not in expected_legacy:
                    return original_prefetch(instances, prefetcher, lookup, level)
                assert state["active_legacy"] is None  # Disjoint phases; never sum nested timings.
                state["active_legacy"] = target
                started, cpu = time.perf_counter(), time.thread_time()
                try:
                    result = original_prefetch(instances, prefetcher, lookup, level)
                    state["legacy"].append({"relation": target, "parent_instances": len(instances),
                                            "related_rows": len(result[0]), "wall": time.perf_counter() - started,
                                            "app_cpu": time.thread_time() - cpu})
                    return result
                finally:
                    state["active_legacy"] = None

            def sql(execute, statement, params, many, context):
                state["sql_calls"] += 1
                state["legacy_sql_calls"] += state["active_legacy"] is not None
                return execute(statement, params, many, context)

            with monkeypatch.context() as patch, connection.execute_wrapper(sql):
                patch.setattr(public_validation.PublicationContext, "__init__", context_init)
                patch.setattr(query_module, "prefetch_one_level", prefetch)
                started, cpu = time.perf_counter(), time.thread_time()
                signature = read(path)
                wall, app_cpu = time.perf_counter() - started, time.thread_time() - cpu
            assert signature == expected
            assert len(state["contexts"]) == 1 and state["contexts"][0]["rows"] == 24
            assert len(state["legacy"]) == 3 and {x["relation"] for x in state["legacy"]} == expected_legacy
            assert all(x["parent_instances"] == 24 and x["related_rows"] == 0 for x in state["legacy"])
            assert state["legacy_sql_calls"] == 3
            observed.append({"wall": wall, "app_cpu": app_cpu,
                             "legacy_share_of_observed_http": sum(x["wall"] for x in state["legacy"]) / wall,
                             "context": state["contexts"][0], "legacy": state["legacy"],
                             "sql_calls": state["sql_calls"], "legacy_sql_calls": state["legacy_sql_calls"]})
        assert read(path) == expected
        observations.append({"route": route, "controls": controls, "observed": observed,
                             "legacy_observed_share_median": statistics.median(x["legacy_share_of_observed_http"] for x in observed)})
    assert not PublicationDirty.objects.exists()
    eligible_to_prototype = all(row["legacy_observed_share_median"] >= 0.10 for row in observations)
    result = {"run_id": run_id, "result": "ATTRIBUTION_COMPLETE_NOT_ROI", "profiles": 1000,
              "rights": 0, "http_reads": 20, "routes": observations,
              "prototype_cost_gate": eligible_to_prototype,
              "limits": ["Current product; no replacement implementation or causal speedup measured",
                         "Five unobserved controls and three observed reads per route; same signatures",
                         "Legacy phase wall includes ORM/driver/fetch; no backend CPU inferred",
                         "Three disjoint inclusive prefetch phases; overhead not independently quantified",
                         "1000 profiles and zero entitlements; not promotional20percent/TCP/Internet capacity",
                         "Gate10percent observed share only decides whether this hypothesis has enough local cost evidence",
                         "No application adoption or SLO acceptance from PASS"]}
    output = settings.BASE_DIR / "artifacts/local-ci" / run_id / "beta-legacy-relation-cost.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    record_property("legacy_relation_cost_prototype_gate", eligible_to_prototype)
    record_property("legacy_relation_cost_artifact_sha256", hashlib.sha256(output.read_bytes()).hexdigest())
