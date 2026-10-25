"""Finite PostgreSQL aggregate baseline; service wall time is distinct from QA."""

import json
import time
from datetime import timedelta
from uuid import UUID

import pytest
from django.db import connection
from django.utils import timezone

from apps.core import operational_snapshot
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [0, 10, 100])
def test_snapshot_publication_backlog_baseline(count, monkeypatch, record_property):
    assert connection.vendor == "postgresql" and connection.get_autocommit()
    assert not PublicationDirty.objects.exists()
    now = timezone.now()
    monkeypatch.setattr(operational_snapshot.timezone, "now", lambda: now)
    PublicationDirty.objects.bulk_create([
        PublicationDirty(listing_id=UUID(int=index + 1), generation=1,
                         marked_at=now - timedelta(seconds=240))
        for index in range(count)
    ])
    before = list(PublicationDirty.objects.order_by("listing_id").values_list(
        "listing_id", "generation", "marked_at"))
    observations = []
    # First call is reported separately; subsequent calls reuse a warm process/DB.
    for index in range(6):
        totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

        def observe(execute, sql, params, many, context):
            totals["sql_queries"] += 1
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                totals["sql_execute_seconds"] += time.perf_counter() - started

        started = time.perf_counter()
        with connection.execute_wrapper(observe):
            result = operational_snapshot.collect_snapshot()
        elapsed = time.perf_counter() - started
        assert result["publication"] == {
            "count": count, "oldest_age_seconds": 240.0 if count else None,
        }
        assert result["scope"] == "durable_database_work_only"
        assert result["object_storage"]["orphan_inventory"] == "unmeasured"
        assert "worker_liveness" in result["not_measured"]
        assert connection.get_autocommit() and not connection.in_atomic_block
        assert list(PublicationDirty.objects.order_by("listing_id").values_list(
            "listing_id", "generation", "marked_at")) == before
        observations.append({"sample": index, "phase": "first" if index == 0 else "warm",
                             "publication_rows": count, "service_seconds_instrumented": elapsed,
                             **totals})
    record_property("n01e_snapshot_samples", json.dumps(observations, sort_keys=True))
    record_property("n01e_snapshot_scope", "Only publication backlog varies; all other work tables empty. No broker, worker, physical storage, restore or universal cardinality claim.")
