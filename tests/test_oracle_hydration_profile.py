"""Bounded native-oracle hydration contrast; diagnostic, not application capacity."""

import hashlib
import statistics
import time
from collections import Counter

import pytest
from beta_promotional_load_fixture import (
    prepare_promotional_load,
    redistribute_promotional_geography,
)
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.models import Municipality
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.core.models import Person
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_oracle_hydration_profile(request, settings, record_property):
    assert connection.vendor == 'postgresql' and not settings.PRODUCTION
    settings.PROMOTION_TEST_MODE = True
    dataset = prepare_promotional_load(request, 100)
    cities = list(Municipality.objects.filter(active=True, source__synthetic=True)
                  .order_by('pk').values_list('pk', flat=True)[:2])
    redistribute_promotional_geography(dataset, {cities[0]: 70, cities[1]: 30})
    rights = list(PromotionEntitlement.objects.select_related('order').order_by('order__listing_id'))
    promoted = Listing.objects.get(pk=rights[0].order.listing_id)
    city = promoted.approved_revision.municipality_id
    organic = Listing.objects.filter(status='published', approved_revision__municipality_id=city).exclude(
        pk__in=[r.order.listing_id for r in rights]).order_by('pk').first()
    assert organic is not None
    rows = []

    def measure(hydrate, text):
        counts = Counter()
        driver = 0

        def observe(execute, sql, params, many, context):
            nonlocal driver
            normalized = sql.lower()
            assert 'listings_publicationstate' not in normalized
            assert 'listings_publicationdirty' not in normalized
            counts['queries'] += 1
            counts['select'] += int(normalized.lstrip().startswith('select'))
            assert normalized.lstrip().startswith('select'), 'Oracle must only read native authority'
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                driver += time.perf_counter()-start
        start, cpu = time.perf_counter(), time.process_time()
        with connection.execute_wrapper(observe):
            ids = reference_territorial_order(city, text, promotions=True, hydrate=hydrate)
        return ids, {'hydrate': hydrate, 'text': text, 'queries': counts['queries'],
                     'wall_seconds': time.perf_counter()-start,
                     'cpu_seconds': time.process_time()-cpu, 'driver_seconds': driver,
                     'count': len(ids), 'ordered_ids_sha256': hashlib.sha256(
                         '\n'.join(map(str, ids)).encode()).hexdigest()}

    # ABBA retains both cold and warm observations; no subtraction of instrumentation.
    fresh = None
    for hydrate in (False, True, True, False):
        ids, row = measure(hydrate, 'photography')
        if fresh is None:
            fresh = ids
        assert ids == fresh
        rows.append(row | {'phase': 'fresh'})
    assert promoted.pk in fresh and organic.pk in fresh
    # Fresh invocations must see new native membership and a commercial-only change.
    assert Listing.objects.filter(pk=promoted.pk).update(status='paused') == 1
    assert Person.objects.filter(pk=organic.person_id).update(consent_revoked_at=timezone.now()) == 1
    assert PromotionEntitlement.objects.filter(pk=rights[1].pk).update(suspended_at=timezone.now()) == 1
    dirty_before = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
    assert dirty_before
    for text in ('', 'photography', 'absent-oracle-token'):
        old, old_row = measure(False, text)
        new, new_row = measure(True, text)
        assert new == old and promoted.pk not in new and organic.pk not in new
        if text != 'absent-oracle-token':
            assert len(new) == len(fresh)-2
        else:
            assert new == []
        rows += [old_row | {'phase': 'mutated'}, new_row | {'phase': 'mutated'}]
    assert list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')) == dirty_before
    baseline = [r for r in rows if r['phase']=='fresh' and not r['hydrate']]
    candidate = [r for r in rows if r['phase']=='fresh' and r['hydrate']]
    assert max(r['queries'] for r in candidate) < min(r['queries'] for r in baseline)
    record_property('oracle_hydration_profile', {
        'population': 100, 'rows': rows,
        'fresh_query_reduction': 1-statistics.median(r['queries'] for r in candidate)/statistics.median(r['queries'] for r in baseline),
        'fresh_wall_ratio': statistics.median(r['wall_seconds'] for r in candidate)/statistics.median(r['wall_seconds'] for r in baseline),
        'native_authority_unchanged': True, 'no_projection_reads': True,
        'no_read_repair': True, 'default_adopted': reference_territorial_order.__kwdefaults__['hydrate'],
        'scope': 'Instrumented native oracle only; no HTTP, worker or application performance improvement credited',
    })
