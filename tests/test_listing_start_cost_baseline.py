"""Attribute existing revision-start requests without changing tasks or oracles."""

import json
import re
import sys
import time
from collections import Counter, defaultdict

import pytest
from django.apps import apps
from django.db import connection
from django.test import Client
from test_revised_listings import (
    pending,  # noqa: F401
    photo_environment,  # noqa: F401
    prepared,  # noqa: F401
    published,  # noqa: F401
    scenario,  # noqa: F401
)
from test_revised_listings import (
    test_rejection_preserves_public_version_and_rate_ids_are_isolated as _rejection_oracle,
)
from test_revised_listings import (
    test_revised_version_keeps_approved_snapshot_and_reuses_bytes as _approved_oracle,
)

from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)


def sql_stage():
    """Only code identities; never inspect locals, SQL values or subject data."""
    seen = set()
    frame = sys._getframe(1)
    try:
        while frame is not None:
            name = frame.f_code.co_name
            filename = frame.f_code.co_filename.replace("\\", "/")
            for suffix, function, stage in [
                ("/apps/mediafiles/tasks.py", "process_blob", "photo_task_eager"),
                ("/apps/listings/publication_signals.py", "_enqueue_refresh", "state_task_eager"),
                ("/apps/listings/revisions.py", "create_draft", "create_draft"),
                ("/apps/core/verification.py", "locked_manager_person", "manager_authority"),
            ]:
                if name == function and filename.endswith(suffix):
                    seen.add(stage)
            frame = frame.f_back
    finally:
        del frame
    return next((s for s in ["photo_task_eager", "state_task_eager", "create_draft",
                             "manager_authority"] if s in seen), "request_other")


@pytest.mark.parametrize("case", ["approved", "rejected_correction"])
def test_listing_start_query_attribution(request, monkeypatch, record_property, case):
    fixture = request.getfixturevalue("published")
    assert connection.vendor == "postgresql" and celery_app.conf.task_always_eager
    original = Client.request
    tables = {model._meta.db_table for model in apps.get_models(include_auto_created=True)}
    samples = []

    def measured(client, **request):
        path = request.get("PATH_INFO", "")
        if (request.get("REQUEST_METHOD") != "POST"
                or not re.fullmatch(r"/(es|en)/person/[a-f0-9-]+/listing/start/", path)):
            return original(client, **request)
        totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}
        stages = defaultdict(lambda: {"sql_queries": 0, "sql_execute_seconds": 0.0})
        table_counts, verbs = Counter(), Counter()

        def observe(execute, sql, params, many, context):
            stage = sql_stage()
            if isinstance(sql, str):
                first = sql.lstrip().split(None, 1)[0].upper() if sql.strip() else "OTHER"
                verb = first if first in {"SELECT", "INSERT", "UPDATE", "DELETE", "SET",
                                          "BEGIN", "COMMIT", "ROLLBACK", "SAVEPOINT", "RELEASE"} else "OTHER"
                verbs[verb] += 1
                # Only exact quoted, statically known Django table identifiers survive.
                table_counts.update({table for table in tables if '"' + table + '"' in sql})
            else:
                verbs["OTHER"] += 1
            totals["sql_queries"] += 1
            stages[stage]["sql_queries"] += 1
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                elapsed = time.perf_counter() - started
                totals["sql_execute_seconds"] += elapsed
                stages[stage]["sql_execute_seconds"] += elapsed

        started = time.perf_counter()
        with connection.execute_wrapper(observe):
            response = original(client, **request)
        elapsed = time.perf_counter() - started
        assert response.status_code == 302
        assert totals["sql_queries"] == sum(s["sql_queries"] for s in stages.values())
        assert totals["sql_queries"] == sum(verbs.values()) and totals["sql_queries"] > 0
        samples.append({"ordinal": len(samples) + 1, "case": case, "status": 302,
                        "request_seconds_instrumented": elapsed, **totals,
                        "stages": dict(stages), "known_table_query_occurrences": dict(table_counts),
                        "verbs": dict(verbs), "task_always_eager": True})
        return response

    monkeypatch.setattr(Client, "request", measured)
    (_approved_oracle if case == "approved" else _rejection_oracle)(fixture)
    assert len(samples) == (1 if case == "approved" else 2)
    record_property("n06a_start_samples", json.dumps(samples, sort_keys=True))
    record_property("n06a_scope", "Existing functional oracles unchanged; only successful listing-start POSTs timed. Real Django/PostgreSQL with original eager Celery fixtures, not broker/worker latency. Code-stack classification overhead included in request wall; joined table occurrences are not additive query counts. No SQL/params/paths/subject identifiers retained.")
