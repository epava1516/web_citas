"""Focalized rule events; no application changes or subtraction-based attribution."""

import time

import pytest
from django import forms
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, moderation, submissions
from apps.listings.forms import ContactsForm, DetailsForm
from apps.listings.public_validation import PublicationContext, SnapshotChoice, SnapshotDetails
from scripts.benchmark_rule_profile import RuleProfile
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_discovery_rule_profile_10000(request, monkeypatch, record_property):
    client = request.getfixturevalue("directory")
    populate(10000)
    assert connection.vendor == "postgresql"
    # Equivalent operational route without the broad ORM profiler. Ordering is
    # recorded, not randomized: warmed OS/PG caches may bias the second request.
    started = time.perf_counter()
    control = client.get("/es/")
    control_seconds = time.perf_counter() - started
    assert control.status_code == 200
    profile = RuleProfile()
    targets = [
        (moderation, "validate_submission"),
        (moderation, "publicly_visible"),
        (submissions, "publication_ready"),
        (discovery, "render"),
        (PublicationContext, "__init__"),
        (PublicationContext, "details"),
        (PublicationContext, "rate_valid"),
        (SnapshotDetails, "__init__"),
        (DetailsForm, "__init__"),
        (forms.BaseForm, "__init__"),
        (SnapshotChoice, "__deepcopy__"),
    ]
    for cls in [SnapshotDetails, ContactsForm]:
        for method in ["__init__", "full_clean", "_clean_fields", "_clean_form", "_post_clean"]:
            if (cls, method) not in targets:
                targets.append((cls, method))
    for owner, name in targets:
        label = f"{getattr(owner, '__name__', str(owner))}.{name}"
        monkeypatch.setattr(owner, name, profile.wrap(label, getattr(owner, name)))

    def sql_event(execute, sql, params, many, context):
        return profile.wrap("sql.cursor_execute", execute)(sql, params, many, context)

    started = time.perf_counter()
    with connection.execute_wrapper(sql_event):
        response = client.get("/es/")
    measured_seconds = time.perf_counter() - started
    assert response.status_code == 200
    assert response.context["page"].paginator.count == 10000
    assert len(response.context["page"].object_list) == 24
    assert response["Cache-Control"] == "no-store"
    record_property("rules", profile.report())
    record_property("control_request_seconds", control_seconds)
    record_property("profiled_request_seconds", measured_seconds)
    record_property("overhead_comparison_seconds", measured_seconds - control_seconds)
    record_property("overhead", "Paired route without/with selected wrappers, sequential control then profile, one sample each. Difference includes instrumentation and uncontrolled PG/OS cache effects: causal overhead not_measured; no correction applied.")
    record_property("scope", "Synchronous request only; ContextVar nested stack; subtract direct instrumented child inclusive intervals once, never grandchildren again. exclusive_time is relative to observed children, includes uninstrumented Python/ORM work. Inline authorization/document/revocation conditions are included in validate_submission, not separately attributed. No arguments/parameters persisted; seconds, optional p95 not_measured. SQL execute may be nested inside forms/render/context; no total-minus-SQL validation attribution.")
    record_property("not_measured", "rows_returned/affected/scanned; CPU/RSS/waits/locks/IO; independent inline predicate timings; causal profiler overhead; concurrent capacity; p95 exclusive")
