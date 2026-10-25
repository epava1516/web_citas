"""Finite maintained discovery stage diagnosis; explicit owned serial execution only."""

import hashlib
import json
import math
import os
import resource
import runpy
import statistics
import time
from collections import Counter, defaultdict
from datetime import UTC
from decimal import Decimal
from functools import wraps
from pathlib import Path

import pytest
from capacity_runtime_role import _owned_database
from django.db import connection
from django.db.models.query import ModelIterable
from django.db.models.signals import post_init
from django.utils import timezone, translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_paged_equivalence import grant
from test_publication_state_matrix import prepare_population

from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
from apps.listings import (
    discovery,
    moderation,
    moderation_views,
    public_validation,
    publication_state,
    submissions,
)
from apps.listings.forms import ContactsForm, DetailsForm
from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.presentation_reads import PagePresentation
from apps.listings.public_validation import PublicationContext
from config.celery import app as celery_app

pytestmark = pytest.mark.django_db(transaction=True)
REFERENCE_SHA = "9f700b72394edbc8aac1a671081885b66c1754ed97f6c012a9f802bc45337c29"
PRIVATE_SENTINEL = "n04b_private_pending_sentinel_3187"


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, allow_nan=False,
                                     separators=(",", ":")).encode()).hexdigest()


def _current():
    publication_state.refresh_all()
    assert publication_state.all_state_current() and not PublicationDirty.objects.exists()


def _business():
    # Local comparison only; no raw editorial/contact fields enter the report.
    return {"listing": list(Listing.objects.order_by("pk").values()),
            "revision": list(Revision.objects.order_by("pk").values())}


def _native_population():
    # Context hydration requires an approved revision; null pointers are
    # rejected independently by the native guard, never silently omitted.
    null_rows = list(Listing.objects.filter(approved_revision__isnull=True))
    assert null_rows and all(not moderation.publicly_visible(row) for row in null_rows)
    context = PublicationContext(Listing.objects.filter(approved_revision__isnull=False), page_read=True)
    return {row.pk for row in context.rows if moderation.publicly_visible(row, context=context)}


def _native_expected(params, language, manual_ids, native_ranked):
    form = discovery.SearchForm(params, english=language == "en")
    assert form.is_valid()
    with translation.override(language):
        context = PublicationContext(discovery.candidates(form.cleaned_data), page_read=True)
        visible = [row for row in context.rows if moderation.publicly_visible(row, context=context)]
        assert {row.pk for row in visible} == manual_ids
        expected, labels = native_ranked(visible, text_search=bool(params.get("q")))
    assert {row.pk for row in expected} == manual_ids and len(expected) == len(manual_ids)
    return [row.pk for row in expected], labels


def _assert_response(response, language, expected_ids, labels, total=None, *, detail=False):
    assert response.status_code == 200 and response["Cache-Control"] == "no-store"
    assert f'lang="{language}"'.encode() in response.content
    assert PRIVATE_SENTINEL.encode() not in response.content
    assert b"fixture-model-b@example.invalid" not in response.content
    if detail:
        actual = [response.context["listing"].pk]
    else:
        page = response.context["page"]
        actual = [row.pk for row in page.object_list]
        assert page.paginator.count == total
        assert response.wsgi_request._publication_route["route"] == "state"
        actual_labels = {card["listing"].pk: card["sponsorship"]
                         for card in response.context["cards"] if card["sponsorship"]}
        assert actual_labels == {pk: labels[pk] for pk in actual if pk in labels}
    assert actual == expected_ids
    return {"returned_count": len(actual), "ordered_ids_sha256": _digest(actual),
            "sponsor_labels_sha256": _digest([(str(pk), labels.get(pk)) for pk in actual])}


def _sample(client, path, params, monkeypatch):
    stages = defaultdict(lambda: {"calls": 0, "wall_seconds": 0.0, "thread_cpu_seconds": 0.0})
    models = Counter()
    sql = {"calls": 0, "execute_seconds": 0.0}

    def wrapped(label, function):
        @wraps(function)
        def measured(*args, **kwargs):
            started, cpu = time.perf_counter(), time.thread_time()
            try:
                return function(*args, **kwargs)
            finally:
                stage = stages[label]
                stage["calls"] += 1
                stage["wall_seconds"] += time.perf_counter() - started
                stage["thread_cpu_seconds"] += time.thread_time() - cpu
        return measured

    original_iteration = ModelIterable.__iter__

    def hydration(instance):
        iterator = iter(original_iteration(instance))
        stage = stages["model_iterable"]
        stage["calls"] += 1
        while True:
            started, cpu = time.perf_counter(), time.thread_time()
            try:
                row = next(iterator)
            except StopIteration:
                return
            finally:
                stage["wall_seconds"] += time.perf_counter() - started
                stage["thread_cpu_seconds"] += time.thread_time() - cpu
            stage["objects"] = stage.get("objects", 0) + 1
            yield row

    def instantiated(sender, **kwargs):
        if sender._meta.app_label in {"listings", "core", "catalog", "safety", "mediafiles"}:
            models[sender._meta.label] += 1

    def query(execute, statement, values, many, context):
        sql["calls"] += 1
        start = time.perf_counter()
        try:
            return execute(statement, values, many, context)
        finally:
            sql["execute_seconds"] += time.perf_counter() - start

    targets = [
        (PublicationContext, "__init__", "publication_context"),
        (PagePresentation, "__init__", "presentation_init"),
        (PagePresentation, "describe", "presentation_describe"),
        (PagePresentation, "photo", "presentation_photo"),
        (discovery, "render", "discovery_render"),
        (moderation_views, "render", "detail_render"),
        (discovery, "publicly_visible", "discovery_guard_alias"),
        (moderation_views, "publicly_visible", "detail_guard_alias"),
        (moderation, "publicly_visible", "native_guard"),
        (publication_state, "publicly_visible", "state_guard_alias"),
        (submissions, "validate_submission", "submissions_validate_submission"),
        (publication_state, "validate_submission", "state_validate_submission"),
        (moderation, "validate_submission", "moderation_validate_submission"),
        (submissions, "publication_ready", "publication_ready"),
        (public_validation, "validate_publication_binding", "validation_binding"),
        (DetailsForm, "full_clean", "details_full_clean"),
        (ContactsForm, "full_clean", "contacts_full_clean"),
    ]
    for _, _, label in targets:
        stages[label]  # Report genuine zero calls explicitly.
    with monkeypatch.context() as patch:
        patch.setattr(ModelIterable, "__iter__", hydration)
        for owner, name, label in targets:
            patch.setattr(owner, name, wrapped(label, getattr(owner, name)))
        post_init.connect(instantiated, weak=False)
        try:
            started, cpu = time.perf_counter(), time.thread_time()
            with connection.execute_wrapper(query):
                response = client.get(path, params)
            wall, thread_cpu = time.perf_counter() - started, time.thread_time() - cpu
        finally:
            post_init.disconnect(instantiated)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert rss < 1024 * 1024
    values = [wall, thread_cpu, sql["execute_seconds"],
              *[value for stage in stages.values() for value in stage.values()]]
    assert all(math.isfinite(value) and value >= 0 for value in values)
    return response, {"request_wall_seconds": wall, "request_thread_cpu_seconds": thread_cpu,
                      "sql": sql, "stages": dict(stages), "model_post_init": dict(models),
                      "process_maxrss_kib": rss}


def test_maintained_discovery_stages(request, settings, monkeypatch, record_property):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned serial maintained-discovery diagnosis only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert request.config.pluginmanager.hasplugin("scripts.local_ci_broker")
    generation = request.getfixturevalue("isolated_test_broker")
    assert generation == os.environ["LOCAL_CI_TEST_QUEUE_GENERATION"] == settings.TASK_QUEUE_GENERATION
    _owned_database()
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert settings.MEDIA_STORAGE_PROVIDER == "local" and not settings.RIGHTS_OBJECT_STORAGE_ENABLED
    client = request.getfixturevalue("directory")
    settings.CELERY_TASK_ALWAYS_EAGER = False
    assert celery_app.conf.task_always_eager is False
    settings.PROMOTION_TEST_MODE = False
    prepare_population(120, "diverse")
    cohort = list(Listing.objects.filter(status="published").select_related(
        "approved_revision", "person__individual", "person__agency__owner").order_by("pk"))
    assert len(cohort) == 120
    women = {row.pk for row in cohort[::2]}
    men = {row.pk for row in cohort[1::2]}
    assert len(women) == len(men) == 60
    revisions = []
    for index, row in enumerate(cohort):
        row.approved_revision.profile_type = "woman" if index % 2 == 0 else "man"
        row.approved_revision.spoken_languages = ["en"] if index % 2 == 0 else ["fr"]
        revisions.append(row.approved_revision)
    Revision.objects.bulk_update(revisions, ["profile_type", "spoken_languages"])
    private = Revision.objects.filter(listing__approved_revision__isnull=True).first()
    assert private is not None
    Revision.objects.filter(pk=private.pk).update(title=PRIVATE_SENTINEL, description=PRIVATE_SENTINEL)
    _current()
    # Independent native authority for every public row and every nonpublic row,
    # outside request clocks; no state projection output serves as its own oracle.
    assert _native_population() == women | men
    assert all("photography" in row.approved_revision.description.lower() for row in cohort)
    reference = settings.BASE_DIR / "docs/evidencias/b08-promociones-referencia-20261020.py"
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == REFERENCE_SHA
    native_ranked = runpy.run_path(str(reference), run_name="apps.catalog._n04b_frozen_reference")["ranked"]
    editorial = _business()
    cohort_sha = _digest([
        {"listing": row.pk, "revision": row.approved_revision_id,
         "type": row.approved_revision.profile_type, "language": row.approved_revision.spoken_languages,
         "description": row.approved_revision.description} for row in cohort])
    day = timezone.now().astimezone(UTC).date()
    observations, coverage, promotion_cache_checks = [], [], []
    for phase in ["organic", "synthetic_promoted"]:
        if phase == "synthetic_promoted":
            settings.PROMOTION_TEST_MODE = True
            for kind, chosen in [("premium", cohort[:8]), ("top", cohort[8:24])]:
                version = PromotionProductVersion.objects.create(
                    product=PromotionProduct.objects.create(slug="n04b_" + kind, kind=kind),
                    version=1, name_es="Prueba", name_en="Test", duration_days=10,
                    amount=Decimal("12.00"), currency="EUR", tax_rate=Decimal("20"),
                    published_at=timezone.now(), is_current=True)
                for row in chosen:
                    entitlement = grant(row.person, version)  # create_order + signed synthetic event + receive_event.
                    cached_status = entitlement.order.status
                    persisted_order = PromotionOrder.objects.get(pk=entitlement.order_id)
                    assert persisted_order.synthetic and persisted_order.status == "paid"
                    promotion_cache_checks.append({"kind": kind, "cached_status": cached_status,
                                                   "persisted_status": persisted_order.status})
            assert PromotionEntitlement.objects.count() == 24
            assert PromotionOrder.objects.filter(kind="premium", synthetic=True, status="paid").count() == 8
            assert PromotionOrder.objects.filter(kind="top", synthetic=True, status="paid").count() == 16
            _current()
            assert _business() == editorial
        else:
            assert not PromotionEntitlement.objects.exists()
        commercial_before = list(PromotionEntitlement.objects.order_by("pk").values())
        state_before = list(publication_state.PublicationState.objects.order_by("listing_id").values())
        for language in ["es", "en"]:
            combined = {"q": "photography", "profile": ["woman"], "language": ["en"]}
            empty = {"q": "photography", "profile": ["woman"], "language": ["fr"]}
            oracle = {}
            for name, params, manual in [("all", {}, women | men), ("combined", combined, women),
                                         ("empty", empty, set())]:
                expected, labels = _native_expected(params, language, manual, native_ranked)
                oracle[name] = (expected, labels)
                all_ids = []
                for page in range(1, max(1, math.ceil(len(expected) / 24)) + 1):
                    response = client.get(f"/{language}/", {**params, "page": str(page)})
                    _assert_response(response, language, expected[(page - 1) * 24:page * 24], labels, len(expected))
                    all_ids.extend(row.pk for row in response.context["page"].object_list)
                assert all_ids == expected and len(all_ids) == len(set(all_ids))
                coverage.append({"phase": phase, "language": language, "segment": name,
                                 "count": len(expected), "ordered_ids_sha256": _digest(expected)})
            all_ids, all_labels = oracle["all"]
            selected, selected_labels = oracle["combined"]
            empty_ids, empty_labels = oracle["empty"]
            cases = [
                ("page1", {}, all_ids[:24], all_labels, 120),
                ("last_page5", {"page": "5"}, all_ids[96:120], all_labels, 120),
                ("combined_page1", combined, selected[:24], selected_labels, 60),
                ("combined_last_page3", {**combined, "page": "3"}, selected[48:60], selected_labels, 60),
                ("empty_combined", empty, empty_ids, empty_labels, 0),
                ("detail", {}, [cohort[0].pk], {}, None),
            ]
            for name, params, expected, labels, total in cases:
                detail = name == "detail"
                path = f"/{language}/listing/{cohort[0].pk}/" if detail else f"/{language}/"
                samples = []
                for ordinal in range(6):
                    response, sample = _sample(client, path, params, monkeypatch)
                    sample.update(_assert_response(response, language, expected, labels, total, detail=detail))
                    assert sample["stages"]["detail_render" if detail else "discovery_render"]["calls"] == 1
                    if detail:
                        assert sample["stages"]["detail_guard_alias"]["calls"] == 1
                    else:
                        assert sample["stages"]["presentation_init"]["calls"] == 1
                    sample.update(ordinal=ordinal + 1, position="first_instrumented" if ordinal == 0 else "later",
                                  route="detail_native_snapshot_guard" if detail else response.wsgi_request._publication_route)
                    samples.append(sample)
                later = [sample["request_wall_seconds"] for sample in samples[1:]]
                observations.append({"phase": phase, "language": language, "segment": name,
                                     "expected_total": total, "samples": samples,
                                     "later_median_seconds": statistics.median(later),
                                     "later_range_seconds": [min(later), max(later)]})
        assert _business() == editorial
        assert commercial_before == list(PromotionEntitlement.objects.order_by("pk").values())
        assert state_before == list(publication_state.PublicationState.objects.order_by("listing_id").values())
        assert publication_state.all_state_current() and not PublicationDirty.objects.exists()
        assert _native_population() == women | men
    assert timezone.now().astimezone(UTC).date() == day, "UTC promotion rotation day changed during finite protocol"
    assert len(observations) == 24 and sum(len(row["samples"]) for row in observations) == 144
    report = {"version": "n04b-maintained-stages-v1", "cohort_sha256": cohort_sha,
              "published": 120, "women_en": 60, "men_fr": 60, "promoted": 24,
              "premium": 8, "top": 16, "promotion_cache_checks": promotion_cache_checks,
              "reference_sha256": REFERENCE_SHA,
              "measured_requests": 144, "coverage": coverage, "observations": observations,
              "limits": "Current maintained state baseline, no app change or speedup/p95/capacity/provider/TCP claim. All pages checked before six instrumented first-plus-five requests; first is not OS cold. Synthetic promotion orders/events only, no payments. Native authority/manual membership/frozen ranking are outside clocks. Stage wrappers delegate real execution, never replace guards/state_page. SQL execute, ModelIterable next hydration, context, validation, presentation and render are inclusive/nested: never sum them or infer SQL server CPU. post_init counts actual model construction. RSS is Linux process cumulative high-water KiB. Private fixture identifiers/fields appear only in local oracles or hashes, never raw report. Commercial UTC day held by validity assertion, no clock patch."}
    record_property("n04b_maintained_stages", json.dumps(report, sort_keys=True, allow_nan=False))
