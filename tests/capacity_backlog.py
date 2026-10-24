"""Explicit scaled dirty-state scenario in the verified disposable capacity DB."""

import json
import re
import time
import urllib.error
import urllib.request
from datetime import UTC, timedelta
from pathlib import Path
from urllib.parse import urlencode
from uuid import UUID

from capacity_beta_http import verify_owned_fixture
from django.db import transaction
from django.utils import timezone
from test_promotional_statistics_preparation import reference_territorial_order

from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible
from scripts.benchmark_refresh_intervals import refresh_intervals


def events(directory):
    files = list(Path(directory).glob('*.jsonl'))
    assert len(files) <= 16
    result = []
    for path in files:
        assert path.stat().st_size <= 1024**2
        result.extend(json.loads(line) for line in path.read_bytes().splitlines(keepends=True)
                      if line.endswith(b'\n'))
    return result


def verify_pages(endpoint, dataset, *, excluded=None, pending_city=None, expected_orders=None, sponsorships=None):
    checks = []
    for city in dataset['geography']:
        if pending_city is not None and str(city) != str(pending_city):
            continue
        for text in ('', 'photography'):
            if pending_city is not None and text:
                continue
            expected = (reference_territorial_order(city, text, promotions=True)
                        if expected_orders is None else expected_orders[(str(city), text)])
            last = (len(expected) + 23) // 24
            pages = sorted({1, (last + 1) // 2, last}) if pending_city is None else [1]
            for language in ('es', 'en'):
                for number in pages:
                    path = '/' + language + '/?' + urlencode({'city': city, 'q': text, 'page': number})
                    with urllib.request.urlopen(endpoint.url + path, timeout=65) as response:
                        body = response.read().decode()
                        assert response.status == 200 and response.headers['Cache-Control'] == 'no-store'
                    ids = [UUID(pk) for pk in re.findall(r'<h2><a href="/(?:es|en)/listing/([0-9a-f-]{36})/">', body)]
                    assert ids == expected[(number - 1) * 24:number * 24] and len(ids) == len(set(ids))
                    assert excluded is None or UUID(excluded) not in ids
                    checks.append({'path': path, 'count': len(ids), 'native_count': len(expected),
                                   'ids': list(map(str, ids))})
                    if sponsorships is not None:
                        cards = re.findall(r'<article class="card listing-card">(.*?)</article>', body, re.S)
                        assert len(cards) == len(ids)
                        labels = []
                        for pk, card in zip(ids, cards):
                            assert card.count('<p class="sponsored">') == (1 if pk in sponsorships else 0)
                            label = re.findall(r'<p class="sponsored">[^<]* · (premium|top)</p>', card)
                            assert len(label) == (1 if pk in sponsorships else 0)
                            actual = label[0] if label else None
                            assert actual == sponsorships.get(pk)
                            labels.append(actual)
                        checks[-1]['sponsorship'] = labels

    return checks


def prepare_backlog(dataset):
    verify_owned_fixture()
    assert dataset['synthetic'] and dataset['promotions']['synthetic_only']
    population = dataset['published']
    assert population in (10, 100, 1000, 10000)
    assert population == Listing.objects.filter(status='published').count()
    assert not publication_state.READ_REPAIR and not PublicationDirty.objects.exists()
    rights = list(PromotionEntitlement.objects.filter(order__synthetic=True, order__status='paid')
                  .values_list('order__listing_id', flat=True))
    assert len(rights) == population // 5
    samples = {UUID(dataset['sample_ids'][0]), UUID(dataset['sample_ids'][-1])}
    first_city = max(dataset['geography'], key=dataset['geography'].get)
    candidates = Listing.objects.filter(status='published', approved_revision__municipality_id=first_city)
    withdrawn = (Listing.objects if population == 10 else candidates).filter(
        pk__in=rights).exclude(pk__in=samples).order_by('pk').first()
    assert withdrawn is not None
    withdrawn = withdrawn.pk
    count = 1 if population == 10 else 49
    eligible = (Listing.objects.filter(status='published').exclude(pk__in=rights)
                if population == 10 else candidates)
    unknown = list(eligible.exclude(pk__in=[*samples, withdrawn]).order_by('pk')[:count])
    assert len(unknown) == count and all(publicly_visible(row) for row in unknown)
    # The independent native oracle is expensive and belongs outside the Beat slot.
    # Only the withdrawn member changes membership/order in this fixture mutation.
    references = {}
    for city in dataset['geography']:
        if population > 10 and str(city) != str(first_city):
            continue
        for text in (('',) if population > 10 else ('', 'photography')):
            references[(str(city), text)] = [pk for pk in reference_territorial_order(
                city, text, promotions=True) if pk != withdrawn]
    return {'withdrawn': withdrawn, 'unknown': [row.pk for row in unknown],
            'city': first_city, 'population': population, 'references': references,
            'reference_day': timezone.now().astimezone(UTC).date().isoformat()}


def create_backlog(dataset, plan):
    verify_owned_fixture()
    assert not publication_state.READ_REPAIR and not PublicationDirty.objects.exists()
    assert dataset['published'] == plan['population']
    assert timezone.now().astimezone(UTC).date().isoformat() == plan['reference_day']
    withdrawn, unknown = plan['withdrawn'], plan['unknown']
    count = len(unknown)
    started = time.monotonic()
    until = timezone.now() + timedelta(hours=1)
    with transaction.atomic():
        # Bulk fixture mutation intentionally exercises DB triggers; model signals,
        # real worker and Beat remain untouched. A normal upload may enqueue repair.
        assert Listing.objects.filter(pk=withdrawn).update(status='withdrawn', available_until=None) == 1
        assert Listing.objects.filter(pk__in=unknown).update(available_until=until) == count
    markers = list(PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation'))
    assert {row['listing_id'] for row in markers} == {withdrawn, *unknown}
    assert not publicly_visible(Listing.objects.get(pk=withdrawn))
    # Authority was checked before the slot; the sole eligible mutation is this
    # future timestamp. Verify its full cohort without repeating N authority queries.
    assert Listing.objects.filter(pk__in=unknown, status='published', available_until=until).count() == count
    return {'mutation_started_monotonic': started, 'withdrawn': str(withdrawn),
            'unknown_eligible': [str(pk) for pk in unknown], 'dirty_city': str(plan['city']),
            'prepared_published': plan['population'], 'native_visible_after': plan['population'] - 1,
            'dirty_markers': [{'listing_id': str(row['listing_id']), 'generation': row['generation']} for row in markers]}


def verify_pending(endpoint, dataset, proof, plan):
    proof['pending_pages'] = verify_pages(
        endpoint, dataset, excluded=proof['withdrawn'],
        pending_city=proof['dirty_city'] if dataset['published'] > 10 else None,
        expected_orders=plan['references'])
    proof['pending_page_scope'] = ('dirty-city first page ESEN without text'
                                   if dataset['published'] > 10 else 'all small pages')
    assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {
        UUID(proof['withdrawn']), *(UUID(pk) for pk in proof['unknown_eligible'])}
    for language in ('es', 'en'):
        try:
            urllib.request.urlopen(endpoint.url + '/' + language + '/listing/' + proof['withdrawn'] + '/', timeout=65)
        except urllib.error.HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError('Withdrawn detail remained public')
    assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {
        UUID(proof['withdrawn']), *(UUID(pk) for pk in proof['unknown_eligible'])}
    proof['pending_verified_monotonic'] = time.monotonic()


def verify_repaired(endpoint, dataset, proof, directory):
    deadline = time.monotonic() + 45
    while True:
        ledger = refresh_intervals(events(directory))
        cleared = [row for row in ledger['matched'] if row['state'] == 'SUCCESS'
                   and row['start_monotonic'] >= proof['mutation_started_monotonic']
                   and row.get('cleared', 0) >= len(proof['dirty_markers'])]
        if not PublicationDirty.objects.exists() and cleared:
            break
        assert time.monotonic() < deadline, 'Native worker did not repair the observed backlog'
        time.sleep(.2)
    proof['repair_verified_monotonic'] = time.monotonic()
    proof['refresh_intervals'] = ledger
    proof['repair_tasks'] = [row['id'] for row in cleared]
    proof['repaired_pages'] = verify_pages(endpoint, dataset, excluded=proof['withdrawn'])
    repaired = {row['path']: row for row in proof['repaired_pages']}
    assert all(repaired[row['path']] == row for row in proof['pending_pages'])
    assert not publicly_visible(Listing.objects.get(pk=proof['withdrawn']))
    assert all(publicly_visible(Listing.objects.get(pk=pk)) for pk in proof['unknown_eligible'])
    proof['native_repaired'] = True
