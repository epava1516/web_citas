"""MOD-04 §16 route coverage at 10.000 listings: mode/filter/promotion -> real route,
native equivalence and observed in-process cost. Opt-in; Client, not TCP or capacity."""

import json
import os
import statistics
import time
from pathlib import Path

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_state_matrix import prepare_population

from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import publication_state

pytestmark = pytest.mark.django_db(transaction=True)

CASES = [
    ("normal", "/es/", {}),
    ("normal", "/en/", {"q": "photography"}),
    ("normal", "/es/", {"checked": ["age"]}),
    ("normal", "/es/", {"checked": ["contact", "agency"]}),
    ("normal", "/es/", {"page": "3"}),
    ("production", "/es/", {}),
    ("production", "/en/", {"q": "photography", "checked": ["age"]}),
    ("promotions", "/es/", {}),
]


def test_route_coverage_matrix(request, settings, monkeypatch, record_property):
    legacy_output = os.getenv("ROUTE_COVERAGE_OUTPUT")
    selected = any(str(argument).partition("::")[2] == "test_route_coverage_matrix"
                   for argument in request.config.args)
    if not legacy_output and not selected:
        pytest.skip("Explicit coverage run only")
    timing_output = request.config.getoption("--gate-timings-output", default=None)
    if not legacy_output and not timing_output:
        pytest.fail("Explicit route coverage requires the owned CI report directory")
    output = Path(legacy_output) if legacy_output else Path(timing_output).parent
    assert output.is_dir()
    client = request.getfixturevalue("directory")
    prepare_population(10000, "repeated")
    entitlement_count = PromotionEntitlement.objects.count()
    rows = []
    for mode, path, params in CASES:
        settings.PRODUCTION = mode == "production"
        settings.PROMOTION_TEST_MODE = mode == "promotions"
        publication_state.rules_version.cache_clear()
        publication_state.mark_stale()
        while publication_state.refresh(500):
            pass
        warm = client.get(path, params)
        timings = []
        for _ in range(2 if mode != "promotions" else 1):
            start = time.perf_counter()
            response = client.get(path, params)
            timings.append(time.perf_counter() - start)
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
            start = time.perf_counter()
            native = client.get(path, params)
            native_seconds = time.perf_counter() - start
        page = response.context["page"] if response.status_code == 200 else None
        row = {
            "mode": mode, "path": path, "params": params, "status": response.status_code,
            "route": response.wsgi_request._publication_route,
            "count": page.paginator.count if page is not None else None,
            "equivalent_to_native": response.status_code == native.status_code
            and response.content == native.content and warm.content == response.content,
            "controls_seconds": timings, "control_mean_seconds": statistics.mean(timings),
            "native_seconds": native_seconds,
        }
        assert row["equivalent_to_native"], row
        expected_count = 0 if mode == "production" or params.get("checked") else 10000
        assert row["count"] == expected_count, row
        rows.append(row)
    publication_state.rules_version.cache_clear()
    report = {"rows": rows, "population": 10000, "promotion_entitlements": entitlement_count,
              "capacity_accepted": False, "real_provider_credited": False,
              "scope": "Client in-process, PostgreSQL synthetic 10.000 repeated; "
                   "2 controls (1 for promotions) after warmup; not TCP/WSGI/capacity; native comparison "
                   "forces the native path in the same process. PRODUCTION rejects the synthetic simulator "
                   "verification, so its population is not publishable. Promotion mode does not issue entitlements."}
    (output / "route-coverage.json").write_text(json.dumps(report, indent=1, default=str))
    record_property("route_coverage_matrix", report)
