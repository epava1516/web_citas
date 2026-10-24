"""Read-only PostgreSQL plan attribution; never clean HTTP/capacity evidence."""

import hashlib
import json
import os
import re
import runpy

import pytest
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_orders import setup
from test_promotion_paged_equivalence import grant
from test_publication_state_matrix import prepare_population

from apps.catalog import promotion_paging
from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.listings import discovery, publication_state
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def redact(value):
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"'(?:[^']|'')*'", "'<redacted>'", value)
        value = re.sub(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "<uuid>", value)
        return re.sub(r"(?<![\w.])[-+]?\d+(?:\.\d+)?(?![\w.])", "<number>", value)
    return value


def test_promotional_ordering_read_only_plans(request, settings, record_property):
    run_id = os.environ.get("LOCAL_CI_ISOLATED_BROKER_RUN")
    assert run_id and connection.vendor == "postgresql"
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_") and not settings.PRODUCTION
    _, _, top, _ = setup(request, settings)
    prepare_population(1000, "diverse")
    premium = PromotionProductVersion.objects.create(
        product=PromotionProduct.objects.create(slug="beta_plan_premium", kind="premium"),
        version=1, name_es="Prueba", name_en="Test", duration_days=top.duration_days,
        amount=top.amount, currency=top.currency, tax_rate=top.tax_rate,
        published_at=timezone.now(), is_current=True,
    )
    rows = list(Listing.objects.filter(status="published", person__agency__isnull=False)
                .select_related("person__agency__owner").order_by("pk")[:200])
    for index, row in enumerate(rows):
        grant(row.person, premium if index % 3 == 0 else top)
    while publication_state.refresh(500):
        pass
    assert not PublicationDirty.objects.exists()
    reference = settings.BASE_DIR / "docs/evidencias/b08-sql-promocional-referencia-20261020.py"
    reference_sha = hashlib.sha256(reference.read_bytes()).hexdigest()
    assert reference_sha == "3663de3391f2ba93c8aaa1fc4168039ec7547d06acd8a0cc41294b167fd2ba38"
    frozen_order = runpy.run_path(str(reference), run_name="apps.catalog._beta_sql_reference")["order_population"]
    plans = {}
    ordered_ids = {}
    now = timezone.now()

    def inspect_order(population, identifier, *, trusted_snapshot):
        assert trusted_snapshot
        with connection.cursor() as cursor:
            cursor.execute("SHOW transaction_isolation")
            assert cursor.fetchone()[0] == "repeatable read"
            cursor.execute("SHOW transaction_read_only")
            assert cursor.fetchone()[0] == "on"
        captured = []

        def capture(execute, sql, params, many, context):
            assert not many
            captured.append((sql, params))
            return execute(sql, params, many, context)

        with connection.execute_wrapper(capture):
            fast = promotion_paging._snapshot_order_population(population, identifier, now=now)
        assert len(captured) == 1
        with connection.cursor() as cursor:
            sql, params = captured[0]
            cursor.execute("EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) " + sql, params)
            raw_plan = cursor.fetchone()[0]
            plans["compatible_rights_once"] = json.loads(raw_plan) if isinstance(raw_plan, str) else raw_plan
        slow = frozen_order(population, identifier, now=now)
        for label, query in [("correlated_page", slow), ("snapshot_page", fast)]:
            page_query = query.values_list(identifier, "_promotion_priority")[:24]
            plans[label] = json.loads(page_query.explain(analyze=True, buffers=True, timing=False, format="json"))
            ordered_ids[label] = list(page_query)
        assert ordered_ids["correlated_page"] == ordered_ids["snapshot_page"]
        return fast

    form = discovery.SearchForm({})
    assert form.is_valid()
    page = publication_state.state_page(discovery.candidates(form.cleaned_data), 1, promotion_order=inspect_order)
    assert page and page.paginator.count == 1000 and len(page.object_list) == 24
    assert set(page.sponsorship.values()) <= {"premium", "top"} and page.sponsorship
    result = {
        "run_id": run_id, "result": "DIAGNOSTIC_COMPLETE", "synthetic_only": True,
        "count": 1000, "rights": 200, "sample": "first ES page, no filter, compatible clean state",
        "snapshot": "caller-owned REPEATABLE READ READ ONLY",
        "explain": "ANALYZE BUFFERS TIMING OFF FORMAT JSON; executes only affected SELECTs",
        "plans": redact(plans), "ordered_page_parity": True, "reference_sha256": reference_sha,
        "limits": ["Warm diagnostic plans only; repeated reads affect caches; no clean latency ratio",
                   "Plan rows and loops belong to each node; do not sum nested scan populations",
                   "No PostgreSQL CPU, TCP, throughput or capacity verdict",
                   "Only1000/200rights; no national geography, independent photos or actual provider"],
    }
    output = settings.BASE_DIR / "artifacts" / "local-ci" / run_id / "beta-promotion-plans.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    record_property("beta_promotion_plans_sha256", hashlib.sha256(output.read_bytes()).hexdigest())
