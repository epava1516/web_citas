"""MOD-04 §16 route coverage at 10.000 listings: mode/filter/promotion -> real route,
native equivalence and observed in-process cost. Opt-in; Client, not TCP or capacity."""

import json
import os
import statistics
import time

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_state_matrix import prepare_population

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


@pytest.mark.skipif(not os.getenv("ROUTE_COVERAGE_OUTPUT"), reason="Explicit coverage run only")
def test_route_coverage_matrix(request, settings, monkeypatch):
    client = request.getfixturevalue("directory")
    prepare_population(10000, "repeated")
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
            "count": page.paginator.count if page else None,
            "equivalent_to_native": response.status_code == native.status_code
            and response.content == native.content and warm.content == response.content,
            "controls_seconds": timings, "control_mean_seconds": statistics.mean(timings),
            "native_seconds": native_seconds,
        }
        assert row["equivalent_to_native"], row
        rows.append(row)
    publication_state.rules_version.cache_clear()
    with open(os.path.join(os.environ["ROUTE_COVERAGE_OUTPUT"], "route-coverage.json"), "w") as fh:
        json.dump({"rows": rows, "scope": "Client in-process, PostgreSQL synthetic 10.000 repeated; "
                   "2 controls (1 for promotions) after warmup; not TCP/WSGI/capacity; native comparison "
                   "forces the native path in the same process. PRODUCTION rejects the synthetic simulator "
                   "verification, so its population is not publishable."}, fh, indent=1, default=str)
