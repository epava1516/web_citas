"""Fixed-cohort native discovery diagnosis; not load or optimization evidence."""

import hashlib
import json
import statistics
import time

import pytest
from django.conf import settings
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings.models import Listing
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_discovery_fixed_cohort_segments(request, record_property):
    client = request.getfixturevalue("directory")
    assert connection.vendor == "postgresql" and not settings.PROMOTION_TEST_MODE
    populate(100)
    listings = list(
        Listing.objects.filter(status="published")
        .select_related("approved_revision")
        .order_by("-published_at", "pk")
    )
    assert len(listings) == 100
    profile = next(row.approved_revision.profile_type for row in listings
                   if row.approved_revision.profile_type not in {"trans", ""})
    selected = [row.pk for row in listings if row.approved_revision.profile_type == profile]
    assert selected
    ordered = [row.pk for row in listings]
    observations = []
    for language in ("es", "en"):
        scenarios = [
            ("listing", f"/{language}/", {}, ordered[:24], 100),
            ("page2", f"/{language}/", {"page": "2"}, ordered[24:48], 100),
            ("profile", f"/{language}/", {"profile": [profile]}, selected[:24], len(selected)),
            ("empty", f"/{language}/", {"q": "n01babsentsyntheticterm"}, [], 0),
            ("detail", f"/{language}/listing/{listings[0].pk}/", {}, [listings[0].pk], None),
        ]
        for name, path, params, expected_ids, expected_count in scenarios:
            samples = []
            for index in range(6):
                totals = {"queries": 0, "execute_seconds": 0.0}

                def measured(execute, sql, values, many, context):
                    totals["queries"] += 1
                    started = time.perf_counter()
                    try:
                        return execute(sql, values, many, context)
                    finally:
                        totals["execute_seconds"] += time.perf_counter() - started

                started = time.perf_counter()
                with connection.execute_wrapper(measured):
                    response = client.get(path, params)
                elapsed = time.perf_counter() - started
                assert response.status_code == 200
                assert response["Cache-Control"] == "no-store"
                assert f'lang="{language}"'.encode() in response.content
                assert b"fixture-model-b@example.invalid" not in response.content
                if expected_count is None:
                    ids = [response.context["listing"].pk]
                else:
                    page = response.context["page"]
                    assert page.paginator.count == expected_count
                    ids = [row.pk for row in page.object_list]
                assert ids == expected_ids
                route = getattr(response.wsgi_request, "_publication_route", {})
                samples.append({
                    "index": index, "position": "first_after_preparation" if index == 0 else "subsequent",
                    "seconds_instrumented": elapsed, **totals,
                    "route": route.get("route"), "reason": route.get("reason"),
                    "returned_count": len(ids),
                    "ordered_ids_sha256": hashlib.sha256(
                        ",".join(str(pk) for pk in ids).encode()
                    ).hexdigest(),
                })
            subsequent = [s["seconds_instrumented"] for s in samples[1:]]
            observations.append({
                "scenario": name, "language": language, "population": 100,
                "expected_total": expected_count, "samples": samples,
                "subsequent_median_seconds": statistics.median(subsequent),
                "subsequent_min_seconds": min(subsequent), "subsequent_max_seconds": max(subsequent),
            })
    assert Listing.objects.filter(status="published").count() == 100
    record_property("n01b_observations", json.dumps(observations, sort_keys=True))
    record_property("measured_requests", 60)
    record_property("scope", "Native organic fixed100cohort,ES/EN5segments6requests; first/subsequent not guaranteed cold/hotOS. No product monkeypatch, promos, TCP, concurrency, p95, causal optimization or capacity.")
