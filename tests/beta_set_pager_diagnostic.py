"""Experimental set-based pager: no product binding outside these tests."""

from datetime import UTC

import pytest
from django.db import connections
from django.db.models import F
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


class SetPager:
    """Narrow paginator protocol; same population and unmodified rights authority."""

    ordered = True

    def __init__(self, query, identifier, *, text_search, now):
        self.queryset = query
        self.identifier = identifier
        self.search = text_search
        self.day = now.astimezone(UTC).date().isoformat()
        self.rights = promotion_paging.live_entitlements(now).filter(
            order__listing_id__in=query.order_by().values(identifier),
        ).order_by().annotate(
            p_listing=F('order__listing_id'), p_kind=F('order__kind'),
            p_bumped=F('last_bumped_at'),
        ).values('p_listing', 'p_kind', 'p_bumped')

    def values_list(self, *fields):
        assert fields == (self.identifier, '_promotion_priority')
        return self

    def count(self):
        return self.queryset.count()

    def __getitem__(self, selection):
        assert isinstance(selection, slice) and selection.step is None
        assert selection.start is not None and selection.stop is not None
        assert 0 <= selection.start <= selection.stop
        base = self.queryset.order_by().annotate(
            p_id=F(self.identifier), p_published=F('published_at'),
        )
        columns = ['p_id', 'p_published']
        if self.search:
            columns.append('relevance')
        base_sql, base_params = base.values(*columns).query.sql_with_params()
        rights_sql, rights_params = self.rights.query.sql_with_params()
        # All SQL identifiers/fragments below are fixed code. Data use parameters.
        bump = '' if self.search else 'r.bump DESC NULLS LAST,'
        relevance = 'b.relevance DESC,' if self.search else ''
        sql = f"""
            WITH live AS MATERIALIZED ({rights_sql}),
            rights AS MATERIALIZED (
                SELECT p_listing,
                    MIN(CASE p_kind WHEN 'premium' THEN 0 WHEN 'top' THEN 1 ELSE 2 END) AS priority,
                    MAX(CASE WHEN p_kind = 'autobump' THEN p_bumped END) AS bump
                FROM live GROUP BY p_listing
            )
            SELECT b.p_id, COALESCE(r.priority, 2)
            FROM ({base_sql}) b LEFT JOIN rights r ON r.p_listing = b.p_id
            ORDER BY COALESCE(r.priority, 2),
                CASE WHEN r.priority < 2 THEN
                    sha256(convert_to(%s || ':' || b.p_id::text, 'UTF8'))
                    ELSE ''::bytea END,
                CASE WHEN r.priority < 2 THEN b.p_id::text ELSE '' END,
                {bump} {relevance} b.p_published DESC, b.p_id
            LIMIT %s OFFSET %s
        """
        with connections[self.queryset.db].cursor() as cursor:
            cursor.execute(sql, [*rights_params, *base_params, self.day,
                                 selection.stop - selection.start, selection.start])
            return cursor.fetchall()


def candidate(query, identifier, *, text_search=False, now=None):
    # Unknown shapes keep the original implementation. Ownership is supplied by
    # order_population: this hook is reached only for its trusted snapshot path.
    expected = ('-relevance', '-published_at', identifier) if text_search else (
        '-published_at', identifier,
    )
    if query.query.distinct or query.query.is_sliced or tuple(query.query.order_by) != expected:
        return ORIGINAL(query, identifier, text_search=text_search, now=now)
    return SetPager(query, identifier, text_search=text_search, now=now or timezone.now())


ORIGINAL = promotion_paging._snapshot_order_population


@pytest.fixture
def candidate_binding(monkeypatch, record_property):
    observed = []

    def bound(*args, **kwargs):
        value = candidate(*args, **kwargs)
        observed.append(isinstance(value, SetPager))
        return value

    monkeypatch.setattr(promotion_paging, '_snapshot_order_population', bound)
    yield observed
    record_property('set_pager_selected_calls', sum(observed))
    record_property('set_pager_fallback_calls', len(observed) - sum(observed))
    record_property('product_changed', False)


def test_set_pager_all_pages(request, settings, monkeypatch, record_property, candidate_binding):
    assert_pages(request, settings, monkeypatch, record_property)
    assert any(candidate_binding)


@pytest.mark.parametrize('role', ['individual', 'owner', 'editor'])
def test_set_pager_revocation(request, settings, role, candidate_binding):
    assert_revocation(request, settings, role)
    assert any(candidate_binding)


def test_set_pager_snapshot_boundary(request, settings, monkeypatch, record_property, candidate_binding):
    assert_snapshot(request, settings, monkeypatch, record_property)
    assert any(candidate_binding)


@pytest.mark.parametrize('language', ['es', 'en'])
def test_set_pager_checked_pending(request, settings, monkeypatch, language, record_property, candidate_binding):
    assert_checked(request, settings, monkeypatch, language, record_property)
    assert any(candidate_binding)


def test_set_pager_inherited_transaction(request, settings, monkeypatch, candidate_binding):
    assert_inherited(request, settings, monkeypatch)
    assert not candidate_binding
