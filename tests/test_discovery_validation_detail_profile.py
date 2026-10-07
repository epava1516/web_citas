"""One finite 10k attribution run, without changing application validation."""

import cProfile
import time
from pathlib import Path

import pytest
from django.db import connection
from django.forms import models as form_models
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, forms, moderation, public_validation, submissions
from apps.listings.models import Revision
from apps.listings.public_validation import PublicationContext, SnapshotDetails
from scripts.benchmark_rule_profile import RuleProfile
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_validation_detail_profile_10000(request, monkeypatch, record_property):
    client = request.getfixturevalue("directory")
    populate(10000)
    assert connection.vendor == "postgresql"
    cpu_start, wall_start = time.thread_time(), time.perf_counter()
    control = client.get("/es/")
    control_wall, control_cpu = time.perf_counter() - wall_start, time.thread_time() - cpu_start
    assert control.status_code == 200
    assert control.context["page"].paginator.count == 10000
    profile = RuleProfile(cpu_clock=time.thread_time)
    targets = [
        (moderation, "validate_submission"), (submissions, "publication_ready"),
        (PublicationContext, "__init__"), (PublicationContext, "_bound_validation"),
        (public_validation, "model_to_dict"), (form_models, "construct_instance"),
        (forms, "validate_listing_text"), (forms, "normalize_telegram"),
        (discovery, "render"),
    ]
    for cls in [SnapshotDetails, forms.ContactsForm]:
        for name in ["full_clean", "_clean_fields", "_clean_form", "_post_clean", "_get_validation_exclusions"]:
            targets.append((cls, name))
    for name in ["full_clean", "clean_fields", "clean", "validate_unique", "validate_constraints"]:
        targets.append((Revision, name))
    for owner, name in targets:
        label = f"{owner.__name__}.{name}"
        monkeypatch.setattr(owner, name, profile.wrap(label, getattr(owner, name)))

    def sql_event(execute, sql, params, many, context):
        return profile.wrap("sql.cursor_execute", execute)(sql, params, many, context)

    # Supplementary native call graph locates comprehensions/metadata lookups
    # without rewriting inline predicates or collecting any locals/arguments.
    native = cProfile.Profile()
    cpu_start, wall_start = time.thread_time(), time.perf_counter()
    native.enable()
    try:
        with connection.execute_wrapper(sql_event):
            response = client.get("/es/")
    finally:
        native.disable()
    measured_wall = time.perf_counter() - wall_start
    measured_cpu = time.thread_time() - cpu_start
    assert response.status_code == 200
    assert response.context["page"].paginator.count == 10000
    assert len(response.context["page"].object_list) == 24
    assert response["Cache-Control"] == "no-store"
    rows = profile.report()
    by_rule = {row["rule"]: row for row in rows}
    assert by_rule["apps.listings.moderation.validate_submission"]["calls"] == 10000
    assert 10000 <= by_rule["Revision.full_clean"]["calls"] <= 20000
    for row in rows:
        assert abs(row["inclusive_time"] - row["exclusive_time"]
                   - sum(row["instrumented_children"].values())) < 1e-7
    root = Path(__file__).resolve().parents[1]

    def label(code):
        if isinstance(code, str):
            return code
        path = Path(code.co_filename)
        try:
            source = str(path.relative_to(root))
        except ValueError:
            source = path.name
        return f"{source}:{code.co_firstlineno}:{code.co_name}"

    entries = native.getstats()
    native_rows = [{
        "function": label(entry.code), "calls": entry.callcount,
        "recursive_calls": entry.reccallcount,
        "inclusive_wall_seconds": entry.totaltime,
        "exclusive_wall_seconds": entry.inlinetime,
        "children": [{"function": label(child.code), "calls": child.callcount,
                      "inclusive_wall_seconds": child.totaltime,
                      "exclusive_wall_seconds": child.inlinetime}
                     for child in entry.calls or []],
        "max_exclusive_time": "not_measured",
    } for entry in entries if not isinstance(entry.code, str)
        and ("apps/listings/" in entry.code.co_filename
             or "django/forms/" in entry.code.co_filename
             or "django/db/models/" in entry.code.co_filename)]
    native_rows.sort(key=lambda row: row["exclusive_wall_seconds"], reverse=True)
    record_property("dataset_published", 10000)
    record_property("rules", rows)
    record_property("native_call_stats", native_rows)
    record_property("control_request_seconds", control_wall)
    record_property("control_thread_cpu_seconds", control_cpu)
    record_property("profiled_request_seconds", measured_wall)
    record_property("profiled_thread_cpu_seconds", measured_cpu)
    record_property("scope", "RuleProfile synchronous wall/thread-CPU intervals: direct instrumented children discounted once; mean/max exclusive per rule. Added native model/exclusion/construct_instance/model_to_dict/text events, so exclusive times differ in scope from older profiles. Inline authority predicates still included in validate_submission, not separately measured or assumed invariant. Supplementary cProfile native call graph uses its own wall timer, includes recursion/call overhead and is not summed with RuleProfile. No locals, SQL, parameters or argument values recorded. Native per-call max/p95 not_measured; this call graph is supplemental, not the per-rule report.")
    record_property("overhead", "One sequential control then combined RuleProfile+cProfile sample, control response/context retained. Difference includes wrappers, native call tracer, host/PG/OS cache/retained objects; causal overhead not_measured, no correction applied. cProfile-inclusive/exclusive uses native call graph, not the selected-wrapper child graph. Results cannot be used as operational latency or compared as equal-instrumentation timing to earlier narrower profiles.")
    record_property("not_measured", "rows_returned/affected/scanned; DB CPU/waits/locks/IO; RSS/allocations; standalone inline authority predicate time; per-rule p95; causal profiler overhead; concurrent capacity")
