"""Mixed lifecycle/authority membership and sponsorship; real PostgreSQL, no load credit."""

import os
from datetime import timedelta

import pytest
from beta_promotional_load_fixture import (
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.db import connection, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.catalog.promotion_exposure import eligible
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.core.models import Person
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('repair_mode', ['manual', 'native'])
def test_mixed_state_territorial_equivalence(request, settings, record_property, tmp_path, repair_mode):
    verify_mixed_state_territorial_equivalence(request, settings, record_property, tmp_path, repair_mode)


def verify_mixed_state_territorial_equivalence(
        request, settings, record_property, tmp_path, repair_mode, *, population=100, selected_pages_only=False):
    assert population in (100, 1000, 10000)
    if repair_mode == 'native' and (os.environ.get('WEB_MODELOS_REFRESH_MODE') != 'normal_worker_beat'
                                    or os.environ.get('PYTEST_XDIST_WORKER')):
        pytest.skip('Explicit single-worker owned native topology required')
    assert connection.vendor == 'postgresql'
    assert not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert not publication_state.READ_REPAIR
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    dataset = prepare_promotional_load(request, population)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    dataset = redistribute_promotional_geography(dataset, {cities[0]: population*7//10, cities[1]: population*3//10})
    rights = list(PromotionEntitlement.objects.select_related('order').order_by('order__listing_id'))
    assert len(rights) == population//5
    right_ids = {r.order.listing_id for r in rights}
    promoted = list(Listing.objects.filter(pk__in=right_ids).order_by('pk'))
    organic = list(Listing.objects.filter(status='published').exclude(pk__in=right_ids).order_by('pk'))
    excluded = set()
    mutations = []
    phases = []
    pending_signatures = None
    native_repair = None
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    for phase in ('fresh', 'mixed_pending', 'mixed_repaired'):
        if phase == 'mixed_pending':
            now = timezone.now()
            with transaction.atomic():
                for i, state in enumerate(('draft', 'processing', 'pending', 'paused',
                                            'expired', 'withdrawn', 'consent_revoked')):
                    for kind, row in (('promoted', promoted[i]), ('organic', organic[i])):
                        if state == 'consent_revoked':
                            assert Person.objects.filter(pk=row.person_id).update(consent_revoked_at=now) == 1
                        elif state == 'expired':
                            # Published row with elapsed expiry tests the clock gate itself.
                            assert Listing.objects.filter(pk=row.pk).update(expires_at=now-timedelta(seconds=1)) == 1
                        else:
                            assert Listing.objects.filter(pk=row.pk).update(status=state) == 1
                        excluded.add(row.pk)
                        mutations.append({'id': str(row.pk), 'kind': kind, 'state': state})
                assert PromotionEntitlement.objects.filter(pk=rights[7].pk).update(suspended_at=now) == 1
                assert PromotionEntitlement.objects.filter(pk=rights[8].pk).update(
                    starts_at=now-timedelta(days=2), ends_at=now-timedelta(days=1)) == 1
            assert len(excluded) == 14
            assert all(not publicly_visible(Listing.objects.get(pk=pk)) for pk in excluded)
        elif phase == 'mixed_repaired':
            if repair_mode == 'native':
                from mixed_state_worker import repair_mixed_with_owned_worker

                native_repair = repair_mixed_with_owned_worker(request, tmp_path, settings)
            else:
                publication_state.refresh_all()  # Explicit manual repair; no worker credit.
            assert not PublicationDirty.objects.exists()
        dirty_before = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
        if phase == 'mixed_pending':
            assert excluded <= {v['listing_id'] for v in dirty_before}
        signatures = []
        for city in cities:
            native = {row.pk for row in Listing.objects.filter(approved_revision__municipality_id=city)
                      if publicly_visible(row)}
            assert not native & excluded
            references = {text: reference_territorial_order(city, text, promotions=True)
                          for text in ('', 'photography')}
            assert all(set(ids) == native for ids in references.values())
            current_rights = list(PromotionEntitlement.objects.select_related('order'))
            sponsored = {right.order.listing_id for right in current_rights
                         if right.order.listing_id in native
                         and eligible(right, Listing.objects.get(pk=right.order.listing_id), timezone.now())}
            for text, reference in references.items():
                for language in ('es', 'en'):
                    seen = []
                    last = (len(reference)+23)//24
                    numbers = sorted({1, (last+1)//2, last}) if selected_pages_only else range(1, last+1)
                    for number in numbers:
                        response = client.get('/'+language+'/', {'city': city, 'q': text, 'page': number})
                        assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
                        page = response.context['page']
                        ids = [row.pk for row in page.object_list]
                        assert page.number == number and page.paginator.count == len(reference)
                        assert ids == reference[(number-1)*24:number*24]
                        labels = [bool(card['sponsorship']) for card in response.context['cards']]
                        assert labels == [pk in sponsored for pk in ids]
                        seen += ids
                        signatures.append({'city': city, 'text': text, 'language': language,
                                           'page': number, 'ids': list(map(str, ids)), 'sponsored': labels,
                                           'count': len(reference)})
                    if not selected_pages_only:
                        assert seen == reference
                    assert len(seen) == len(set(seen))
        if phase != 'fresh':
            for pk in excluded:
                for language in ('es', 'en'):
                    assert client.get(f'/{language}/listing/{pk}/').status_code == 404
            for right in (rights[7], rights[8]):
                row = Listing.objects.get(pk=right.order.listing_id)
                assert publicly_visible(row)
                assert not eligible(PromotionEntitlement.objects.get(pk=right.pk), row, timezone.now())
            assert sum(1 for row in Listing.objects.all() if publicly_visible(row)) == population-14
        assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == dirty_before
        if phase == 'mixed_pending':
            pending_signatures = signatures
        elif phase == 'mixed_repaired':
            assert signatures == pending_signatures
        phases.append({'phase': phase, 'pages': signatures, 'dirty_marks': len(dirty_before)})
    assert PromotionEntitlement.objects.count() == population//5
    record_property('mixed_state_territorial_equivalence', {
        'population': population, 'geography': dataset['geography'], 'rights': population//5,
        'selected_pages_only': selected_pages_only,
        'mutations': mutations, 'excluded': 14, 'visible_after': population-14,
        'suspended_rights': 1, 'expired_rights': 1, 'phases': phases,
        'repair': 'native_beat_worker' if repair_mode == 'native' else 'explicit_manual',
        'worker_execution_credited': native_repair is not None, 'native_repair': native_repair,
        'capacity_accepted': False, 'production_or_real_verification_credited': False,
    })
