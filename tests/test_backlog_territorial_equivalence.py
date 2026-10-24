"""All small territorial pages across the real 48/49 unknown-state boundary.

Functional PostgreSQL equivalence only. Repair is explicit/manual here; worker
execution and capacity are separate evidence, not simulated by this control.
"""

import hashlib
from contextlib import nullcontext
from datetime import timedelta

import pytest
from beta_promotional_load_fixture import (
    finalize_promotional_statistics,
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.db import connection, transaction
from django.db.models import Count
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def verify_territorial_unknown49_equivalence(
        request, settings, record_property, with_rights, *, population=100, selected_pages_only=False):
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert not publication_state.READ_REPAIR and publication_state.NATIVE_UNKNOWN_LIMIT == 48
    assert publication_state.DIRTY_LIMIT == 1000
    settings.PROMOTION_TEST_MODE = True
    client = request.getfixturevalue('directory')
    settings.CELERY_TASK_ALWAYS_EAGER = False
    from config.celery import app as celery_app

    assert not celery_app.conf.task_always_eager
    if with_rights:
        dataset = prepare_promotional_load(request, population)
    else:
        dataset = populate(population)
        assert not PromotionEntitlement.objects.exists()
        dataset['promotions'] = {'synthetic_only': True, 'count': 0, 'premium': 0, 'top': 0,
                                 'issuance': 'No orders or rights issued in this control'}
        dataset['geography'] = {
            str(row['approved_revision__municipality_id']): row['count']
            for row in Listing.objects.filter(status='published')
            .values('approved_revision__municipality_id').annotate(count=Count('pk'))
        }
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    assert len(cities) == 2
    first_count = population * 7 // 10
    second_count = population - first_count
    dataset = redistribute_promotional_geography(
        dataset, {cities[0]: first_count, cities[1]: second_count})
    publication_state.refresh_all()
    finalized = finalize_promotional_statistics(dataset)
    assert finalized['owned_synthetic_postgresql_verified'] and len(finalized['tables']) == 8
    expected_rights = population // 5 if with_rights else 0
    assert PromotionEntitlement.objects.count() == expected_rights
    right_ids = set(PromotionEntitlement.objects.values_list('order__listing_id', flat=True))
    # Geography was assigned in PK order, so these 49 retained candidates share
    # the first municipality and really cross the per-query unknown threshold.
    first_city = Listing.objects.filter(status='published', approved_revision__municipality_id=cities[0])
    if with_rights:
        withdrawn = first_city.filter(
            pk__in=PromotionEntitlement.objects.values_list('order__listing_id', flat=True)
        ).order_by('pk').first()
    else:
        withdrawn = first_city.order_by('pk').first()
    assert withdrawn is not None
    unknown = list(first_city.exclude(pk=withdrawn.pk).order_by('pk')[:49])
    assert len(unknown) == 49 and all(publicly_visible(row) for row in unknown)
    phases = []
    pending_signatures = None
    for phase in ('fresh', 'dirty49', 'dirty49_read_committed', 'repaired'):
        if phase == 'dirty49':
            with transaction.atomic():
                assert Listing.objects.filter(pk=withdrawn.pk).update(status='withdrawn') == 1
                assert Listing.objects.filter(pk__in=[row.pk for row in unknown]).update(
                    available_until=timezone.now() + timedelta(hours=1)) == 49
            assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {
                withdrawn.pk, *(row.pk for row in unknown)}
            assert not publicly_visible(Listing.objects.get(pk=withdrawn.pk))
            assert all(publicly_visible(Listing.objects.get(pk=row.pk)) for row in unknown)
        elif phase == 'repaired':
            publication_state.refresh_all()  # Deliberately manual; no worker credit.
            assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
        signatures, reports, census = [], [], []
        sponsorships = 0
        expected_sponsorships = 0
        for city in cities:
            expected_count = first_count if city == cities[0] else second_count
            if phase != 'fresh' and city == cities[0]:
                expected_count -= 1
            for text in ('', 'photography'):
                reference = reference_territorial_order(city, text, promotions=True)
                assert len(reference) == expected_count and len(reference) == len(set(reference))
                assert set(reference) == set(Listing.objects.filter(
                    status='published', approved_revision__municipality_id=city
                ).values_list('pk', flat=True))
                census.append({'city': city, 'text': text, 'count': len(reference),
                               'ordered_ids_sha256': hashlib.sha256(
                                   '\n'.join(map(str, reference)).encode()).hexdigest()})
                for language in ('es', 'en'):
                    seen = []
                    last = (expected_count + 23) // 24
                    numbers = (sorted({1, (last + 1) // 2, last}) if selected_pages_only
                               else list(range(1, last + 1)))
                    for number in numbers:
                        params = {'city': city, 'q': text, 'page': number}
                        with transaction.atomic() if phase == 'dirty49_read_committed' else nullcontext():
                            if phase == 'dirty49_read_committed':
                                with connection.cursor() as cursor:
                                    cursor.execute('SHOW transaction_isolation')
                                    assert cursor.fetchone()[0] == 'read committed'
                            response = client.get('/' + language + '/', params)
                        assert response.status_code == 200
                        page, route = response.context['page'], response.wsgi_request._publication_route
                        ids = [row.pk for row in page.object_list]
                        assert page.number == number and page.paginator.count == expected_count
                        assert ids == reference[(number - 1) * 24:number * 24]
                        fallback = phase == 'dirty49_read_committed' and city == cities[0]
                        assert route['route'] == ('fallback' if fallback else 'state')
                        if fallback:
                            assert route['reason'] == 'state_unknown_over_limit'
                        elif phase == 'dirty49' and city == cities[0]:
                            assert route['reason'] == 'trusted_state_extended_unknown' and route['native_unknown'] == 49
                        if phase != 'fresh':
                            assert withdrawn.pk not in ids
                        labels = [card['sponsorship'] for card in response.context['cards']]
                        expected_labels = [pk in right_ids for pk in reference[(number - 1) * 24:number * 24]]
                        assert [bool(value) for value in labels] == expected_labels
                        sponsorships += sum(bool(value) for value in labels)
                        expected_sponsorships += sum(expected_labels)
                        signatures.append({'city': city, 'text': text, 'language': language, 'page': number,
                                           'count': expected_count, 'ids': list(map(str, ids)), 'sponsorship': labels})
                        reports.append({'city': city, 'text': text, 'language': language,
                                        'page': number, 'route': route})
                        seen += ids
                    selected_reference = [pk for number in numbers
                                          for pk in reference[(number - 1) * 24:number * 24]]
                    assert seen == selected_reference and len(seen) == len(set(seen))
                    if not selected_pages_only:
                        assert seen == reference
        assert sponsorships == expected_sponsorships
        if not selected_pages_only:
            assert sponsorships == 4 * (expected_rights - (1 if with_rights and phase != 'fresh' else 0))
        if phase == 'dirty49':
            pending_signatures = signatures
            assert PublicationDirty.objects.count() == 50  # GET must not repair behind this test.
        elif phase in {'dirty49_read_committed', 'repaired'}:
            assert signatures == pending_signatures
            assert PublicationDirty.objects.count() == (50 if phase == 'dirty49_read_committed' else 0)
        phases.append({'phase': phase, 'pages': len(signatures), 'signatures': signatures,
                       'routes': reports, 'reference_census': census, 'sponsorship_cards': sponsorships,
                       'dirty_count_after_reads': PublicationDirty.objects.count()})
    expected_pages = 24 if selected_pages_only else 20
    assert [row['pages'] for row in phases] == [expected_pages] * 4
    record_property('territorial_unknown49_equivalence', {
        'population_prepared': population, 'visible_after': population - 1,
        'coverage': 'first_middle_last' if selected_pages_only else 'all_pages',
        'complete_native_reference_census': True, 'geography_prepared': dataset['geography'],
        'native_rights': expected_rights, 'eligible_unknown': 49, 'withdrawn_dirty': 1,
        'withdrawn_id': str(withdrawn.pk), 'unknown_eligible_ids': [str(row.pk) for row in unknown],
        'threshold_unchanged': 48, 'dirty_limit_unchanged': publication_state.DIRTY_LIMIT, 'phases': phases, 'manual_repair': True,
        'worker_execution_credited': False, 'capacity_accepted': False,
    })


@pytest.mark.parametrize('with_rights', [False, True], ids=['0-rights', '20-rights'])
def test_territorial_unknown49_equivalence(request, settings, record_property, with_rights):
    verify_territorial_unknown49_equivalence(request, settings, record_property, with_rights)
