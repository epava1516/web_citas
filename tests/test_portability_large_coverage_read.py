"""Native audited page read with1500 synthetic revisions; partial performance probe."""

import time
import tracemalloc
from uuid import uuid4

import pytest
import test_rights_portability_export_races as fixtures
from django.db import connection, transaction
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Revision
from apps.safety.models import RightsPortabilityCoverageRead
from apps.safety.rights_copy_inspection import SECTIONS
from apps.safety.rights_exports import canonical, reviewer_case, source_copy
from apps.safety.rights_portability_coverage_inspection import inspect_page
from apps.safety.rights_portability_coverage_store import save_coverage

pytestmark = pytest.mark.django_db(transaction=True)


def test_first_audited_coverage_page_with_large_retained_source(
    request,
    settings,
    monkeypatch,
    record_property,
):
    request.getfixturevalue("directory")
    original = fixtures.ready
    description = ("Synthetic retained large source. " * 200)[:6000]
    count = 1500

    def ready(*args, **kwargs):
        result = original(*args, **kwargs)
        person = result[-1]
        Revision.objects.bulk_create(
            [
                Revision(
                    listing=person.listing,
                    manager_version=person.manager_version,
                    title=f"Synthetic retained history {index}",
                    description=description,
                )
                for index in range(count)
            ],
            batch_size=100,
        )
        return result

    monkeypatch.setattr(fixtures, "ready", ready)
    case, author, selection, decision, _, _, _ = fixtures.prepared_selection(
        request,
        settings,
        monkeypatch,
        False,
    )
    reason = "Inspect real synthetic large source before volume acceptance"
    coverage = save_coverage(
        author,
        case.pk,
        case.version,
        decision.pk,
        uuid4(),
        0,
        reason,
        {name: {} for name in SECTIONS},
        {},
        allow_partial=True,
    )
    with transaction.atomic():
        locked, person, listing = reviewer_case(author, case.pk)
        source = source_copy(person, listing, locked)
    assert len(source["revisions"]) >= count
    source_bytes = len(canonical(source).encode())
    assert source_bytes > 8 * 1024 * 1024
    del source
    queries = 0

    def counter(execute, sql, params, many, context):
        nonlocal queries
        queries += 1
        return execute(sql, params, many, context)

    before = RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count()
    tracemalloc.start()
    started = time.perf_counter()
    try:
        with connection.execute_wrapper(counter):
            action, page = inspect_page(
                decision.action.actor,
                case.pk,
                case.version,
                coverage.pk,
                uuid4(),
                reason,
                "revisions",
                0,
                1,
            )
        seconds = time.perf_counter() - started
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert action.operation == "coverage_inspect"
    assert page["row_count"] >= count and page["has_next_row"]
    assert RightsPortabilityCoverageRead.objects.filter(coverage=coverage).count() == before + 1
    case.refresh_from_db()
    assert case.status == "reviewing" and case.version == locked.version
    record_property("historical_revisions", count)
    record_property("source_bytes", source_bytes)
    record_property("page_seconds_instrumented", seconds)
    record_property("page_python_peak_bytes", peak)
    record_property("page_sql_queries", queries)
    record_property(
        "scope", "First native audited coverage page only; no full approval/closure acceptance"
    )
