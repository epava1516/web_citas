"""Counterfactual rollback must agree with actual native state and rendered pages."""

import pytest
from beta_promotional_load_fixture import (
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.utils import timezone
from mixed_state_plan import apply_mixed_plan, native_sponsorships, prepare_mixed_plan
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.catalog.promotion_exposure import eligible
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('population', [100, 1000, 10000])
def test_counterfactual_mixed_plan_rolls_back_then_matches_actual_pages(request, settings, record_property, population):
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    dataset = prepare_promotional_load(request, population)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    dataset = redistribute_promotional_geography(dataset, {cities[0]: population*7//10, cities[1]: population*3//10})
    publication_state.refresh_all()
    for invalid in (dataset | {'synthetic': False}, dataset | {'published': 100000}):
        with pytest.raises(AssertionError):
            prepare_mixed_plan(invalid)
        assert not PublicationDirty.objects.exists()
    plan = prepare_mixed_plan(dataset)
    assert plan['route_geography'] == {str(cities[0]): population*7//10-14,
                                       str(cities[1]): population*3//10}
    assert plan['protected_detail_ids'] == {dataset['sample_ids'][0], dataset['sample_ids'][-1]}
    assert not plan['protected_detail_ids'] & {str(x['id']) for x in plan['mutations']}
    assert not plan['protected_detail_ids'] & set(map(str, plan['inactive_profiles']))
    assert plan['rollback_proof']['native_fields_restored'] and plan['rollback_proof']['dirty_empty']
    assert plan['rollback_proof']['sequence_after']>plan['rollback_proof']['sequence_before']
    assert not plan['rollback_proof']['sequence_reset']
    assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
    assert len(native_sponsorships()) == population//5  # Suspensions and expiry were rolled back too.
    assert all(publicly_visible(Listing.objects.get(pk=x['id'])) for x in plan['mutations'])
    markers = apply_mixed_plan(dataset, plan)
    assert len(markers) == 14 and len({x['generation'] for x in markers}) == 14
    assert all(x['generation']>plan['rollback_proof']['sequence_after'] for x in markers)
    assert native_sponsorships() == plan['sponsorships'] and len(plan['sponsorships']) == population//5-9
    pages_checked = 0
    for city in dataset['geography']:
        for text in ('', 'photography'):
            expected = reference_territorial_order(city, text, promotions=True)
            assert expected == plan['references'][(str(city), text)]
            for language in ('es', 'en'):
                seen = []
                last = (len(expected)+23)//24
                numbers = sorted({1, (last+1)//2, last}) if population>=1000 else range(1, last+1)
                for page_number in numbers:
                    response = client.get('/'+language+'/', {'city': city, 'q': text, 'page': page_number})
                    assert response.status_code == 200
                    page = response.context['page']
                    ids = [row.pk for row in page.object_list]
                    assert ids == expected[(page_number-1)*24:page_number*24]
                    assert page.paginator.count == len(expected)
                    assert [card['sponsorship'] for card in response.context['cards']] == [
                        plan['sponsorships'].get(pk) for pk in ids]
                    seen += ids
                    pages_checked += 1
                if population==100:
                    assert seen == expected
                assert len(seen) == len(set(seen))
    for mutation in plan['mutations']:
        assert not publicly_visible(Listing.objects.get(pk=mutation['id']))
        for language in ('es', 'en'):
            assert client.get(f'/{language}/listing/{mutation["id"]}/').status_code == 404
    for right_id, pk in zip(plan['inactive_rights'], plan['inactive_profiles']):
        row = Listing.objects.get(pk=pk)
        assert publicly_visible(row)
        assert not eligible(PromotionEntitlement.objects.get(pk=right_id), row, timezone.now())
    assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == markers
    assert pages_checked == (20 if population==100 else 24)
    record_property('counterfactual_mixed_plan', {
        'protected_detail_count': 2, 'population': population, 'visible_after': population-14, 'excluded': 14,
        'rights': population//5, 'active_sponsorships_after': population//5-9,
        'route_geography': plan['route_geography'],
        'rollback': plan['rollback_proof'], 'actual_dirty_marks': 14,
        'native_order_censuses_after': 4, 'pages_after': pages_checked,
        'excluded_detail_404_checks': 28, 'reads_do_not_repair': True,
        'worker_execution_credited': False, 'capacity_accepted': False,
    })


@pytest.mark.parametrize('population', [100, 1000, 10000])
def test_committed_mixed_plan_preserves_native_pages_before_and_after_refresh(request, settings, record_property, population):
    from mixed_state_plan import prepare_committed_mixed_plan

    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    dataset = prepare_promotional_load(request, population)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    dataset = redistribute_promotional_geography(dataset, {cities[0]: population*7//10, cities[1]: population*3//10})
    publication_state.refresh_all()
    for invalid in (dataset | {'synthetic': False}, dataset | {'published': 100000}):
        with pytest.raises(AssertionError):
            prepare_committed_mixed_plan(invalid)
        assert not PublicationDirty.objects.exists()
    plan = prepare_committed_mixed_plan(dataset)
    assert plan['counterfactual_rollback_used'] is False and 'rollback_proof' not in plan
    assert plan['route_geography'] == {str(cities[0]): population*7//10-14, str(cities[1]): population*3//10}
    assert len(plan['committed_dirty_markers']) == 14
    assert len({x['generation'] for x in plan['committed_dirty_markers']}) == 14
    assert not plan['protected_detail_ids'] & {str(x['id']) for x in plan['mutations']}
    assert not plan['protected_detail_ids'] & set(map(str, plan['inactive_profiles']))
    signatures = []
    pages_checked = 0
    for repaired in (False, True):
        if repaired:
            publication_state.refresh_all()
            assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
        observed = []
        for city in dataset['geography']:
            for text in ('', 'photography'):
                expected = reference_territorial_order(city, text, promotions=True)
                assert expected == plan['references'][(str(city), text)]
                for language in ('es', 'en'):
                    last = (len(expected)+23)//24
                    numbers = sorted({1, (last+1)//2, last}) if population>=1000 else range(1, last+1)
                    for page_number in numbers:
                        response = client.get('/'+language+'/', {'city': city, 'q': text, 'page': page_number})
                        assert response.status_code == 200
                        page = response.context['page']
                        ids = [row.pk for row in page.object_list]
                        labels = [card['sponsorship'] for card in response.context['cards']]
                        assert ids == expected[(page_number-1)*24:page_number*24]
                        assert page.paginator.count == len(expected) and len(ids) == len(set(ids))
                        assert labels == [plan['sponsorships'].get(pk) for pk in ids]
                        observed.append((str(city), text, language, page_number, ids, labels, page.paginator.count))
                        pages_checked += 1
        for mutation in plan['mutations']:
            assert not publicly_visible(Listing.objects.get(pk=mutation['id']))
            for language in ('es', 'en'):
                assert client.get(f'/{language}/listing/{mutation["id"]}/').status_code == 404
        for right_id, pk in zip(plan['inactive_rights'], plan['inactive_profiles']):
            row = Listing.objects.get(pk=pk)
            assert publicly_visible(row)
            assert not eligible(PromotionEntitlement.objects.get(pk=right_id), row, timezone.now())
        if not repaired:
            assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == plan['committed_dirty_markers']
        signatures.append(observed)
    assert signatures[0] == signatures[1]
    assert pages_checked == (40 if population==100 else 48)
    record_property('committed_mixed_plan', {
        'population': population, 'visible_after': population-14, 'rights': population//5,
        'active_sponsorships_after': population//5-9, 'route_geography': plan['route_geography'],
        'pages': pages_checked, 'excluded_detail_404_checks': 56, 'native_order_censuses': 12,
        'counterfactual_rollback_used': False, 'pending_get_preserves_marks': True,
        'pending_repaired_signatures_equal': True, 'manual_refresh': True,
        'worker_execution_credited': False, 'capacity_accepted': False,
    })
