"""Native full-sized binary selection page attribution; no capacity acceptance."""

import cProfile
import io
import json
import pstats
import time
from uuid import uuid4

import pytest
from django.db import connection
from test_capacity_selection_tcp import REASON, prepare_target
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.models import RightsPortabilitySelectionRead
from apps.safety.rights_portability_selection_review import record

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_full_binary_page_attribution(
    request, settings, monkeypatch, live_server, record_property
):
    context = {}
    target = prepare_target(request, settings, monkeypatch, live_server,
                            "capacity-subject-profile", independent_reviewer=True,
                            include_binary=True, details=context)
    case, selection = target[:2]
    queries = {}

    def observe(execute, sql, params, many, execution_context):
        verb = sql.split(maxsplit=1)[0].upper()
        begin = time.perf_counter()
        try:
            return execute(sql, params, many, execution_context)
        finally:
            item = queries.setdefault(verb, {"count": 0, "seconds": 0})
            item["count"] += 1
            item["seconds"] += time.perf_counter() - begin

    profile = cProfile.Profile()
    started = time.perf_counter()
    try:
        with connection.execute_wrapper(observe):
            profile.enable()
            evidence, page = record(context["reviewer"], case.pk, case.version,
                                    selection.pk, uuid4(), REASON, page=1)
    finally:
        profile.disable()
        output = io.StringIO()
        pstats.Stats(profile, stream=output).sort_stats("cumulative").print_stats(70)
        record_property("native_binary_page_profile", json.dumps({
            "seconds_with_instrumentation": time.perf_counter() - started,
            "queries": queries, "profile": output.getvalue(),
            "fixture": target[5], "binary_preparation": context["binary_preparation_operations"],
            "scope": "One native page in real PostgreSQL, full-size synthetic source and16images. "
                     "Observer delegates all actual SQL. Instrumented attribution; no HTTP p95, "
                     "CPU causal experiment, enforced global budget or N3 acceptance.",
        }))
    assert page["pagination"] == {"page": 1, "pages": 31, "total": 1517, "rows": 50}
    assert sum(len(items) for items in page["datasets"].values()) == 50
    assert RightsPortabilitySelectionRead.objects.filter(pk=evidence.pk, selection=selection).exists()
    assert queries["SELECT"]["count"] > 0
