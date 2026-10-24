"""Sequential in-process diagnostics; never a TCP throughput/capacity verdict."""

import hashlib
import json
import math
import os
import resource
import time
from collections import Counter
from uuid import uuid4

import pytest
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_publication_state_matrix import prepare_population

from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_orders import create_order, receive_event, synthetic_event
from apps.listings import discovery
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def percentile(values, percent):
    return sorted(values)[max(0, math.ceil(len(values) * percent / 100) - 1)]


@pytest.mark.parametrize("count", [100, 1000, 10000])
def test_sequential_read_diagnostic(request, settings, monkeypatch, record_property, count):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id and connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    output = settings.BASE_DIR / "artifacts" / "local-ci" / run_id
    assert output.is_dir() and not settings.PRODUCTION
    _, _, top, _ = setup(request, settings)
    client = request.getfixturevalue("directory")
    prepare_population(count, "diverse")
    settings.PUBLICATION_STATE_READ_REPAIR = False
    premium = PromotionProductVersion.objects.create(
        product=PromotionProduct.objects.create(slug="beta_baseline_premium", kind="premium"),
        version=1, name_es="Prueba", name_en="Test", duration_days=top.duration_days,
        amount=top.amount, currency=top.currency, tax_rate=top.tax_rate,
        published_at=timezone.now(), is_current=True,
    )
    agency_rows = list(
        Listing.objects.filter(status="published", person__agency__isnull=False)
        .select_related("person__agency__owner", "approved_revision").order_by("pk")
    )
    promoted = agency_rows[:count // 5]
    for index, listing in enumerate(promoted):
        buyer = listing.person.agency.owner
        buyer.mfa_enabled = True
        buyer.save(update_fields=["mfa_enabled"])
        credentials = {"mfa_version": buyer.mfa_version, "account_version": buyer.session_version}
        order = create_order(
            buyer, listing.pk, (premium if index % 3 == 0 else top).pk, uuid4(), **credentials
        )
        payload, signature = synthetic_event(order.payment_attempt, "succeeded", uuid4())
        receive_event(buyer, payload, signature, **credentials)
    # Commercial setup may mark state dirty. Establish a clean baseline afterwards.
    from apps.listings import publication_state

    while publication_state.refresh(500):
        pass
    assert not PublicationDirty.objects.exists()
    city = agency_rows[0].approved_revision.municipality_id
    scenarios = [
        ("first_es", "/es/", {}),
        ("text_en", "/en/", {"q": "photography"}),
        ("last_es", "/es/", {"page": math.ceil(count / 24)}),
        ("combined_en", "/en/", {"city": city, "language": "en"}),
    ]
    reports = []

    def fingerprint(response):
        assert response.status_code == 200
        page = response.context["page"]
        ids = [str(row.pk) for row in page.object_list]
        assert len(ids) == len(set(ids)) and len(ids) <= 24
        return {
            "ids": ids, "count": page.paginator.count, "page": page.number,
            "sponsorship": [card["sponsorship"] for card in response.context["cards"]],
            "route": response.wsgi_request._publication_route,
        }

    for mode in ("organic", "promoted", "backlog"):
        settings.PROMOTION_TEST_MODE = mode != "organic"
        withdrawn = []
        if mode == "backlog":
            # Stale projection deliberately retained; no mocked public authority.
            monkeypatch.setattr("apps.listings.tasks.refresh_publication_state.delay", lambda: None)
            withdrawn = [row.pk for row in promoted[:max(1, count // 100)]]
            Listing.objects.filter(pk__in=withdrawn).update(status="withdrawn")
            assert PublicationDirty.objects.filter(listing_id__in=withdrawn).count() == len(withdrawn)
        for name, path, query in scenarios:
            if mode == "backlog" and name == "last_es":
                query = {"page": math.ceil((count - len(withdrawn)) / 24)}
            expected = fingerprint(client.get(path, query))
            if name in {"first_es", "last_es"}:
                assert expected["count"] == count - len(withdrawn)
            assert not set(expected["ids"]) & {str(pk) for pk in withdrawn}
            if mode == "organic":
                assert not any(expected["sponsorship"])
            controls, cpu = [], []
            for _ in range(5):
                wall_start, cpu_start = time.perf_counter(), time.process_time()
                response = client.get(path, query)
                controls.append(time.perf_counter() - wall_start)
                cpu.append(time.process_time() - cpu_start)
                assert fingerprint(response) == expected
            sql = {"calls": 0, "driver_seconds": 0.0}
            renders = []

            def query_event(execute, sql_text, params, many, context):
                start = time.perf_counter()
                try:
                    return execute(sql_text, params, many, context)
                finally:
                    sql["calls"] += 1
                    sql["driver_seconds"] += time.perf_counter() - start

            original_render = discovery.render

            def render_event(*args, **kwargs):
                start = time.perf_counter()
                try:
                    return original_render(*args, **kwargs)
                finally:
                    renders.append(time.perf_counter() - start)

            with monkeypatch.context() as patch:
                patch.setattr(discovery, "render", render_event)
                start = time.perf_counter()
                with connection.execute_wrapper(query_event):
                    response = client.get(path, query)
                instrumented = time.perf_counter() - start
            assert fingerprint(response) == expected and len(renders) == 1
            reports.append({
                "mode": mode, "scenario": name, "path": path, "query": query,
                "fingerprint": expected, "controls_seconds": controls,
                "descriptive_p50_seconds": percentile(controls, 50),
                "descriptive_p95_seconds": percentile(controls, 95),
                "descriptive_p99_seconds": percentile(controls, 99),
                "process_cpu_seconds": cpu, "instrumented_seconds": instrumented,
                "render_seconds": renders[0], "sql": sql,
                "process_maxrss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            })
    result = {
        "run_id": run_id, "count": count, "result": "DIAGNOSTIC_COMPLETE",
        "synthetic_only": True, "concurrency": 1, "transport": "Django test client in process",
        "promoted_count": len(promoted), "withdrawn_count": len(withdrawn),
        "geography": dict(Counter(str(row.approved_revision.municipality_id) for row in agency_rows)),
        "dataset": "Existing diverse synthetic clone fixture; shared photos and agency",
        "reports": reports,
        "limits": [
            "Five controls: p95/p99 descriptive nearest rank, no statistical tail acceptance",
            "Process CPU/RSS cover pytest process; SQL driver elapsed is not PostgreSQL CPU",
            "No TCP, throughput, host resource isolation, queue capacity or production verdict",
            "No national geographic coverage or independent photo corpus",
        ],
    }
    destination = output / f"beta-read-diagnostic-{count}.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    record_property("beta_read_diagnostic_sha256", hashlib.sha256(destination.read_bytes()).hexdigest())
