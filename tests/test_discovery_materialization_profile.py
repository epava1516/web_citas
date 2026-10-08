"""Explicit stage measurements; no subtraction-based attribution of Python time."""

import time
from collections import Counter

import pytest
from django.db import connection
from django.db.models.signals import post_init
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, moderation, publication_state
from apps.listings.public_validation import PublicationContext
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [10, 100, 1000, 10000])
def test_discovery_materialization_and_explicit_stage_times(
    request, monkeypatch, record_property, count
):
    client = request.getfixturevalue("directory")
    populate(count)
    queries = 0
    sql_execute_seconds = 0.0
    objects = Counter()
    stages = {
        "context_seconds": 0.0,
        "validation_seconds": 0.0,
        "render_seconds": 0.0,
        "validation_calls": 0,
        "candidate_listings": 0,
        "relation_memberships": {},
    }

    def sql_timer(execute, sql, params, many, context):
        nonlocal queries, sql_execute_seconds
        queries += 1
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            sql_execute_seconds += time.perf_counter() - start

    def initialized(sender, **kwargs):
        if sender._meta.app_label in ["listings", "core", "catalog", "safety", "mediafiles"]:
            objects[sender._meta.label] += 1

    original_init = PublicationContext.__init__
    original_validation = moderation.validate_submission
    original_render = discovery.render

    def context_init(self, query, **kwargs):
        start = time.perf_counter()
        try:
            original_init(self, query, **kwargs)
        finally:
            stages["context_seconds"] += time.perf_counter() - start
        stages["candidate_listings"] = len(self.rows)
        stages["relation_memberships"] = {
            name: sum(len(getattr(row.approved_revision, "_pv_" + name)) for row in self.rows)
            for name in ["categories", "services", "travel_areas", "rates", "photos"]
        }

    def validate(*args, **kwargs):
        start = time.perf_counter()
        stages["validation_calls"] += 1
        try:
            return original_validation(*args, **kwargs)
        finally:
            stages["validation_seconds"] += time.perf_counter() - start

    def render(*args, **kwargs):
        start = time.perf_counter()
        try:
            return original_render(*args, **kwargs)
        finally:
            stages["render_seconds"] += time.perf_counter() - start

    monkeypatch.setattr(PublicationContext, "__init__", context_init)
    monkeypatch.setattr(moderation, "validate_submission", validate)
    monkeypatch.setattr(discovery, "render", render)
    # MOD-05: the listing is served from stored state; this profiles the native path.
    monkeypatch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
    post_init.connect(initialized, weak=False)
    start = time.perf_counter()
    try:
        with connection.execute_wrapper(sql_timer):
            response = client.get("/es/")
    finally:
        elapsed = time.perf_counter() - start
        post_init.disconnect(initialized)
    assert response.status_code == 200
    assert response.context["page"].paginator.count == count
    assert len(response.context["page"].object_list) == min(count, 24)
    assert response["Cache-Control"] == "no-store"
    record_property("dataset_published", count)
    record_property("queries", queries)
    record_property("sql_execute_seconds", sql_execute_seconds)
    record_property("total_seconds_instrumented", elapsed)
    record_property("objects_instantiated_by_model", dict(objects))
    record_property("explicit_stages", stages)
    record_property(
        "limits",
        "Real PG/Django Client; post_init signal and timing wrappers add overhead. SQL execute excludes fetch/materialization, validation and render include their nested SQL. Stage sums may overlap. Counts of constructed instances include repeated model instances; relation memberships are references, not distinct allocation counts. Same instrumentation required for future elapsed comparisons. Previous10/100 profiles did not measure these stages. Not TCP/capacity/CPU/request.",
    )
