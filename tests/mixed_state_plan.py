"""Counterfactual native test oracle; logical rollback, monotonic generations kept."""

from datetime import UTC, timedelta

from capacity_runtime_role import _owned_database
from django.conf import settings
from django.db import connection, transaction
from django.utils import timezone
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.promotion_exposure import eligible
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.core.models import Person
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible

STATES = ('draft', 'processing', 'pending', 'paused', 'expired', 'withdrawn', 'consent_revoked')


def _scope(dataset):
    _owned_database()
    assert settings.PROMOTION_TEST_MODE and not settings.PRODUCTION and not settings.RECOVERY_MODE
    assert dataset['synthetic'] and dataset['promotions']['synthetic_only']
    assert dataset['published'] in (100, 1000, 10000)
    assert dataset['promotions']['count'] == dataset['published']//5
    assert not publication_state.READ_REPAIR and not connection.in_atomic_block


def _snapshot(plan):
    return {
        'listings': list(Listing.objects.filter(pk__in=[x['id'] for x in plan['mutations']])
                         .order_by('pk').values_list('pk', 'status', 'expires_at')),
        'people': list(Person.objects.filter(pk__in=[x['person'] for x in plan['mutations']])
                       .order_by('pk').values_list('pk', 'consent_revoked_at')),
        'rights': list(PromotionEntitlement.objects.filter(pk__in=plan['inactive_rights'])
                       .order_by('pk').values_list('pk', 'starts_at', 'ends_at', 'suspended_at')),
    }


def _mutate(plan):
    now = plan['mutation_time']
    for state in STATES:
        rows = [x for x in plan['mutations'] if x['state'] == state]
        assert len(rows) == 2
        if state == 'consent_revoked':
            assert Person.objects.filter(pk__in=[x['person'] for x in rows]).update(consent_revoked_at=now) == 2
        elif state == 'expired':
            assert Listing.objects.filter(pk__in=[x['id'] for x in rows]).update(expires_at=now-timedelta(seconds=1)) == 2
        else:
            assert Listing.objects.filter(pk__in=[x['id'] for x in rows]).update(status=state) == 2
    assert PromotionEntitlement.objects.filter(pk=plan['inactive_rights'][0]).update(suspended_at=now) == 1
    assert PromotionEntitlement.objects.filter(pk=plan['inactive_rights'][1]).update(
        starts_at=now-timedelta(days=2), ends_at=now-timedelta(days=1)) == 1


def native_sponsorships():
    rights = list(PromotionEntitlement.objects.select_related('order'))
    assert len(rights) in (20, 200, 2000)
    listings = {row.pk: row for row in Listing.objects.filter(pk__in=[r.order.listing_id for r in rights])}
    now = timezone.now()
    result = {}
    for right in rights:
        assert right.order.kind in {'top', 'premium'} and right.order.synthetic
        if eligible(right, listings[right.order.listing_id], now):
            result[right.order.listing_id] = right.order.kind
    return result


def _select_mixed_plan(dataset):
    _scope(dataset)
    population = dataset['published']
    assert Listing.objects.filter(status='published').count() == population
    assert not PublicationDirty.objects.exists()
    city = max(dataset['geography'], key=dataset['geography'].get)
    samples = {dataset['sample_ids'][0], dataset['sample_ids'][-1]}
    assert len(samples) == 2
    rights = list(PromotionEntitlement.objects.select_related('order').order_by('order__listing_id'))
    assert len(rights) == population//5
    right_ids = {right.order.listing_id for right in rights}
    query = Listing.objects.filter(status='published', approved_revision__municipality_id=city).exclude(pk__in=samples)
    promoted = list(query.filter(pk__in=right_ids).order_by('pk')[:9])
    organic = list(query.exclude(pk__in=right_ids).order_by('pk')[:7])
    assert len(promoted)==9 and len(organic)==7
    assert all(publicly_visible(row) for row in promoted+organic)
    by_listing = {right.order.listing_id: right.pk for right in rights}
    plan = {'city': city, 'population': population, 'protected_detail_ids': samples, 'mutation_time': timezone.now(),
            'reference_day': timezone.now().astimezone(UTC).date().isoformat(),
            'inactive_rights': [by_listing[row.pk] for row in promoted[7:]],
            'inactive_profiles': [row.pk for row in promoted[7:]],
            'mutations': [{'id': row.pk, 'person': row.person_id, 'kind': kind, 'state': state}
                          for index, state in enumerate(STATES)
                          for kind, row in (('promoted', promoted[index]), ('organic', organic[index]))]}
    assert len({x['id'] for x in plan['mutations']}) == 14
    return plan


def prepare_committed_mixed_plan(dataset):
    """Commit the final synthetic mixture once; never run a counterfactual rollback."""
    plan = _select_mixed_plan(dataset)
    with transaction.atomic():
        _mutate(plan)
    markers = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
    assert {x['listing_id'] for x in markers} == {x['id'] for x in plan['mutations']}
    plan['references'] = {(str(target), text): reference_territorial_order(target, text, promotions=True)
                          for target in dataset['geography'] for text in ('', 'photography')}
    plan['sponsorships'] = native_sponsorships()
    plan['route_geography'] = {str(target): len(plan['references'][(str(target), '')])
                               for target in dataset['geography']}
    assert all(len(plan['references'][(str(target), 'photography')]) == count
               for target, count in plan['route_geography'].items())
    assert sum(plan['route_geography'].values()) == plan['population']-14
    assert len(plan['sponsorships']) == plan['population']//5-9
    assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == markers
    plan['committed_dirty_markers'] = markers
    plan['counterfactual_rollback_used'] = False
    return plan


def prepare_mixed_plan(dataset):
    plan = _select_mixed_plan(dataset)
    population = plan['population']
    before = _snapshot(plan)
    with connection.cursor() as cursor:
        cursor.execute('SELECT last_value FROM listings_publication_generation')
        sequence_before = cursor.fetchone()[0]
    with transaction.atomic():
        _mutate(plan)
        assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {x['id'] for x in plan['mutations']}
        plan['references'] = {(str(target), text): reference_territorial_order(target, text, promotions=True)
                              for target in dataset['geography'] for text in ('', 'photography')}
        plan['sponsorships'] = native_sponsorships()
        plan['route_geography'] = {str(target): len(plan['references'][(str(target), '')])
                                   for target in dataset['geography']}
        assert all(len(plan['references'][(str(target), 'photography')]) == count
                   for target, count in plan['route_geography'].items())
        assert sum(len(ids) for (target, text), ids in plan['references'].items() if not text) == population-14
        assert len(plan['sponsorships']) == population//5-9
        transaction.set_rollback(True)
    assert _snapshot(plan) == before and not PublicationDirty.objects.exists()
    assert Listing.objects.filter(status='published').count() == population
    with connection.cursor() as cursor:
        cursor.execute('SELECT last_value FROM listings_publication_generation')
        sequence_after = cursor.fetchone()[0]
    assert sequence_after > sequence_before
    plan['original'] = before
    plan['rollback_proof'] = {'native_fields_restored': True, 'dirty_empty': True,
                              'sequence_before': sequence_before, 'sequence_after': sequence_after,
                              'sequence_reset': False, 'scope': 'Logical rollback only; aborted tuple work and monotonic sequence advance remain; not clean capacity'}
    return plan


def apply_mixed_plan(dataset, plan):
    _scope(dataset)
    assert not PublicationDirty.objects.exists() and _snapshot(plan) == plan['original']
    assert timezone.now().astimezone(UTC).date().isoformat() == plan['reference_day']
    with transaction.atomic():
        _mutate(plan)
    marks = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
    assert {x['listing_id'] for x in marks} == {x['id'] for x in plan['mutations']}
    assert all(x['generation']>plan['rollback_proof']['sequence_after'] for x in marks)
    return marks
