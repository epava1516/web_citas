"""Current HTTP fallback feeds bounded observation beside a durable-work snapshot."""

import io
import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_operational_events import recorded_events  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.operational_snapshot import collect_snapshot
from apps.core.operational_window import summarize_window
from apps.listings import publication_state
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def test_actual_http_fallback_window_and_durable_backlog(request, record_property):
    assert connection.vendor == "postgresql"
    assert publication_state.DIRTY_LIMIT == 1000 and not publication_state.READ_REPAIR
    capture_events = request.getfixturevalue("recorded_events")
    client = request.getfixturevalue("directory")
    publication_state.refresh_all()
    state = client.get("/es/")
    assert state.status_code == 200
    assert state.wsgi_request._publication_route["route"] == "state"
    expected_ids = [row.pk for row in state.context["page"].object_list]
    marked_at = timezone.now() - timedelta(minutes=4)
    # Real persisted queue ceiling; orphan marks are an explicit synthetic
    # backlog fixture, not proof of 1001 domain-trigger writes or worker repair.
    PublicationDirty.objects.bulk_create([
        PublicationDirty(listing_id=uuid4(), generation=index + 1, marked_at=marked_at)
        for index in range(1001)
    ])
    fallback = client.get("/es/")
    assert fallback.status_code == 200
    assert fallback.wsgi_request._publication_route == {
        "route": "fallback", "reason": "state_dirty_over_limit",
    }
    assert [row.pk for row in fallback.context["page"].object_list] == expected_ids
    assert fallback.context["page"].paginator.count == state.context["page"].paginator.count
    snapshot = collect_snapshot()
    assert snapshot["scope"] == "durable_database_work_only"
    assert snapshot["publication"]["count"] == 1001
    sample_time = datetime.fromisoformat(snapshot["sampled_at"])
    expected_age = max(0, (sample_time - marked_at).total_seconds())
    assert snapshot["publication"]["oldest_age_seconds"] == pytest.approx(expected_age)
    assert {"broker_depth", "worker_liveness", "fallback_frequency"} <= set(snapshot["not_measured"])
    assert PublicationDirty.objects.count() == 1001
    assert connection.get_autocommit() and not connection.in_atomic_block

    rows = [row for row in capture_events() if row["event"] == "publication_read"]
    assert len(rows) == 2
    assert [row["route"] for row in rows] == ["state", "fallback"]
    timestamps = [row["timestamp_seconds"] for row in rows]
    data = b"".join(json.dumps(row).encode() + b"\n" for row in rows)
    window = summarize_window(io.BytesIO(data), min(timestamps), max(timestamps) + 1)
    assert window["scope"] == "observed_input_only"
    assert window["coverage"] == "unverified" and window["health"] == "unknown"
    assert window["counts"]["publication_observed"] == 2
    assert window["counts"]["fallback_observed"] == 1
    assert window["fallback_fraction_observed"] == 0.5
    assert window["publication_reasons_observed"]["state_dirty_over_limit"] == 1
    record_property("read_delivery_observation", dict(
        actual_http_reads=2, fallback_reads=1, fallback_fraction_observed=0.5,
        dirty_limit=1000, durable_mark_count=1001,
        oldest_age_seconds=snapshot["publication"]["oldest_age_seconds"],
        snapshot_scope=snapshot["scope"], window_scope=window["scope"],
        coverage=window["coverage"], health=window["health"],
        limits="Synthetic orphan backlog, observed input only; not full traffic, broker, worker repair or production health",
    ))
