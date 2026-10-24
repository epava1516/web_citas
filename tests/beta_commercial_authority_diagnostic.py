"""Experimental joined authority; never installed in the application by this test."""

import pytest
from django.db.models import Exists, F, OuterRef, Q
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_paged_equivalence import (
    test_all_pages_match_frozen_native_with_overlapping_rights as assert_pages,
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

from apps.catalog import promotion_exposure, promotion_paging
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.core.models import AgencyMember

pytestmark = pytest.mark.django_db(transaction=True)


def joined_authority(now):
    member = AgencyMember.objects.filter(
        agency_id=OuterRef("order__listing__person__agency_id"),
        user_id=OuterRef("order__buyer_id"), active=True,
    )
    return PromotionEntitlement.objects.filter(
        starts_at__lte=now, ends_at__gt=now, suspended_at__isnull=True,
        order__synthetic=True, order__status="paid", order__buyer__is_active=True,
        order__buyer__account_erased_at__isnull=True,
        order__listing__person__manager_version=F("order__manager_version"),
        order__listing__person__publication_erased_at__isnull=True,
    ).filter(
        Q(order__listing__person__individual_id=F("order__buyer_id"))
        | Q(order__listing__person__agency__owner_id=F("order__buyer_id"))
        | (Q(order__listing__person__assigned_editor_id=F("order__buyer_id")) & Q(Exists(member)))
    )


@pytest.fixture
def candidate_binding(monkeypatch, record_property):
    original = promotion_exposure.live_entitlements
    counts = {"comparisons": 0}

    def compared(now):
        candidate = joined_authority(now)
        actual = list(candidate.order_by("pk").values_list("pk", flat=True))
        expected = list(original(now).order_by("pk").values_list("pk", flat=True))
        assert actual == expected  # Includes duplicate/missing entitlements.
        counts["comparisons"] += 1
        return candidate

    monkeypatch.setattr(promotion_exposure, "live_entitlements", compared)
    monkeypatch.setattr(promotion_paging, "live_entitlements", compared)
    yield
    assert counts["comparisons"] > 0
    record_property("joined_authority_compared_with_original", counts["comparisons"])
    record_property("product_authority_changed", False)


def test_joined_all_pages(request, settings, monkeypatch, record_property, candidate_binding):
    assert_pages(request, settings, monkeypatch, record_property)


@pytest.mark.parametrize("role", ["individual", "owner", "editor"])
def test_joined_revocation(request, settings, role, candidate_binding):
    assert_revocation(request, settings, role)


def test_joined_snapshot_boundary(request, settings, monkeypatch, record_property, candidate_binding):
    assert_snapshot(request, settings, monkeypatch, record_property)


@pytest.mark.parametrize("language", ["es", "en"])
def test_joined_checked_pending(request, settings, monkeypatch, language, record_property, candidate_binding):
    assert_checked(request, settings, monkeypatch, language, record_property)


def test_joined_inherited_transaction(request, settings, monkeypatch, candidate_binding):
    assert_inherited(request, settings, monkeypatch)
