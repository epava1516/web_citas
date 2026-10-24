"""One test-only population membership fence; unchanged commercial authority/rank."""

import hashlib
import inspect
from pathlib import Path

import pytest
from django.core.exceptions import EmptyResultSet
from django.db.models.expressions import RawSQL
from django.utils import timezone
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

from apps.catalog import promotion_paging

pytestmark = pytest.mark.django_db(transaction=True)
ORIGINAL = promotion_paging._snapshot_order_population


def barrier_membership(query, listing_field):
    population = query.order_by().values(listing_field)
    try:
        sql, params = population.query.get_compiler(using=query.db).as_sql()
    except EmptyResultSet:
        return population
    # Zero offset is a semantic identity, with no candidate cap. Whether it
    # actually fences this planner path is an experimental plan question.
    return RawSQL(sql + ' OFFSET 0', params)


def build_candidate():
    assert hashlib.sha256(Path(promotion_paging.__file__).read_bytes()).hexdigest() == (
        '79665c4cd351f668f4f8378ead3ce514b6fdd6491f737e1b6c8294b31913009e'
    )
    source = inspect.getsource(ORIGINAL)
    before = 'order__listing_id__in=query.order_by().values(listing_field)'
    after = 'order__listing_id__in=barrier_membership(query, listing_field)'
    assert source.count(before) == 1
    modified = source.replace(before, after)
    namespace = vars(promotion_paging).copy() | {'barrier_membership': barrier_membership}
    exec(compile(modified, '<beta-membership-fence>', 'exec'), namespace)
    return namespace['_snapshot_order_population']


CANDIDATE = build_candidate()


@pytest.fixture
def candidate_binding(monkeypatch, record_property):
    counts = []

    def compared(query, listing_field, *, text_search=False, now=None):
        now = now or timezone.now()
        rights = promotion_paging.live_entitlements(now)
        expected = list(rights.filter(
            order__listing_id__in=query.order_by().values(listing_field),
        ).order_by('pk').values_list('pk', flat=True))
        actual = list(rights.filter(
            order__listing_id__in=barrier_membership(query, listing_field),
        ).order_by('pk').values_list('pk', flat=True))
        assert actual == expected
        counts.append(len(actual))
        return CANDIDATE(query, listing_field, text_search=text_search, now=now)

    monkeypatch.setattr(promotion_paging, '_snapshot_order_population', compared)
    yield counts
    record_property('membership_fence_rights_comparisons', len(counts))
    record_property('product_changed', False)


def test_membership_all_pages(request, settings, monkeypatch, record_property, candidate_binding):
    assert_pages(request, settings, monkeypatch, record_property)
    assert len(candidate_binding) == 32


@pytest.mark.parametrize('role', ['individual', 'owner', 'editor'])
def test_membership_revocation(request, settings, role, candidate_binding):
    assert_revocation(request, settings, role)
    assert len(candidate_binding) == 2


def test_membership_snapshot_boundary(request, settings, monkeypatch, record_property, candidate_binding):
    assert_snapshot(request, settings, monkeypatch, record_property)
    assert len(candidate_binding) == 2


@pytest.mark.parametrize('language', ['es', 'en'])
def test_membership_checked(request, settings, monkeypatch, language, record_property, candidate_binding):
    assert_checked(request, settings, monkeypatch, language, record_property)
    assert len(candidate_binding) == 2


def test_membership_inherited(request, settings, monkeypatch, candidate_binding):
    assert_inherited(request, settings, monkeypatch)
    assert not candidate_binding
