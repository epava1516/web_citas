"""Focalized rule events; no application changes or subtraction-based attribution."""

import time

import pytest
from django import forms
from django.db import connection
from django.db.models import JSONField, Model
from django.db.models import query as query_module
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, moderation, publication_state, submissions
from apps.listings.forms import ContactsForm, DetailsForm
from apps.listings.public_validation import PublicationContext, SnapshotChoice, SnapshotDetails
from scripts.benchmark_rule_profile import RuleProfile
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_discovery_rule_profile_10000(request, monkeypatch, record_property):
    # MOD-05: the listing is served from stored state; this profiles the native path.
    monkeypatch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
    client = request.getfixturevalue("directory")
    populate(10000)
    assert connection.vendor == "postgresql"
    # Equivalent operational route without the broad ORM profiler. Ordering is
    # recorded, not randomized: warmed OS/PG caches may bias the second request.
    control_cpu_start = time.thread_time()
    started = time.perf_counter()
    control = client.get("/es/")
    control_seconds = time.perf_counter() - started
    control_thread_cpu_seconds = time.thread_time() - control_cpu_start
    assert control.status_code == 200
    profile = RuleProfile(cpu_clock=time.thread_time)
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
        (query_module, "prefetch_one_level"),
    ]
    for cls in [SnapshotDetails, ContactsForm]:
        for method in ["__init__", "full_clean", "_clean_fields", "_clean_form", "_post_clean"]:
            if (cls, method) not in targets:
                targets.append((cls, method))
    for owner, name in targets:
        label = f"{getattr(owner, '__name__', str(owner))}.{name}"
        monkeypatch.setattr(owner, name, profile.wrap(label, getattr(owner, name)))

    original_json_conversion = JSONField.from_db_value

    def json_conversion(field, *args, **kwargs):
        # Model/field names only: never collect the JSON value or query parameters.
        label = f"json.{field.model._meta.label}.{field.name}"
        return profile.wrap(label, original_json_conversion)(field, *args, **kwargs)

    monkeypatch.setattr(JSONField, "from_db_value", json_conversion)

    original_from_db = Model.from_db.__func__

    def from_db(model_class, *args, **kwargs):
        label = f"from_db.{model_class._meta.label}"
        return profile.wrap(label, original_from_db)(model_class, *args, **kwargs)

    monkeypatch.setattr(Model, "from_db", classmethod(from_db))
    original_prefetch = query_module.prefetch_one_level.__wrapped__

    def relation_prefetch(instances, prefetcher, lookup, level):
        return profile.wrap(f"prefetch.{lookup.prefetch_to}", original_prefetch)(
            instances, prefetcher, lookup, level
        )

    monkeypatch.setattr(query_module, "prefetch_one_level", profile.wrap(
        "django.db.models.query.prefetch_one_level", relation_prefetch
    ))
    revision_model = DetailsForm._meta.model
    for relation in ["categories", "services", "travel_areas", "rates"]:
        manager_class = getattr(revision_model, relation).related_manager_cls
        for method in ["__init__", "_apply_rel_filters"]:
            monkeypatch.setattr(manager_class, method, profile.wrap(
                f"manager.{relation}.{method}", getattr(manager_class, method)
            ))

    def sql_event(execute, sql, params, many, context):
        return profile.wrap("sql.cursor_execute", execute)(sql, params, many, context)

    profile_cpu_start = time.thread_time()
    started = time.perf_counter()
    with connection.execute_wrapper(sql_event):
        response = client.get("/es/")
    measured_seconds = time.perf_counter() - started
    profile_thread_cpu_seconds = time.thread_time() - profile_cpu_start
    assert response.status_code == 200
    assert response.context["page"].paginator.count == 10000
    assert len(response.context["page"].object_list) == 24
    assert response["Cache-Control"] == "no-store"
    record_property("rules", profile.report())
    record_property("control_request_seconds", control_seconds)
    record_property("profiled_request_seconds", measured_seconds)
    record_property("control_thread_cpu_seconds", control_thread_cpu_seconds)
    record_property("profiled_thread_cpu_seconds", profile_thread_cpu_seconds)
    record_property("thread_cpu_scope", "time.thread_time: CPU user+system of this synchronous DjangoClient request thread only; excludes PostgreSQL/other processes and other threads, does not measure DB CPU or concurrent capacity. Direct-child CPU intervals subtracted once, independent of wall-clock subtraction; includes profiler overhead. Paired control/profiler CPU and wall observed, causal overhead not_measured; no retroactive CPU attribution to prior profiles.")
    record_property("overhead_comparison_seconds", measured_seconds - control_seconds)
    record_property("overhead", "Paired route without/with selected wrappers, sequential control then profile, one sample each. Difference includes instrumentation and uncontrolled PG/OS cache effects: causal overhead not_measured; no correction applied.")
    record_property("scope", "Synchronous request only; ContextVar nested stack; subtract direct instrumented child inclusive intervals once, never grandchildren again. Added prefetch by relation, manager construction/_apply_rel_filters and Model.from_db by model; earlier profile did not have these children and exclusive times are not directly comparable. from_db includes construction/state but not prior fetch/JSON conversion. exclusive_time is relative to observed children, includes uninstrumented Python/ORM work. Inline authorization/document/revocation conditions are included in validate_submission, not separately attributed. No arguments/parameters persisted; seconds, optional p95 not_measured. SQL execute may be nested inside forms/render/context; no total-minus-SQL validation attribution. publicly_visible imported alias in discovery is not separately observed; no missing event inferred as zero.")
    record_property("not_measured", "rows_returned/affected/scanned; CPU/RSS/waits/locks/IO; independent inline predicate timings; causal profiler overhead; concurrent capacity; p95 exclusive")
