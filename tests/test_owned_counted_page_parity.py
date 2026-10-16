"""Parity controls for a first-page exact count window; no product changes."""
import os
from urllib.parse import urlencode

import pytest
from owned_counted_page import build_counted_page_prototype
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_counted_page_parity(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_counted_page_parity.py'
               for x in request.config.args):
        pytest.skip('Explicit test-only dirty projection validation')
    assert os.environ['LOCAL_CI_POSTGRES_CONTAINER'].startswith('web-modelos-ci-pg-')
    client = request.getfixturevalue('directory')
    dataset = populate(80)
    listing = Listing.objects.select_related('approved_revision').get(pk=dataset['sample_ids'][0])
    native = publication_state._state_page
    counters = {"windows": 0}
    proposed = build_counted_page_prototype(counters)
    cases = []
    for scenario in ['private_draft', 'published_to_paused', 'paused_to_published', 'search_change']:
        Listing.objects.filter(pk=listing.pk).update(status='published')
        if scenario == 'paused_to_published':
            Listing.objects.filter(pk=listing.pk).update(status='paused')
        publication_state.refresh_all()
        assert not PublicationDirty.objects.exists()
        if scenario == 'private_draft':
            Revision.objects.create(listing=listing, manager_version=listing.approved_revision.manager_version)
            # Controlled pending marker; a bare draft insert need not invalidate its approved sibling.
            publication_state.mark([listing.pk])
        elif scenario == 'published_to_paused':
            Listing.objects.filter(pk=listing.pk).update(status='paused')
        elif scenario == 'paused_to_published':
            Listing.objects.filter(pk=listing.pk).update(status='published')
        else:
            Revision.objects.filter(pk=listing.approved_revision_id).update(title='Synthetic dirtyprojectionneedle')
            Listing.objects.filter(pk=listing.pk).update(published_at=None)
        assert PublicationDirty.objects.filter(pk=listing.pk).exists()
        marks = list(PublicationDirty.objects.values_list('pk', 'generation'))
        for language, term in [('es', ''), ('en', 'synthetic'), ('es', 'photography'),
                               ('en', 'dirtyprojectionneedle')]:
            route = '/' + language + '/'
            reference = client.get(route, {'q': term})
            assert reference.status_code == 200
            count = reference.context['page'].paginator.count
            last = reference.context['page'].paginator.num_pages
            for number in sorted({1, min(2, last), last}):
                params = {'q': term, 'page': number}
                with monkeypatch.context() as patch:
                    patch.setattr(publication_state, '_state_page', native)
                    reference = client.get(route, params)
                with monkeypatch.context() as patch:
                    patch.setattr(publication_state, '_state_page', proposed)
                    candidate = client.get(route, params)
                assert candidate.status_code == reference.status_code == 200
                assert candidate.content == reference.content
                assert candidate['Cache-Control'] == reference['Cache-Control'] == 'no-store'
                assert candidate.context['page'].paginator.count == count
                assert [row.pk for row in candidate.context['page']] == [row.pk for row in reference.context['page']]
                assert reference.wsgi_request._publication_route['population'] == 'native_query'
                assert candidate.wsgi_request._publication_route['population'] == 'native_query'
                cases.append({'scenario': scenario, 'route': route + '?' + urlencode(params),
                              'count': count, 'page_size': len(candidate.context['page'])})
        assert list(PublicationDirty.objects.values_list('pk', 'generation')) == marks
    record_property('counted_page_parity', cases)
    record_property('limits', 'Test-only exact count window over unchanged population in own RR; no trigger changes, '
                    'write locks or persisted results. Four mutation scenarios, ESEN, search/list, '
                    'first/intermediate/last pages. Not ROI, concurrency, complete N2 or N3.')

    assert counters["windows"] > 0
    record_property("counted_page_windows", counters["windows"])
