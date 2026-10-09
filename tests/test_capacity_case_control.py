"""Small real case validates stage/TCP instrumentation; not large-case capacity."""

import json
import sys
import time
from pathlib import Path

import pytest
import test_rights_portability_response_races as response_fixture
from django.db import connection
from test_portability_large_closed_json_transport import (
    test_native_closed_selected_json_over_local_tcp as run_transport,
)
from test_reports import directory, photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_small_case_instrumentation(
    request, settings, monkeypatch, live_server, tmp_path, record_property
):
    if getattr(settings, "CAPACITY_SQL_DIAGNOSE", False):
        original = response_fixture.approved_coverage
        counters = {}
        app_root = str(Path(__file__).resolve().parents[1] / "apps") + "/"

        def sql_observed(execute, sql, params, many, context):
            frame = sys._getframe(1)
            caller = "outside-app"
            while frame is not None:
                filename = frame.f_code.co_filename
                if filename.startswith(app_root):
                    caller = filename[len(app_root):] + ":" + frame.f_code.co_name
                    break
                frame = frame.f_back
            del frame
            bucket = counters.setdefault(caller, {"queries": 0, "cursor_seconds": 0.0})
            bucket["queries"] += 1
            started = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                bucket["cursor_seconds"] += time.perf_counter() - started

        def diagnosed(*args, **kwargs):
            started = time.perf_counter()
            try:
                with connection.execute_wrapper(sql_observed):
                    return original(*args, **kwargs)
            finally:
                record_property("preparation_sql_attribution", json.dumps(counters))
                record_property("instrumented_preparation_seconds", time.perf_counter() - started)
                record_property("attribution_scope", "Preparation main connection only; cursor duration excludes lazy materialization; no SQL or params recorded")

        monkeypatch.setattr(response_fixture, "approved_coverage", diagnosed)
    run_transport(request, settings, monkeypatch, live_server, tmp_path, record_property,
                  large=False, control=True)
