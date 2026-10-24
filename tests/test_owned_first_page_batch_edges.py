"""Negative, scope, bound and snapshot controls for first-page batching."""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connections, transaction
from owned_first_page_batch import build_first_page_batch_prototype
from owned_state_page_before_batch import build_native_reference
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings import discovery, publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState, Rate, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def batch_case(request):
    client = request.getfixturevalue("directory")
    dataset = populate(80)
    target = Listing.objects.select_related("approved_revision", "person").get(
        pk=dataset["sample_ids"][1]
    )
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    counts = dict(batch_contexts=0, batch_sizes=[], page_reuses=0, missing_selected_fallbacks=0)
    proposed = build_first_page_batch_prototype(counts)
    return client, target, build_native_reference(), proposed, counts, dataset


def pair(client, native, proposed, monkeypatch, params=None):
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "_state_page", native)
        reference = client.get("/es/", params or {})
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "_state_page", proposed)
        candidate = client.get("/es/", params or {})
    assert candidate.status_code == reference.status_code == 200
    assert candidate.content == reference.content
    assert candidate["Cache-Control"] == reference["Cache-Control"] == "no-store"
    assert candidate.context["page"].paginator.count == reference.context["page"].paginator.count
    assert [row.pk for row in candidate.context["page"]] == [
        row.pk for row in reference.context["page"]
    ]
    return reference, candidate


def test_negative_authority_content_rate_and_normalization_keep_native_guard(
    batch_case,
    monkeypatch,
    record_property,
):
    client, target, native, proposed, counts, _ = batch_case
    revision = target.approved_revision
    assert not revision.rates.exists()
    base = {
        name: getattr(revision, name)
        for name in ["phone", "description", "telegram", "contact_exposure_accepted"]
    }
    manager_version = target.person.manager_version
    observed = []
    original_guard = proposed.__globals__["publicly_visible"]

    def guard(row, **kwargs):
        observed.append(row.pk)
        return original_guard(row, **kwargs)

    proposed.__globals__["publicly_visible"] = guard
    rows = []
    for case in [
        "phone",
        "description",
        "contact_consent",
        "forbidden_rate",
        "authority",
        "telegram_normalization",
    ]:
        Revision.objects.filter(pk=revision.pk).update(**base)
        Person.objects.filter(pk=target.person_id).update(manager_version=manager_version)
        Rate.objects.filter(revision=revision).delete()
        publication_state.refresh_all()
        if case == "phone":
            Revision.objects.filter(pk=revision.pk).update(phone="invalid")
        elif case == "description":
            Revision.objects.filter(pk=revision.pk).update(description="https://example.invalid")
        elif case == "contact_consent":
            Revision.objects.filter(pk=revision.pk).update(contact_exposure_accepted=False)
        elif case == "forbidden_rate":
            Rate.objects.bulk_create(
                [Rate(revision=revision, concept="https://example.invalid", mode="consult")]
            )
        elif case == "authority":
            Person.objects.filter(pk=target.person_id).update(manager_version=manager_version + 1)
        else:
            Revision.objects.filter(pk=revision.pk).update(telegram="@synthetic_user")
        marks = list(PublicationDirty.objects.values_list("pk", "generation"))
        assert len(marks) == 1 and marks[0][0] == target.pk
        observed.clear()
        before = counts["batch_contexts"]
        _, candidate = pair(client, native, proposed, monkeypatch)
        assert counts["batch_contexts"] == before + 1
        assert counts["page_reuses"] == counts["batch_contexts"]
        selected = list(candidate.context["page"])
        tally = Counter(observed)
        # One native pass decides the pending row; every selected row has its own guard.
        assert tally == Counter([target.pk] + [row.pk for row in selected])
        if case != "telegram_normalization":
            assert target.pk not in {row.pk for row in selected}
        else:
            assert (
                next(row.approved_revision.telegram for row in selected if row.pk == target.pk)
                == "synthetic_user"
            )
        assert list(PublicationDirty.objects.values_list("pk", "generation")) == marks
        rows.append(
            dict(
                case=case,
                native_guard_calls=len(observed),
                page_count=candidate.context["page"].paginator.count,
            )
        )
    record_property("batch_negative_native_guards", rows)


@pytest.mark.parametrize("pending", [1, 24, 48, 49])
def test_batch_bound_and_native_unknown_limit(batch_case, monkeypatch, record_property, pending):
    client, _, native, proposed, counts, dataset = batch_case
    ids = list(
        Listing.objects.filter(status="published")
        .order_by("pk")
        .values_list("pk", flat=True)[:pending]
    )
    assert len(ids) == pending
    publication_state.mark(ids)
    marks = list(PublicationDirty.objects.values_list("pk", "generation"))
    assert len(marks) == pending
    pair(client, native, proposed, monkeypatch)
    assert counts["batch_contexts"] == counts["page_reuses"] == 1
    assert counts["batch_sizes"] == [pending + 24]
    if pending == 49:
        observation = {}
        with transaction.atomic():
            assert (
                publication_state.state_page(discovery.candidates({}), 1, observation=observation)
                is None
            )
        assert observation["reason"] == "state_unknown_over_limit"
        observation = {}
        assert (
            publication_state.state_page(discovery.candidates({}).all(), 1, observation=observation)
            is None
        )
        assert observation["reason"] == "state_unknown_over_limit"

    assert list(PublicationDirty.objects.values_list("pk", "generation")) == marks
    record_property("pending_boundary", dict(pending=pending, counters=counts))


def test_scope_bypasses_and_missing_preview_fallback(batch_case, monkeypatch, record_property):
    client, target, native, proposed, counts, _ = batch_case
    publication_state.mark([target.pk])
    # The exact query protocol is required; clones and filters lose it.
    for query in [
        discovery.candidates({}).all(),
        discovery.candidates({}, stored_search=False),
        discovery.candidates({"profile": ["woman"]}),
        discovery.candidates({"available": True}),
    ]:
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, "_state_page", proposed)
            assert publication_state.state_page(query, 1) is not None
        assert counts["batch_contexts"] == 0
    pair(client, native, proposed, monkeypatch, {"checked": ["age"]})
    pair(client, native, proposed, monkeypatch, {"page": 2})
    with transaction.atomic():
        pair(client, native, proposed, monkeypatch)
    assert counts["batch_contexts"] == 0
    PublicationState.objects.filter(pk=target.pk).update(rules_version="obsolete-batch-control")
    pair(client, native, proposed, monkeypatch)
    assert counts["batch_contexts"] == 0
    PublicationState.objects.filter(pk=target.pk).delete()
    pair(client, native, proposed, monkeypatch)
    assert counts["batch_contexts"] == 0
    publication_state.mark_stale()
    publication_state.refresh_all()
    publication_state.mark([target.pk])
    for name in ["DIRTY_LIMIT", "NATIVE_UNKNOWN_LIMIT"]:
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, name, 0)
            patch.setitem(proposed.__globals__, name, 0)
            if name == "NATIVE_UNKNOWN_LIMIT":
                # Zero still rejects unknown rows in inherited READ COMMITTED.
                with transaction.atomic():
                    pair(client, native, proposed, monkeypatch)
            else:
                pair(client, native, proposed, monkeypatch)
        assert counts["batch_contexts"] == 0
    # Force an incomplete preview without weakening production selection or the guard.
    proposed.__globals__["_owned_clean_preview"] = lambda query, dirty: []
    pair(client, native, proposed, monkeypatch)
    assert counts["batch_contexts"] == 1 and counts["page_reuses"] == 0
    assert counts["missing_selected_fallbacks"] == 1
    record_property("scope_and_fallback", counts)


@pytest.mark.parametrize("victim_kind", ["pending", "clean_preview"])
def test_committed_change_after_preview_keeps_snapshot_then_denies_fresh_request(
    batch_case,
    monkeypatch,
    record_property,
    victim_kind,
):
    client, target, native, proposed, counts, _ = batch_case
    publication_state.mark([target.pk])
    reference = client.get("/es/")
    count = reference.context["page"].paginator.count
    preview = proposed.__globals__["_owned_clean_preview"]
    changed = []

    def writer(listing_id):
        try:
            row = Listing.objects.only("approved_revision_id").get(pk=listing_id)
            assert Revision.objects.filter(pk=row.approved_revision_id).update(phone="invalid") == 1
        finally:
            connections.close_all()

    def after_preview(query, dirty):
        ids = preview(query, dirty)
        if not changed:
            victim = target.pk if victim_kind == "pending" else ids[0]
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(writer, victim).result(timeout=15)
            changed.append(victim)
        return ids

    proposed.__globals__["_owned_clean_preview"] = after_preview
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "_state_page", proposed)
        old_snapshot = client.get("/es/")
        assert changed and old_snapshot.content == reference.content
        assert old_snapshot.context["page"].paginator.count == count
        fresh = client.get("/es/")
    assert fresh.status_code == 200 and fresh.context["page"].paginator.count == count - 1
    assert changed[0] not in {row.pk for row in fresh.context["page"]}
    assert PublicationDirty.objects.filter(pk=changed[0]).exists()
    assert counts["batch_contexts"] == counts["page_reuses"] == 2
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, "_state_page", native)
        expected = client.get("/es/")
    assert fresh.content == expected.content
    record_property("snapshot_change", dict(victim_kind=victim_kind, counters=counts))


def test_stale_clean_state_still_fails_native_page_guard(batch_case, monkeypatch, record_property):
    client, target, native, proposed, counts, dataset = batch_case
    victim = Listing.objects.get(pk=dataset["sample_ids"][2])
    Revision.objects.filter(pk=victim.approved_revision_id).update(phone="invalid")
    publication_state.mark([target.pk])
    bodies = []
    for implementation in [native, proposed]:
        PublicationDirty.objects.filter(pk=victim.pk).delete()  # Simulated missing invalidation.
        with monkeypatch.context() as patch:
            patch.setattr(publication_state, "_state_page", implementation)
            response = client.get("/es/")
        assert response.status_code == 200
        assert response.wsgi_request._publication_route["reason"] == "state_page_guard_changed"
        assert PublicationDirty.objects.filter(pk=victim.pk).exists()
        assert victim.pk not in {row.pk for row in response.context["page"]}
        bodies.append(response.content)
    assert bodies[0] == bodies[1]
    assert counts["batch_contexts"] == 1
    record_property("stale_guard", counts)
