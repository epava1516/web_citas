"""Committed synthetic mixture before HTTP; native oracle outside arrivals."""

import urllib.error
import urllib.request

from beta_promotional_load_fixture import finalize_promotional_statistics
from capacity_backlog import verify_pages
from capacity_beta_http import verify_owned_fixture
from mixed_state_plan import native_sponsorships, prepare_committed_mixed_plan

from apps.listings import publication_state
from apps.listings.models import PublicationDirty


def prepare(dataset):
    verify_owned_fixture()
    plan = prepare_committed_mixed_plan(dataset)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists() and publication_state.all_state_current()
    assert native_sponsorships() == plan['sponsorships']
    removed_status = sum(v['state'] not in ('expired', 'consent_revoked') for v in plan['mutations'])
    assert removed_status == 10
    # The statistics guard declares SQL status='published', not native visibility.
    stats = finalize_promotional_statistics(dataset | {'published': plan['population']-removed_status})
    assert len(stats['tables']) == 8 and stats['owned_synthetic_postgresql_verified']
    return plan


def verify(endpoint, dataset, plan):
    assert not PublicationDirty.objects.exists()
    assert native_sponsorships() == plan['sponsorships']
    # Recompute native expected order independently on every verification pass.
    pages = verify_pages(endpoint, dataset, sponsorships=plan['sponsorships'])
    for page in pages:
        assert page['native_count'] in plan['route_geography'].values()
    for mutation in plan['mutations']:
        for language in ('es', 'en'):
            try:
                with urllib.request.urlopen(f'{endpoint.url}/{language}/listing/{mutation["id"]}/', timeout=65):
                    raise AssertionError('Committed ineligible detail remained public')
            except urllib.error.HTTPError as error:
                assert error.code == 404
    assert not PublicationDirty.objects.exists()
    return {'pages': pages, 'excluded_detail_404_checks': 28}
