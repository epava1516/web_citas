"""Explicit stage measurements; no subtraction-based attribution of Python time."""

import hashlib
import os
import platform
import time
from collections import Counter

import pytest
from django.db import connection
from django.db.models import Model
from django.db.models import query as query_module
from django.db.models.query import ModelIterable
from django.db.models.signals import post_init
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, moderation, publication_state
from apps.listings.forms import ContactsForm
from apps.listings.public_validation import PublicationContext, SnapshotDetails
from scripts.query_pattern_redaction import query_pattern
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [100, 1000, 10000])
def test_discovery_cost_checkpoint(request, monkeypatch, record_property, count):
    client = request.getfixturevalue("directory")
    populate(count)
    assert connection.vendor == "postgresql"
    queries = 0
    patterns = {}
    normalization_cache = {}
    phase = "request_other"
    provenance = Counter()
    from_db_calls = Counter()
    from_db_seconds = Counter()
    iteration_seconds = Counter()
    iterator_roots = Counter()
    prefetch_seconds = Counter()
    prefetch_calls = Counter()
    sql_execute_seconds = 0.0
    objects = Counter()
    field_clean_stats = []
    form_events = {}

    def instrument_form_method(form_class, method):
        original = getattr(form_class, method)
        label = f"{form_class.__name__}.{method}"
        bucket = form_events.setdefault(label, {"calls": 0, "seconds": 0.0})

        def measured(self, *args, **kwargs):
            bucket["calls"] += 1
            start = time.perf_counter()
            try:
                return original(self, *args, **kwargs)
            finally:
                bucket["seconds"] += time.perf_counter() - start

        monkeypatch.setattr(form_class, method, measured)

    # Diagnostic subevents only: retain all native construction/cleaning behavior.
    # full_clean contains _clean_fields/_clean_form/_post_clean, not exclusive time.
    for form_class in [SnapshotDetails, ContactsForm]:
        for method in ["__init__", "full_clean", "_clean_fields", "_clean_form", "_post_clean"]:
            instrument_form_method(form_class, method)
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
        if sql not in normalization_cache:
            normalization_cache[sql] = query_pattern(sql)
        pattern = normalization_cache[sql]
        bucket = patterns.setdefault(
            pattern, {"calls": 0, "total_time": 0.0, "parameter_count_max": 0}
        )
        bucket["parameter_count_max"] = max(bucket["parameter_count_max"], len(params or []))
        start = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            duration = time.perf_counter() - start
            sql_execute_seconds += duration
            bucket["calls"] += 1
            bucket["total_time"] += duration

    def initialized(sender, **kwargs):
        if sender._meta.app_label in ["listings", "core", "catalog", "safety", "mediafiles"]:
            objects[sender._meta.label] += 1
            provenance[(phase, sender._meta.label)] += 1

    original_from_db = Model.from_db.__func__
    original_iterator = ModelIterable.__iter__
    original_prefetch = query_module.prefetch_one_level

    def from_db(cls, db, field_names, values):
        label = cls._meta.label
        start = time.perf_counter()
        try:
            return original_from_db(cls, db, field_names, values)
        finally:
            from_db_calls[label] += 1
            from_db_seconds[label] += time.perf_counter() - start

    def iterator(self):
        inner = original_iterator(self)
        label = self.queryset.model._meta.label
        while True:
            start = time.perf_counter()
            try:
                item = next(inner)
            except StopIteration:
                iteration_seconds[label] += time.perf_counter() - start
                return
            iteration_seconds[label] += time.perf_counter() - start
            iterator_roots[label] += 1
            yield item

    def prefetch(instances, prefetcher, lookup, level):
        relation = lookup.prefetch_to
        start = time.perf_counter()
        try:
            return original_prefetch(instances, prefetcher, lookup, level)
        finally:
            prefetch_calls[relation] += 1
            prefetch_seconds[relation] += time.perf_counter() - start

    monkeypatch.setattr(Model, "from_db", classmethod(from_db))
    monkeypatch.setattr(ModelIterable, "__iter__", iterator)
    monkeypatch.setattr(query_module, "prefetch_one_level", prefetch)

    original_init = PublicationContext.__init__
    original_validation = moderation.validate_submission
    original_render = discovery.render

    def context_init(self, query, **kwargs):
        nonlocal phase
        before = phase
        phase = "context"
        start = time.perf_counter()
        try:
            original_init(self, query, **kwargs)
            field_clean_stats.append(self.field_clean_cache_stats)
        finally:
            stages["context_seconds"] += time.perf_counter() - start
            phase = before
        stages["candidate_listings"] = len(self.rows)
        stages["relation_memberships"] = {
            name: sum(len(getattr(row.approved_revision, "_pv_" + name)) for row in self.rows)
            for name in ["categories", "services", "travel_areas", "rates", "photos"]
        }

    def validate(*args, **kwargs):
        nonlocal phase
        before = phase
        phase = "validation"
        start = time.perf_counter()
        stages["validation_calls"] += 1
        try:
            return original_validation(*args, **kwargs)
        finally:
            stages["validation_seconds"] += time.perf_counter() - start
            phase = before

    def render(*args, **kwargs):
        nonlocal phase
        before = phase
        phase = "render"
        start = time.perf_counter()
        try:
            return original_render(*args, **kwargs)
        finally:
            stages["render_seconds"] += time.perf_counter() - start
            phase = before

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
    record_property("form_events", form_events)
    record_property("field_clean_cache_stats", field_clean_stats)
    record_property("objects_by_phase_model", {f"{p}:{m}": n for (p, m), n in provenance.items()})
    record_property("from_db_calls_by_model", dict(from_db_calls))
    record_property("from_db_seconds_by_model", dict(from_db_seconds))
    record_property("orm_iteration_seconds_by_queryset_model", dict(iteration_seconds))
    record_property("queryset_root_objects_yielded", dict(iterator_roots))
    record_property(
        "prefetch_events_by_relation",
        {
            name: {"calls": prefetch_calls[name], "seconds": secs}
            for name, secs in prefetch_seconds.items()
        },
    )
    dominant = [
        {
            "query_pattern": pattern,
            "pattern_sha256": hashlib.sha256(pattern.encode()).hexdigest(),
            **data,
            "mean_time": data["total_time"] / data["calls"],
            "rows_returned": "not_measured",
            "rows_affected": "not_measured",
            "rows_scanned": "not_measured",
        }
        for pattern, data in patterns.items()
    ]
    dominant.sort(key=lambda item: item["total_time"], reverse=True)
    record_property("dominant_queries", dominant)
    record_property(
        "not_measured",
        [
            "rows_returned",
            "rows_affected",
            "rows_examined/rows_scanned",
            "DB CPU/waits/locks/IO",
            "RSS",
            "pure serialization separate from HTML render",
            "pure materialization CPU independent of nested SQL/fetch/conversion",
        ],
    )
    record_property(
        "normalization",
        "Strip comments; replace quoted/dollar SQL literals and numeric constants; collapse variable-length bind lists; collapse whitespace. Parameters never persisted. calls/total_time/mean_time all synchronous cursor.execute calls, seconds; patterns ordered by accumulated client execute time.",
    )
    record_property(
        "resources",
        {
            "python": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "postgres_shared_service": True,
            "request_topology": "Django Client single request/PG synthetic isolated",
            "cache_state": "fresh per-case seeded data, same process and shared PG/OS caches not reset;100 then1000 then10000; DummyCache",
        },
    )
    record_property(
        "limits",
        "End-to-end DjangoClient.get includes middleware/view/render; excludes fixtures/network/Gunicorn. cursor.execute includes driver/server IO/buffering and excludes later ORM iteration conversion/hydration. Model.from_db measures construction/state setup, includes post_init counter overhead; excludes SQL and earlier JSON conversion. ORM iteration intervals include lazy SQL/fetch/conversion/from_db; prefetch includes nested SQL/iteration and relation-cache mapping; context/validation/render include nested events. Timers overlap and cannot be summed as exclusive phases. Model instances/root objects/relation references are not SQL rows or distinct entities. Every dataset uses same instrumentation; no total-minus-SQL Python attribution. If SQL exceeds half of end-to-end in a dataset, run separate EXPLAIN ANALYZE BUFFERS on relevant isolated synthetic SELECTs; otherwise do not invent SQL dominance. No backend changes before reviewed checkpoint. Prior profiles lack these new metrics.",
    )
