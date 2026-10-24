"""Explicit bounded native-stage candidate: safety first, then finite A/A/C."""

import gc
import hashlib
import json
import math
import os
import subprocess
import time
import tracemalloc
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC

import pytest
from beta_balanced_reader import balanced_reads
from beta_extended_unknown_candidate import extended_unknown_candidate
from beta_promotional_load_fixture import prepare_promotional_load
from django.db import connection, connections, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, public_validation, publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)
ROUTES = [("directory_es", "/es/"), ("search_en", "/en/?q=synthetic")]


def prepare(request, settings, count):
    assert connection.vendor == "postgresql" and not settings.PRODUCTION
    assert not publication_state.READ_REPAIR and not celery_app.conf.task_always_eager
    assert publication_state.NATIVE_UNKNOWN_LIMIT == 48 and publication_state.DIRTY_LIMIT == 1000
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, count)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    form = discovery.SearchForm({"q": "synthetic"})
    assert form.is_valid()
    marked = list(discovery.candidates(form.cleaned_data).values_list("pk", flat=True)[:49])
    assert len(marked) == 49
    publication_state.mark(marked)
    assert PublicationDirty.objects.count() == 49
    return dataset, marked


def response_signature(client, path):
    response = client.get(path)
    assert response.status_code == 200 and response["Cache-Control"] == "no-store"
    page = response.context["page"]
    signature = (hashlib.sha256(response.content).hexdigest(), page.paginator.count,
                 tuple(str(row.pk) for row in page.object_list),
                 tuple(card["sponsorship"] for card in response.context["cards"]))
    return signature, dict(response.wsgi_request._publication_route)


def install(monkeypatch):
    original, candidate, metadata = extended_unknown_candidate()
    chosen = {"function": original, "arm": "A"}

    def dispatch(*args, **kwargs):
        return chosen["function"](*args, **kwargs)

    def set_arm(arm):
        chosen.update(function=candidate if arm == "C" else original, arm=arm)

    monkeypatch.setattr(publication_state, "_state_page", dispatch)
    return original, candidate, metadata, chosen, set_arm


def test_extended_unknown_small_safety(request, settings, monkeypatch, record_property):
    _, marked = prepare(request, settings, 100)
    client = request.getfixturevalue("directory")
    _, candidate, metadata, _, set_arm = install(monkeypatch)
    gold = {}
    for route, path in ROUTES:
        ids = []
        for page in range(1, 6):
            location = path + ("&" if "?" in path else "?") + f"page={page}"
            set_arm("A")
            expected, native_route = response_signature(client, location)
            assert native_route["route"] == "fallback" and native_route["reason"] == "state_unknown_over_limit"
            set_arm("C")
            actual, proposed_route = response_signature(client, location)
            assert actual == expected
            assert proposed_route["route"] == "state"
            assert proposed_route["reason"] == "trusted_state_extended_unknown"
            assert proposed_route["native_unknown"] == 49
            ids.extend(actual[2])
            if page == 1:
                gold[route] = actual
        assert len(ids) == len(set(ids)) == 100
    set_arm("C")
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SHOW transaction_isolation")
        assert cursor.fetchone()[0] == "read committed"
        actual, route = response_signature(client, "/es/")
        assert actual == gold["directory_es"]
        assert route["route"] == "fallback" and route["reason"] == "state_unknown_over_limit"
    form = discovery.SearchForm({})
    assert form.is_valid()
    cloned = discovery.candidates(form.cleaned_data).all()
    assert getattr(cloned, "_publication_state_population", None) is None
    observed = {}
    assert publication_state.state_page(cloned, 1, observation=observed) is None
    assert observed["reason"] == "state_unknown_over_limit"
    missing = Listing.objects.exclude(pk__in=marked).values_list("pk", flat=True).first()
    PublicationState.objects.filter(listing_id=missing).delete()
    actual, route = response_signature(client, "/es/")
    assert actual == gold["directory_es"] and route["route"] == "fallback"
    publication_state.mark_stale()
    publication_state.refresh_all()
    assert publication_state.all_state_current()
    publication_state.mark(marked)
    assert PublicationDirty.objects.count() == 49
    agency_listing = Listing.objects.filter(person__agency__isnull=False).select_related("person__agency__owner").first()
    owner = agency_listing.person.agency.owner
    person = agency_listing.person
    affected = {str(pk) for pk in Listing.objects.filter(person=person).values_list("pk", flat=True)}
    buyer_listings = {str(pk) for pk in Listing.objects.filter(person__agency__owner=owner).values_list("pk", flat=True)}
    native_census = candidate.__globals__["all_state_current"]
    revocations = []

    def revoke():
        try:
            type(owner).objects.filter(pk=owner.pk).update(is_active=False)
            type(person).objects.filter(pk=person.pk).update(consent_revoked_at=timezone.now())
        finally:
            connections.close_all()

    def census(*args, **kwargs):
        current = native_census(*args, **kwargs)
        if current and not revocations:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_setting('transaction_isolation'), current_setting('transaction_read_only')")
                assert cursor.fetchone() == ("repeatable read", "on")
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(revoke).result(timeout=10)
            revocations.append("Committed actor revocation after snapshot census")
        return current

    candidate.__globals__["all_state_current"] = census
    first, first_route = response_signature(client, "/es/")
    assert revocations and first[1:] == gold["directory_es"][1:]
    assert first_route["reason"] == "trusted_state_extended_unknown"
    # Independent complete native reference after the committed mutation.
    context = public_validation.PublicationContext(discovery.candidates(form.cleaned_data), page_read=True)
    visible = [row for row in context.rows if discovery.publicly_visible(row, context=context)]
    from apps.catalog.promotion_exposure import ranked

    expected, labels = ranked(visible)
    expected_ids = [str(row.pk) for row in expected]
    assert not affected.intersection(expected_ids)
    assert all(labels.get(row.pk) is None for row in expected if str(row.pk) in buyer_listings)
    next_ids = []
    for page in range(1, max(1, math.ceil(len(expected) / 24)) + 1):
        actual, _ = response_signature(client, f"/es/?page={page}")
        assert actual[1] == len(expected)
        assert list(actual[2]) == expected_ids[(page - 1) * 24:page * 24]
        assert list(actual[3]) == [labels.get(row.pk) for row in expected[(page - 1) * 24:page * 24]]
        next_ids.extend(actual[2])
    assert next_ids == expected_ids and not affected.intersection(next_ids)
    result = {"result": "SMALL_SAFETY_COMPLETE", "candidate": metadata,
              "count": 100, "initial_unknown": 49, "routes_all_pages": [name for name, _ in ROUTES],
              "inherited_read_committed_preserved": True, "cloned_query_declined": True,
              "incomplete_census_declined": True, "own_repeatable_read_read_only_verified": True,
              "concurrent_revocation_snapshot_then_fresh_next_request": True,
              "native_complete_after_revocation": True,
              "personal_consent_and_buyer_sponsorship_revoked": True, "capacity_acceptance": False}
    folder = settings.BASE_DIR / "artifacts/local-ci" / os.environ["LOCAL_CI_ISOLATED_BROKER_RUN"]
    (folder / "beta-extended-unknown-small.json").write_text(json.dumps(result, indent=2) + "\n")
    record_property("beta_extended_unknown_small_safety", result)


def test_extended_unknown_balanced_roi(request, settings, monkeypatch, record_property):
    started_day = timezone.now().astimezone(UTC).date()
    dataset, _ = prepare(request, settings, 1000)
    run_id = os.environ["LOCAL_CI_ISOLATED_BROKER_RUN"]
    folder = settings.BASE_DIR / "artifacts/local-ci" / run_id
    runner = json.loads((folder / "runner.json").read_text())
    inspection = json.loads(subprocess.check_output([
        "docker", "inspect", os.environ["LOCAL_CI_POSTGRES_CONTAINER"],
    ], text=True))[0]
    gc_policy = (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    assert gc_policy[0] and gc_policy[2] == 0
    client = request.getfixturevalue("directory")
    _, _, metadata, chosen, set_arm = install(monkeypatch)
    requests = 0

    def read(path):
        nonlocal requests
        requests += 1
        signature, route = response_signature(client, path)
        expected = ("state", "trusted_state_extended_unknown") if chosen["arm"] == "C" else (
            "fallback", "state_unknown_over_limit",
        )
        assert (route["route"], route["reason"]) == expected
        assert signature[1] == 1000 and len(signature[2]) <= 24
        return signature

    all_pages = {}
    for route, path in ROUTES:
        arms = {}
        for arm in "AC":
            set_arm(arm)
            arms[arm] = [read(path + ("&" if "?" in path else "?") + f"page={page}")
                         for page in range(1, math.ceil(1000 / 24) + 1)]
        assert arms["A"] == arms["C"]
        ids = [pk for signature in arms["C"] for pk in signature[2]]
        assert len(ids) == len(set(ids)) == 1000
        all_pages[route] = arms
    records, signatures, comparisons = balanced_reads(ROUTES, read, set_arm, runner, inspection)
    observations = []
    for route, path in ROUTES:
        for arm in "AC":
            set_arm(arm)
            contexts, executes, probes = [], [], []
            probing = {"active": False}
            original_init = public_validation.PublicationContext.__init__

            def context_init(context, *args, **kwargs):
                started = time.perf_counter()
                original_init(context, *args, **kwargs)
                elapsed = time.perf_counter() - started
                probing["active"] = True
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT current_setting('transaction_isolation'), current_setting('transaction_read_only')")
                        isolation, readonly = cursor.fetchone()
                finally:
                    probing["active"] = False
                probes.append(1)
                contexts.append({"rows": len(context.rows), "inclusive_seconds": elapsed,
                                 "isolation_after_constructor": isolation, "readonly_after_constructor": readonly})

            def execute(real_execute, sql, params, many, context):
                if probing["active"]:
                    return real_execute(sql, params, many, context)
                start = time.perf_counter()
                try:
                    return real_execute(sql, params, many, context)
                finally:
                    executes.append(time.perf_counter() - start)

            assert not tracemalloc.is_tracing()
            try:
                tracemalloc.start()
                start, cpu = time.perf_counter(), time.thread_time()
                with monkeypatch.context() as patch, connection.execute_wrapper(execute):
                    patch.setattr(public_validation.PublicationContext, "__init__", context_init)
                    assert read(path) == signatures[route]
                wall, used_cpu = time.perf_counter() - start, time.thread_time() - cpu
                retained, peak = tracemalloc.get_traced_memory()
            finally:
                tracemalloc.stop()
            if arm == "A":
                assert [c["rows"] for c in contexts] == [1000, 200]
            else:
                assert contexts and sum(c["rows"] for c in contexts) <= 97
                assert all((c["isolation_after_constructor"], c["readonly_after_constructor"]) == (
                    "repeatable read", "on",
                ) for c in contexts)
            observations.append({"route": route, "arm": arm, "contexts": contexts,
                                 "execute_calls_excluding_probes": len(executes),
                                 "execute_seconds_excluding_probes": sum(executes),
                                 "mode_probes": len(probes), "observed_wall_seconds": wall,
                                 "observed_thread_cpu_seconds": used_cpu,
                                 "python_peak_bytes": peak, "python_retained_bytes": retained})
    assert timezone.now().astimezone(UTC).date() == started_day
    assert requests == 316 and PublicationDirty.objects.count() == 49
    assert gc_policy == (gc.isenabled(), gc.get_threshold(), gc.get_debug())
    result = {"result": "EXPERIMENT_COMPLETE", "run_id": run_id, "candidate": metadata,
              "count": dataset["published"], "rights": dataset["promotions"]["count"],
              "requests": requests, "all_pages_reads": 168, "warm_reads": 36,
              "measured_reads": 108, "observed_reads": 4, "all_pages": all_pages,
              "route_signatures": signatures, "records": records, "comparisons": comparisons,
              "observations": observations, "eligible": all(c["eligible"] for c in comparisons.values()),
              "gc_policy_unchanged": gc_policy,
              "limits": ["Candidate only: second stage under own RR/read-only, current census and canonical candidates",
                         "Threshold48 triggers a bounded full-pending stage; cap1000/fallback remain, no truncated results",
                         "Full native unknown checks and selected-page guard, commercial rules and inherited path unchanged",
                         "Two routes/all42pages A/C byte/IDs/count/labels parity; separate108balanced controls",
                         "App thread and exact owned PG backend CPU; GC normal, no profiler/SQL hooks in controls",
                         "Four observations only: contexts/mode probes/execute/tracemalloc; probes excluded from execute counts",
                         "Execute omits server cursor FETCH; inclusive times overlap; Python peak not RSS",
                         "No10k/TCP/capacity/global beta acceptance; pytestPASS means integrity, eligiblefalse rejects"]}
    (folder / "beta-extended-unknown-roi.json").write_text(json.dumps(result, indent=2) + "\n")
    record_property("beta_extended_unknown_eligible", result["eligible"])
