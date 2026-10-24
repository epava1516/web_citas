"""Owned synthetic-only statistics finalization after full publication refresh."""

import hashlib
import os
from datetime import UTC

import pytest
from beta_post_fixture_statistics import data_checksums
from beta_promotional_load_fixture import (
    finalize_promotional_statistics,
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Municipality
from apps.catalog.promotion_order_models import PromotionEntitlement, PromotionOrder
from apps.listings import publication_state
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible

pytestmark = pytest.mark.django_db(transaction=True)


def reference_territorial_order(city, text, *, promotions, hydrate=True):
    """Native membership/authority, independent Python commercial comparator.

    PostgreSQL's text-search primitive supplies relevance, not discovery's
    candidates/order_population/ranked helpers or an observed HTTP order.
    """
    query = Listing.objects.filter(status='published', approved_revision__municipality_id=city)
    if text:
        search = (SearchQuery(text, config='spanish', search_type='websearch')
                  | SearchQuery(text, config='english', search_type='websearch'))
        query = query.annotate(vector=F('approved_revision__search_document'),
                               rank=SearchRank(F('approved_revision__search_document'), search))
        query = query.filter(vector=search).order_by('-rank', '-published_at', 'pk')
    else:
        query = query.order_by('-published_at', 'pk')
    if hydrate:
        # Fresh native joins only: never state projection, context validation or a result cache.
        query = query.select_related(
            'approved_revision__publisher_acceptance__document',
            'approved_revision__municipality__province__region',
            'person__phone_claim', 'person__agency',
        )
    visible = [row for row in query if publicly_visible(row)]
    if not promotions:
        return [row.pk for row in visible]
    from apps.catalog.promotion_exposure import eligible

    now = timezone.now()
    rights = list(PromotionEntitlement.objects.select_related('order')
                  .filter(order__listing_id__in=[row.pk for row in visible]))
    by_id = {row.pk: row for row in visible}
    priority = {}
    for right in rights:
        assert right.order.kind in {'premium', 'top'}  # This fixture has no autobump.
        if eligible(right, by_id[right.order.listing_id], now):
            pk = right.order.listing_id
            priority[pk] = min(priority.get(pk, 2), {'premium': 0, 'top': 1}[right.order.kind])
    day = now.astimezone(UTC).date().isoformat()
    sponsored = sorted(priority, key=lambda pk: (
        priority[pk], hashlib.sha256((day + ':' + str(pk)).encode()).digest(), str(pk)))
    return sponsored + [row.pk for row in visible if row.pk not in priority]


def test_promotional_geography_covers_individual_and_agency_profiles(request, settings, record_property):
    settings.PROMOTION_TEST_MODE = True
    request.getfixturevalue('directory')
    individual = Listing.objects.get(status='published', person__individual__isnull=False)
    city = Municipality.objects.get(code='demo-north')
    revision = individual.approved_revision
    revision.municipality, revision.postal_code, revision.zone = city, None, None
    revision.save(update_fields=['municipality', 'postal_code', 'zone'])
    assert publicly_visible(Listing.objects.get(pk=individual.pk))
    dataset = prepare_promotional_load(request, 10)
    agency = Listing.objects.filter(status='published', person__agency__isnull=False).first()
    assert agency.approved_revision.municipality_id != city.pk
    assert dataset['geography'] == {str(city.pk): 1, str(agency.approved_revision.municipality_id): 9}
    assert sum(dataset['geography'].values()) == dataset['published'] == 10
    assert dataset['geography_scope'] == 'All published listings, including individual and agency profiles'
    assert dataset['promotions']['count'] == 2
    assert PromotionOrder.objects.filter(status='paid', synthetic=True).count() == 2
    assert PromotionOrder.objects.count() == PromotionEntitlement.objects.count() == 2
    record_property('complete_geography_census', dataset['geography'])
    record_property('complete_geography_profiles', 10)


def verify_territorial_equivalence(request, settings, record_property, population, *, selected_pages_only=False):
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, population)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True).order_by('pk')[:2])
    assert len(cities) == 2
    first = population * 7 // 10
    second = population - first
    allocations = {cities[0].pk: first, cities[1].pk: second}
    before = data_checksums()
    for invalid in ({cities[0].pk: population}, {cities[0].pk: first, cities[1].pk: second - 1},
                    {cities[0].pk: population, cities[1].pk: 0},
                    {cities[0].pk: population - 1, cities[1].pk: True},
                    {cities[0].pk: first, 999999999: second}):
        with pytest.raises(ValueError):
            redistribute_promotional_geography(dataset, invalid)
        assert data_checksums() == before
    with pytest.raises(ValueError, match='synthetic PostgreSQL'):
        redistribute_promotional_geography(dataset | {'synthetic': False}, allocations)
    assert data_checksums() == before
    orders = list(PromotionOrder.objects.order_by('pk').values())
    rights = list(PromotionEntitlement.objects.order_by('pk').values())
    result = redistribute_promotional_geography(dataset, allocations)
    assert result['geography'] == {str(k): v for k, v in allocations.items()}
    assert result['publication_refresh_required_after_geography']
    assert dataset['geography'] != result['geography']  # Original evidence is not rewritten.
    assert 'agency/photo/geography' in dataset['limits']
    assert 'agency/photo/geography' not in result['limits']
    publication_state.refresh_all()
    assert publication_state.all_state_current()
    client = request.getfixturevalue('directory')
    all_ids = set()
    pages_checked = 0
    deepest_page = 0
    for city, count in allocations.items():
        listings = list(Listing.objects.filter(status='published', approved_revision__municipality_id=city))
        assert len(listings) == count and all(publicly_visible(row) for row in listings)
        expected = {row.pk for row in listings}
        assert not all_ids & expected
        all_ids |= expected
        references = {text: reference_territorial_order(city, text, promotions=True)
                      for text in ('', 'photography')}
        assert all(set(reference) == expected for reference in references.values())
        for language in ('es', 'en'):
            for text in ('', 'photography'):
                reference = references[text]
                seen = set()
                last = (count + 23) // 24
                numbers = (sorted({1, (last + 1) // 2, last}) if selected_pages_only
                           else range(1, last + 1))
                for number in numbers:
                    response = client.get('/' + language + '/', {'city': city, 'q': text, 'page': number})
                    assert response.status_code == 200
                    page = response.context['page']
                    assert page.number == number and page.paginator.count == count
                    ids = {row.pk for row in page.object_list}
                    assert len(ids) == len(page.object_list) <= 24
                    assert [row.pk for row in page.object_list] == reference[(number - 1) * 24:number * 24]
                    assert not seen & ids
                    seen |= ids
                    pages_checked += 1
                    deepest_page = max(deepest_page, number)
                if not selected_pages_only:
                    assert seen == expected
    assert len(all_ids) == population
    if population == 100:
        assert deepest_page == 3 and pages_checked == 20
    assert list(PromotionOrder.objects.order_by('pk').values()) == orders
    assert list(PromotionEntitlement.objects.order_by('pk').values()) == rights
    record_property('explicit_geography_counts', result['geography'])
    record_property('native_visible_and_filtered_es_en', population)
    record_property('negative_allocations_without_mutation', 6)
    record_property('city_and_text_pages_checked', pages_checked)
    record_property('deepest_page_checked', deepest_page)
    record_property('independent_commercial_order_pages_checked', pages_checked)
    record_property('page_coverage_mode', 'first_middle_last' if selected_pages_only else 'exhaustive')


@pytest.mark.parametrize('population', [10, 100])
def test_explicit_geography_distribution_preserves_native_visibility_and_rights(request, settings, record_property, population):
    verify_territorial_equivalence(request, settings, record_property, population)


def test_statistics_finalization_scope_and_domain_preservation(request, settings, monkeypatch, record_property):
    name = os.environ.get('LOCAL_CI_POSTGRES_CONTAINER', '')
    if not name.startswith('web-modelos-ci-pg-'):
        pytest.skip('Real disposable PostgreSQL runner required')
    monkeypatch.setenv('LOCAL_CI_BENCHMARK_RUN', name.removeprefix('web-modelos-ci-pg-'))
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, 10)
    analyzed = []

    def capture(execute, sql, params, many, context):
        if isinstance(sql, str) and sql.startswith('ANALYZE '):
            analyzed.append(sql)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(capture):
        with pytest.raises(ValueError, match='clean and current'):
            finalize_promotional_statistics(dataset)
        publication_state.refresh_all()
        before = data_checksums()
        with transaction.atomic(), pytest.raises(ValueError, match='autocommit'):
            finalize_promotional_statistics(dataset)
        with monkeypatch.context() as patch:
            patch.setattr(settings, 'PRODUCTION', True)
            with pytest.raises(ValueError, match='disposable'):
                finalize_promotional_statistics(dataset)
        with monkeypatch.context() as patch:
            patch.setenv('LOCAL_CI_POSTGRES_CONTAINER', 'unowned-synthetic-negative')
            with pytest.raises(ValueError, match='exact owned'):
                finalize_promotional_statistics(dataset)
        with pytest.raises(ValueError, match='declared complete'):
            finalize_promotional_statistics(dataset | {'published': 11})
        assert not analyzed
        result = finalize_promotional_statistics(dataset)
        expected = {'core_user', 'core_person', 'core_representationaction', 'core_verificationcheck',
                    'catalog_promotionorder', 'catalog_promotionentitlement',
                    'listings_publicationstate', 'listings_revision_categories'}
        assert set(result['tables']) == expected and len(analyzed) == 8
        assert all(sql == 'ANALYZE ' + connection.ops.quote_name(table)
                   for sql, table in zip(analyzed, sorted(expected), strict=True))
        assert result['owned_synthetic_postgresql_verified'] and not result['domain_rows_mutated']
        assert data_checksums() == before
    record_property('statistics_scope_negatives_before_analyze', 5)
    record_property('statistics_tables_analyzed', 8)
    record_property('statistics_domain_checksums_preserved', True)
