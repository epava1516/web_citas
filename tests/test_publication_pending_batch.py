"""Bounded pending-state selection: native equivalence and authority boundaries."""

import hashlib
import math
from concurrent.futures import ThreadPoolExecutor

import pytest
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


def test_pending_batch_preserves_pages_guards_and_concurrent_authority(request, settings, monkeypatch, record_property):
    _, marked = prepare(request, settings, 100)
    client = request.getfixturevalue("directory")
    gold = {}
    for route, path in ROUTES:
        ids = []
        for page in range(1, 6):
            location = path + ("&" if "?" in path else "?") + f"page={page}"
            with monkeypatch.context() as patch:
                patch.setattr(publication_state, "state_page", lambda *args, **kwargs: None)
                expected, _ = response_signature(client, location)
            actual, proposed_route = response_signature(client, location)
            assert actual == expected
            assert proposed_route["route"] == "state"
            assert proposed_route["reason"] == "trusted_state_extended_unknown"
            assert proposed_route["native_unknown"] == 49
            ids.extend(actual[2])
            if page == 1:
                gold[route] = actual
        assert len(ids) == len(set(ids)) == 100
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
    # Exercise the exact ceiling with real persisted rows and no truncation.
    # Production constants remain 48/1000; only this scoped boundary is reduced.
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "DIRTY_LIMIT", 48)
        actual, route = response_signature(client, "/es/")
        assert actual == gold["directory_es"]
        assert route["route"] == "fallback" and route["reason"] == "state_dirty_over_limit"
    assert publication_state.DIRTY_LIMIT == 1000
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
    native_census = publication_state.all_state_current
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

    monkeypatch.setattr(publication_state, "all_state_current", census)
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
    record_property("pending_snapshot_boundary", {
        "source": "Integrated product, independent complete native reference",
        "all_pages_es_en": True, "inherited_rc_clone_incomplete_census_fallback": True,
        "pending_ceiling_no_truncation": True, "own_rr_readonly_concurrent_snapshot": True,
        "fresh_next_request_personal_consent_and_commercial_buyer": True,
    })
