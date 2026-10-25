"""Unknown versus operationally prepared state, with unchanged request oracles."""

import io
import json
import time

import pytest
from django.core.management import call_command
from test_discovery import directory  # noqa: F401
from test_discovery_segment_baseline import (
    test_native_discovery_fixed_cohort_segments as measure_segments,
)
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_discovery_unknown_and_prepared_states(request, record_property):
    captured = {}
    measure_segments(request, captured.__setitem__)
    before = json.loads(captured["n01b_observations"])
    before_business = list(
        Listing.objects.order_by("pk").values_list(
            "pk", "approved_revision_id", "status", "published_at", "expires_at"
        )
    )
    before_dirty = PublicationDirty.objects.count()
    stream = io.StringIO()
    started = time.perf_counter()
    call_command("refresh_publication_state", "--all", stdout=stream)
    preparation_seconds = time.perf_counter() - started
    assert publication_state.all_state_current()
    assert not PublicationDirty.objects.exists()
    assert list(
        Listing.objects.order_by("pk").values_list(
            "pk", "approved_revision_id", "status", "published_at", "expires_at"
        )
    ) == before_business
    captured.clear()
    measure_segments(request, captured.__setitem__)
    after = json.loads(captured["n01b_observations"])
    assert len(before) == len(after) == 10
    for initial, prepared in zip(before, after, strict=True):
        assert (initial["language"], initial["scenario"]) == (
            prepared["language"], prepared["scenario"]
        )
        assert initial["expected_total"] == prepared["expected_total"]
        assert len(initial["samples"]) == len(prepared["samples"]) == 6
        for old, new in zip(initial["samples"], prepared["samples"], strict=True):
            assert old["ordered_ids_sha256"] == new["ordered_ids_sha256"]
            assert old["returned_count"] == new["returned_count"]
        if initial["scenario"] in {"listing", "page2", "profile"}:
            assert all(sample["route"] == "fallback" for sample in initial["samples"])
            assert all(sample["reason"] == "state_unknown_over_limit"
                       for sample in initial["samples"])
        if prepared["scenario"] != "detail":
            assert all(sample["route"] == "state" for sample in prepared["samples"])
    assert publication_state.all_state_current()
    assert not PublicationDirty.objects.exists()
    record_property("n01c_observations", json.dumps({"before": before, "after": after}, sort_keys=True))
    record_property("preparation_seconds", preparation_seconds)
    record_property("preparation_dirty_before", before_dirty)
    record_property("prepared_listing_count", len(before_business))
    record_property("measured_requests", 120)
    record_property("scope", "Unknown then refresh_publication_state--all on same synthetic100cohort. Operational preparation includes VACUUM/ANALYZE; fixed order and warmup confound attribution. No product edits, worker/Beat throughput, p95, TCP, capacity or code-optimization claim.")
