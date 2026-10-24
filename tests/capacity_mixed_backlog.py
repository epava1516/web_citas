"""Mixed100/1000/10000 functional HTTP only; independent native planning and final oracle."""

import time
import urllib.error
import urllib.request

from capacity_backlog import events
from capacity_backlog import verify_pages as base_pages
from capacity_beta_http import verify_owned_fixture
from django.utils import timezone
from mixed_state_plan import apply_mixed_plan, native_sponsorships, prepare_mixed_plan

from apps.listings.models import Listing, PublicationDirty
from apps.listings.moderation import publicly_visible
from scripts.benchmark_refresh_intervals import refresh_intervals


def verify_pages(endpoint, dataset):
    return base_pages(endpoint, dataset, sponsorships=native_sponsorships())


def prepare_backlog(dataset):
    verify_owned_fixture()
    return prepare_mixed_plan(dataset)


def create_backlog(dataset, plan):
    verify_owned_fixture()
    started = time.monotonic()
    markers = apply_mixed_plan(dataset, plan)
    return {'scenario': 'mixed_states', 'mutation_started_monotonic': started,
            'prepared_published': plan['population'], 'native_visible_after': plan['population']-14, 'dirty_city': str(plan['city']),
            'excluded': [str(x['id']) for x in plan['mutations']],
            'mutations': [{k: str(v) for k, v in x.items() if k!='person'} for x in plan['mutations']],
            'inactive_profiles': list(map(str, plan['inactive_profiles'])),
            'dirty_markers': [{'listing_id': str(x['listing_id']), 'generation': x['generation']} for x in markers],
            'rollback_proof': plan['rollback_proof'],
            'expected_sponsorships': {str(k): v for k, v in plan['sponsorships'].items()}}


def _marks(proof):
    observed = [{'listing_id': str(x['listing_id']), 'generation': x['generation']}
                for x in PublicationDirty.objects.order_by('listing_id').values('listing_id', 'generation')]
    assert observed == proof['dirty_markers']


def verify_pending(endpoint, dataset, proof, plan):
    _marks(proof)
    proof['pending_pages'] = base_pages(endpoint, dataset, pending_city=plan['city'],
                                       expected_orders=plan['references'], sponsorships=plan['sponsorships'])
    proof['pending_page_scope'] = 'dirty-city first page ESEN without text;14 excluded details ESEN'
    for pk in proof['excluded']:
        for language in ('es', 'en'):
            try:
                with urllib.request.urlopen(f'{endpoint.url}/{language}/listing/{pk}/', timeout=65):
                    raise AssertionError('Mixed ineligible detail remained public')
            except urllib.error.HTTPError as error:
                assert error.code == 404
    _marks(proof)
    proof['excluded_detail_404_checks'] = 28
    proof['pending_verified_monotonic'] = time.monotonic()


def verify_repaired(endpoint, dataset, proof, directory):
    while True:
        ledger = refresh_intervals(events(directory))
        cleared = [row for row in ledger['matched'] if row['state']=='SUCCESS'
                   and row['published_monotonic']>=proof['mutation_started_monotonic']
                   and row.get('cleared', 0)>=14 and row.get('dirty_after')==0 and 'snapshot_error' not in row]
        if cleared and not PublicationDirty.objects.exists():
            break
        assert time.monotonic()-proof['mutation_started_monotonic']<45, 'Native mixed repair exceeded45s from mutation'
        time.sleep(.2)
    proof['repair_verified_monotonic'] = time.monotonic()
    assert proof['repair_verified_monotonic']-proof['mutation_started_monotonic']<=45
    proof['refresh_intervals'] = ledger
    proof['repair_tasks'] = [row['id'] for row in cleared]
    sponsorships = native_sponsorships()
    assert {str(k): v for k, v in sponsorships.items()} == proof['expected_sponsorships']
    proof['repaired_pages'] = base_pages(endpoint, dataset, sponsorships=sponsorships)
    repaired = {row['path']: row for row in proof['repaired_pages']}
    assert all(repaired[row['path']]==row for row in proof['pending_pages'])
    assert not any(pk in row['ids'] for row in proof['repaired_pages'] for pk in proof['excluded'])
    assert all(not publicly_visible(Listing.objects.get(pk=pk)) for pk in proof['excluded'])
    for pk in proof['inactive_profiles']:
        assert publicly_visible(Listing.objects.get(pk=pk)) and pk not in proof['expected_sponsorships']
    proof['native_repaired'] = True
    proof['native_oracle_completed_at'] = timezone.now().isoformat()
