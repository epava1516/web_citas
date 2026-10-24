"""Finite attribution of the existing 100-profile diagnostic, separate from controls."""

import json
import os
import time
from collections import defaultdict
from functools import wraps

import pytest
from beta_read_baseline_diagnostic import test_sequential_read_diagnostic as run_diagnostic
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog import promotion_exposure
from apps.listings.public_validation import PublicationContext


@pytest.mark.django_db(transaction=True)
def test_promotional_read_attribution(request, settings, monkeypatch, record_property):
    stats = defaultdict(lambda: {"calls": 0, "inclusive_seconds": 0.0, "exclusive_sql_calls": 0})
    stack = []
    observing = {"active": False, "requests": 0}
    client = request.getfixturevalue("directory")
    original_get = client.get

    def observed_get(*args, **kwargs):
        observing["active"] = True
        observing["requests"] += 1
        try:
            return original_get(*args, **kwargs)
        finally:
            observing["active"] = False

    monkeypatch.setattr(client, "get", observed_get)

    def instrument(owner, name, label):
        original = getattr(owner, name)

        @wraps(original)
        def call(*args, **kwargs):
            if not observing["active"]:
                return original(*args, **kwargs)
            stack.append(label)
            start = time.perf_counter()
            try:
                return original(*args, **kwargs)
            finally:
                stats[label]["calls"] += 1
                stats[label]["inclusive_seconds"] += time.perf_counter() - start
                assert stack.pop() == label

        monkeypatch.setattr(owner, name, call)

    instrument(PublicationContext, "__init__", "population_context")
    for name in ["ranked", "eligible", "can_manage_person", "publicly_visible"]:
        instrument(promotion_exposure, name, name)

    def sql_event(execute, sql, params, many, context):
        if stack:
            stats[stack[-1]]["exclusive_sql_calls"] += 1
        return execute(sql, params, many, context)

    with connection.execute_wrapper(sql_event):
        run_diagnostic(request, settings, monkeypatch, record_property, 100)
    assert observing["requests"] == 84
    result = {
        "result": "ATTRIBUTION_COMPLETE", "run_id": os.environ["LOCAL_CI_ISOLATED_BROKER_RUN"],
        "count": 100, "requests": observing["requests"], "stats": dict(stats),
        "limits": "Inclusive wall times overlap and include instrumentation; do not add or compare to clean latency. SQL counts attributed exclusively to innermost observed function. No raw SQL/parameters retained.",
    }
    output = settings.BASE_DIR / "artifacts/local-ci" / result["run_id"]
    (output / "beta-promotion-attribution.json").write_text(json.dumps(result, indent=2))
    record_property("beta_promotion_attribution", json.dumps(result))
