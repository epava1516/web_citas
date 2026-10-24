"""Experimental global rank restriction; no product patch or capacity claim."""

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

pytestmark = pytest.mark.django_db(transaction=True)


def global_rights_candidate():
    source_sha = hashlib.sha256(Path(promotion_paging.__file__).read_bytes()).hexdigest()
    assert source_sha == "79665c4cd351f668f4f8378ead3ce514b6fdd6491f737e1b6c8294b31913009e"
    source = inspect.getsource(promotion_paging._snapshot_order_population)
    needle = (
        "live_entitlements(now).filter(\n"
        "        order__listing_id__in=query.order_by().values(listing_field),\n"
        "    ).values_list"
    )
    assert source.count(needle) == 1
    candidate = source.replace(needle, "live_entitlements(now).values_list")
    namespace = vars(promotion_paging).copy()
    exec(compile(candidate, "<beta-global-rights-candidate>", "exec"), namespace)
    return namespace["_snapshot_order_population"], source_sha, hashlib.sha256(candidate.encode()).hexdigest()


@pytest.fixture
def candidate_binding(monkeypatch, record_property):
    proposed, source_sha, candidate_sha = global_rights_candidate()
    monkeypatch.setattr(promotion_paging, "_snapshot_order_population", proposed)
    record_property("global_rights_source_sha256", source_sha)
    record_property("global_rights_candidate_sha256", candidate_sha)


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


def test_global_rights_outside_selective_population(request, settings, record_property):
    """Rights outside membership must affect neither relative order nor labels."""
    import runpy
    from datetime import timedelta

    from django.db import connection, transaction
    from django.utils import timezone
    from test_promotion_orders import setup
    from test_promotion_paged_equivalence import grant
    from test_publication_state_matrix import prepare_population

    from apps.catalog.promotion_models import PromotionProduct, PromotionProductVersion
    from apps.catalog.promotion_order_models import PromotionEntitlement
    from apps.listings import discovery, publication_state
    from apps.listings.models import Listing
    from apps.listings.moderation import publicly_visible
    from apps.listings.public_validation import PublicationContext

    _, _, top, _ = setup(request, settings)
    prepare_population(50, "diverse")
    rows = list(Listing.objects.filter(status="published", person__agency__isnull=False)
                .select_related("person__agency__owner").order_by("pk"))
    assert len(rows) == 49
    instant = timezone.now()
    for kind, selected in [("premium", rows[:12]), ("top", rows[8:24]), ("autobump", rows[4:32])]:
        version = top if kind == "top" else PromotionProductVersion.objects.create(
            product=PromotionProduct.objects.create(slug="global_parity_" + kind, kind=kind),
            version=1, name_es="Prueba", name_en="Test", duration_days=top.duration_days,
            amount=top.amount, currency=top.currency, tax_rate=top.tax_rate,
            bump_interval_minutes=60 if kind == "autobump" else None,
            daily_bump_limit=3 if kind == "autobump" else None,
            published_at=instant, is_current=True,
        )
        for index, row in enumerate(selected):
            entitlement = grant(row.person, version)
            if kind == "autobump":
                PromotionEntitlement.objects.filter(pk=entitlement.pk).update(
                    last_bumped_at=instant - timedelta(minutes=1 + index // 2),
                )
    # Rights remain commercially live while their listings leave publication.
    Listing.objects.filter(pk__in=[r.pk for r in rows[:2]]).update(status="withdrawn")
    Listing.objects.filter(pk__in=[r.pk for r in rows[2:4]]).update(
        expires_at=instant - timedelta(seconds=1),
    )
    publication_state.refresh_all()
    instant = timezone.now()  # Include every right created during setup.
    proposed, source_sha, candidate_sha = global_rights_candidate()
    reference = settings.BASE_DIR / "docs/evidencias/b08-promociones-referencia-20261020.py"
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == (
        "9f700b72394edbc8aac1a671081885b66c1754ed97f6c012a9f802bc45337c29"
    )
    native = runpy.run_path(str(reference), run_name="apps.catalog._beta_frozen_reference")["ranked"]
    cohorts = {
        "all": rows, "empty": [], "organic_only": rows[36:],
        "mixed": [rows[i] for i in [4, 8, 12, 17, 24, 25, 32, 48]],
        "bump_and_organic": rows[24:32] + rows[44:], "single_organic": rows[48:],
    }
    comparisons = []
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        global_count = promotion_paging.live_entitlements(instant).count()
        assert global_count == 56
        excluded_rights = promotion_paging.live_entitlements(instant).filter(
            order__listing_id__in=[r.pk for r in rows[:4]],
        ).count()
        assert excluded_rights > 0
        for name, selected in cohorts.items():
            for text_search in [False, True]:
                form = discovery.SearchForm({"q": "photography"} if text_search else {})
                assert form.is_valid()
                population = discovery.candidates(form.cleaned_data).filter(
                    pk__in=[r.pk for r in selected],
                )
                context = PublicationContext(population, page_read=True)
                visible = [row for row in context.rows if publicly_visible(row, context=context)]
                expected, labels = native(visible, text_search=text_search, now=instant)
                original = list(promotion_paging._snapshot_order_population(
                    population, "pk", text_search=text_search, now=instant,
                ).values_list("pk", "_promotion_priority"))
                candidate = list(proposed(
                    population, "pk", text_search=text_search, now=instant,
                ).values_list("pk", "_promotion_priority"))
                assert original == candidate
                assert [pk for pk, _ in candidate] == [row.pk for row in expected]
                assert {pk: "premium" if rank == 0 else "top"
                        for pk, rank in candidate if rank < 2} == labels
                filtered_count = promotion_paging.live_entitlements(instant).filter(
                    order__listing_id__in=population.order_by().values("pk"),
                ).count()
                if name in {"organic_only", "single_organic", "empty"}:
                    assert filtered_count == 0 and not labels
                comparisons.append({"cohort": name, "text_search": text_search,
                                    "population": len(candidate), "global_rights": global_count,
                                    "filtered_rights": filtered_count})
    assert len(comparisons) == 12
    record_property("global_rights_selective_comparisons", comparisons)
    record_property("global_rights_source_sha256", source_sha)
    record_property("global_rights_candidate_sha256", candidate_sha)
