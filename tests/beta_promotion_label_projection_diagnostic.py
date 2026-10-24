"""Experimental label projection; filter, authority and rank remain unchanged."""

import hashlib
import inspect
from pathlib import Path

import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_paged_equivalence import (
    test_all_pages_match_frozen_native_with_overlapping_rights as assert_native_pages,
)
from test_promotion_paged_equivalence import (
    test_commercial_revocation_is_fresh_in_sql_and_batch as assert_revocation,
)
from test_promotion_snapshot_ordering import (
    test_inherited_read_committed_does_not_reuse_a_rights_map as assert_inherited,
)
from test_promotion_snapshot_ordering import (
    test_positive_checked_filter_with_promotions_and_delayed_refresh as assert_checked,
)
from test_promotion_snapshot_ordering import (
    test_snapshot_map_does_not_survive_next_request as assert_snapshot,
)

from apps.catalog import promotion_paging
from apps.listings import publication_state

pytestmark = pytest.mark.django_db(transaction=True)


def label_projection_candidate():
    source_sha = hashlib.sha256(Path(promotion_paging.__file__).read_bytes()).hexdigest()
    page_sha = hashlib.sha256(Path(publication_state.__file__).read_bytes()).hexdigest()
    assert source_sha == "79665c4cd351f668f4f8378ead3ce514b6fdd6491f737e1b6c8294b31913009e"
    assert page_sha == "282f88e5af3c3f49f618aaf9bf3c5949e0d038f7699bfe6ca79ac880998703c6"
    source = inspect.getsource(promotion_paging._snapshot_order_population)
    needle = '    return query.order_by("_promotion_position", *query.query.order_by)'
    assert source.count(needle) == 1
    ranking = source.replace(needle, '\n'.join([
        '    ordered = query.order_by("_promotion_position", *query.query.order_by)',
        '    ordered._publication_sponsorship = promotions',
        '    return ordered',
    ]))
    page_source = inspect.getsource(publication_state._state_page)
    old_block = '\n'.join([
        '        page = Paginator(population.values_list(identifier, "_promotion_priority"), 24).page(number)',
        '        selected_rights = list(page.object_list)',
        '        selected = [pk for pk, _ in selected_rights]',
        '        page.sponsorship = {',
        '            pk: ("premium" if priority == 0 else "top")',
        '            for pk, priority in selected_rights if priority < 2',
        '        }',
    ])
    assert page_source.count(old_block) == 1
    flat = '\n'.join([
        '        snapshot_sponsorship = (',
        '            getattr(population, "_publication_sponsorship", None) if trusted_snapshot else None',
        '        )',
        '        if snapshot_sponsorship is not None:',
        '            page = Paginator(population.values_list(identifier, flat=True), 24).page(number)',
        '            selected = list(page.object_list)',
        '            page.sponsorship = {',
        '                pk: snapshot_sponsorship[pk] for pk in selected if pk in snapshot_sponsorship',
        '            }',
        '        else:',
    ])
    page = page_source.replace(old_block, flat + '\n' + '\n'.join('    ' + line for line in old_block.splitlines()))
    ranking_namespace = vars(promotion_paging).copy()
    page_namespace = vars(publication_state).copy()
    exec(compile(ranking, "<beta-label-ranking-candidate>", "exec"), ranking_namespace)
    exec(compile(page, "<beta-label-page-candidate>", "exec"), page_namespace)
    return (ranking_namespace["_snapshot_order_population"], page_namespace["_state_page"],
            {"ranking": source_sha, "page": page_sha},
            hashlib.sha256((ranking + "\n" + page).encode()).hexdigest())


@pytest.fixture
def candidate_binding(monkeypatch, record_property):
    proposed, page, source_sha, candidate_sha = label_projection_candidate()
    monkeypatch.setattr(promotion_paging, "_snapshot_order_population", proposed)
    monkeypatch.setattr(publication_state, "_state_page", page)
    record_property("label_projection_source_sha256", source_sha)
    record_property("label_projection_candidate_sha256", candidate_sha)


def test_candidate_all_pages_native_reference(request, settings, monkeypatch, record_property, candidate_binding):
    assert_native_pages(request, settings, monkeypatch, record_property)


@pytest.mark.parametrize("role", ["individual", "owner", "editor"])
def test_candidate_revocation(request, settings, role, candidate_binding):
    assert_revocation(request, settings, role)


def test_candidate_snapshot_boundary(request, settings, monkeypatch, record_property, candidate_binding):
    assert_snapshot(request, settings, monkeypatch, record_property)


@pytest.mark.parametrize("language", ["es", "en"])
def test_candidate_checked_pending(request, settings, monkeypatch, language, record_property, candidate_binding):
    assert_checked(request, settings, monkeypatch, language, record_property)


def test_candidate_inherited_transaction(request, settings, monkeypatch, candidate_binding):
    assert_inherited(request, settings, monkeypatch)


@pytest.mark.parametrize("kind", ["premium", "autobump"])
def test_sql_shape_and_empty_or_populated_hint(request, settings, monkeypatch, record_property, kind):
    import json

    from django.db import connection, transaction
    from django.test import Client
    from django.utils import timezone
    from psycopg.types.json import Jsonb
    from test_promotion_exposure import purchased

    from apps.catalog.promotion_order_models import PromotionEntitlement
    from apps.listings.models import Listing, PublicationState

    _, listing, entitlement = purchased(request, settings, kind)
    if kind == "autobump":
        PromotionEntitlement.objects.filter(pk=entitlement.pk).update(last_bumped_at=timezone.now())
    publication_state.refresh_all()
    ranking, page_candidate, sources, candidate_sha = label_projection_candidate()
    original_ranking = promotion_paging._snapshot_order_population
    instant = timezone.now()
    shapes = []
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        for surface, population, identifier in [
            ("listing", Listing.objects.filter(pk=listing.pk).order_by("-published_at", "pk"), "pk"),
            ("state", PublicationState.objects.filter(listing_id=listing.pk, eligible=True).order_by(
                "-published_at", "listing_id"), "listing_id"),
        ]:
            before = original_ranking(population, identifier, now=instant)
            after = ranking(population, identifier, now=instant)
            original = before.values_list(identifier, "_promotion_priority")
            candidate = after.values_list(identifier, flat=True)
            old_sql, old_params = original.query.sql_with_params()
            new_sql, new_params = candidate.query.sql_with_params()
            old_maps = [p for p in old_params if isinstance(p, Jsonb)]
            new_maps = [p for p in new_params if isinstance(p, Jsonb)]
            old_bytes = sum(len(json.dumps(p.obj, separators=(",", ":")).encode()) for p in old_maps)
            new_bytes = sum(len(json.dumps(p.obj, separators=(",", ":")).encode()) for p in new_maps)
            assert old_sql.count("jsonb_extract_path_text") > new_sql.count("jsonb_extract_path_text") >= 1
            assert len(old_maps) > len(new_maps) >= 1 and old_bytes > new_bytes > 0
            old_rows, new_ids = list(original), list(candidate)
            assert new_ids == [pk for pk, _ in old_rows] == [listing.pk]
            labels = {pk: "premium" if rank == 0 else "top" for pk, rank in old_rows if rank < 2}
            hint = after._publication_sponsorship
            assert {pk: hint[pk] for pk in new_ids if pk in hint} == labels
            shapes.append({"surface": surface, "kind": kind,
                           "original_map_parameters": len(old_maps), "candidate_map_parameters": len(new_maps),
                           "original_json_bytes": old_bytes, "candidate_json_bytes": new_bytes,
                           "original_json_extracts": old_sql.count("jsonb_extract_path_text"),
                           "candidate_json_extracts": new_sql.count("jsonb_extract_path_text")})
    baseline = Client().get("/es/")
    observed_hints = []

    def observed_ranking(*args, **kwargs):
        ordered = ranking(*args, **kwargs)
        hint = getattr(ordered, "_publication_sponsorship", None)
        observed_hints.append(None if hint is None else len(hint))
        return ordered

    with monkeypatch.context() as patch:
        patch.setattr(promotion_paging, "_snapshot_order_population", observed_ranking)
        patch.setattr(publication_state, "_state_page", page_candidate)
        response = Client().get("/es/")
    assert response.status_code == baseline.status_code == 200
    assert response.wsgi_request._publication_route["route"] == "state"
    assert baseline.wsgi_request._publication_route["route"] == "state"
    assert response.content == baseline.content
    assert response.context["page"].sponsorship == baseline.context["page"].sponsorship
    assert observed_hints == [1 if kind == "premium" else 0]
    record_property("label_projection_sql_shapes", shapes)
    record_property("label_projection_source_sha256", sources)
    record_property("label_projection_candidate_sha256", candidate_sha)
