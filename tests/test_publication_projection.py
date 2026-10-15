"""Maintained projection parity, invalidation and current-source copies."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import connection, connections, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import discovery, publication_state
from apps.listings.discovery import candidates
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def target():
    return Listing.objects.filter(status='published').select_related('approved_revision').first()


def copied(listing_id):
    listing = Listing.objects.select_related('approved_revision').get(pk=listing_id)
    state = PublicationState.objects.get(pk=listing_id)
    assert state.expires_at == listing.expires_at
    assert state.published_at == listing.published_at
    assert state.revision_id == listing.approved_revision_id
    assert state.search_document == (
        listing.approved_revision.search_document if listing.approved_revision else None
    )
    return state


def test_projection_copies_source_and_updates_without_unnecessary_rewrites(request):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    listing = target()
    copied(listing.pk)
    mutations = [
        (Listing, listing.pk, {'expires_at': timezone.now() + timedelta(days=40)}),
        (Listing, listing.pk, {'published_at': None}),
        (Revision, listing.approved_revision_id, {'title': 'Synthetic projection title updated'}),
        (Revision, listing.approved_revision_id, {'description': 'Synthetic description changed for projection'}),
        (Revision, listing.approved_revision_id, {'description_alternative': 'Alternative projection description'}),
        (Revision, listing.approved_revision_id, {'content_language': 'en'}),
        (Listing, listing.pk, {'status': 'paused'}),
    ]
    for model, pk, values in mutations:
        model.objects.filter(pk=pk).update(**values)
        assert PublicationDirty.objects.filter(pk=listing.pk).exists()
        publication_state.refresh_all()
        copied(listing.pk)
    assert not copied(listing.pk).eligible
    with connection.cursor() as cursor:
        cursor.execute('SELECT xmin::text FROM listings_publicationstate WHERE listing_id=%s', [listing.pk])
        before = cursor.fetchone()[0]
    publication_state.mark([listing.pk])
    publication_state.refresh_all()
    with connection.cursor() as cursor:
        cursor.execute('SELECT xmin::text FROM listings_publicationstate WHERE listing_id=%s', [listing.pk])
        assert cursor.fetchone()[0] == before
    Listing.objects.filter(pk=listing.pk).update(approved_revision=None)
    publication_state.refresh_all()
    assert not copied(listing.pk).eligible


def test_projection_matches_original_population_html_pages_and_rank(request, monkeypatch):
    client = request.getfixturevalue('directory')
    dataset = populate(50)
    Listing.objects.filter(pk__in=dataset['sample_ids'][:2]).update(published_at=None)
    publication_state.refresh_all()
    original = discovery.candidates

    def without_projection(*args, **kwargs):
        query = original(*args, **kwargs)
        query.__dict__.pop('_publication_projection', None)
        return query

    for language in ('es', 'en'):
        for text in ('', 'photography', 'synthetic', 'zzznomatchproof'):
            for number in (1, 2, 3):
                params = {'q': text, 'page': number}
                projected = client.get('/' + language + '/', params)
                with monkeypatch.context() as patch:
                    patch.setattr(discovery, 'candidates', without_projection)
                    native = client.get('/' + language + '/', params)
                assert projected.status_code == native.status_code
                assert projected.content == native.content
                if projected.status_code == 200:
                    assert projected.wsgi_request._publication_route['population'] == 'projection'
                    assert native.wsgi_request._publication_route['population'] == 'native_query'
                    assert projected.context['page'].paginator.count == native.context['page'].paginator.count
                    assert [x.pk for x in projected.context['page']] == [x.pk for x in native.context['page']]


def test_projection_is_closed_for_filters_clones_dirty_stale_and_inherited_transactions(request):
    request.getfixturevalue('directory')
    publication_state.refresh_all()

    def route(query, *, checked=()):
        observation = {}
        page = publication_state.state_page(query, 1, checked=checked, observation=observation)
        assert page is not None
        return observation['population']

    assert route(candidates({})) == 'projection'
    assert route(candidates({'q': 'photography'})) == 'projection'
    for query in (candidates({}).all(), candidates({}, stored_search=False),
                  candidates({'profile': ['woman']}), candidates({'available': True}),
                  candidates({'reception': True}), candidates({'q': 'photography', 'travel': True})):
        assert route(query) == 'native_query'
    assert route(candidates({}), checked=('age',)) == 'native_query'
    with transaction.atomic():
        assert route(candidates({})) == 'native_query'
    listing = target()
    publication_state.mark([listing.pk])
    assert route(candidates({})) == 'native_query'
    publication_state.refresh_all()
    PublicationState.objects.filter(pk=listing.pk).update(rules_version='old-version')
    assert route(candidates({})) == 'native_query'
    publication_state.mark_stale()
    publication_state.refresh_all()
    PublicationState.objects.filter(pk=listing.pk).delete()
    assert route(candidates({})) == 'native_query'


def test_sweep_detects_projection_fields_even_when_eligibility_has_not_changed(request):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    listing = target()
    mutations = ({'expires_at': None}, {'published_at': None},
                 {'search_document': "'wrong':1"}, {'revision_id': None})
    assert listing.published_at is not None
    for values in mutations:
        PublicationState.objects.filter(pk=listing.pk).update(**values)
        assert publication_state.sweep() == 1
        assert PublicationDirty.objects.filter(pk=listing.pk).exists()
        publication_state.refresh_all()
        copied(listing.pk)
        assert publication_state.sweep() == 0


def test_projection_reader_snapshot_then_committed_text_change_stays_dirty_and_fresh(
    request, monkeypatch,
):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    listing = target()
    paginator = publication_state.Paginator
    called = []

    def change_text():
        try:
            Revision.objects.filter(pk=listing.approved_revision_id).update(
                title='Synthetic projectionneedle photography',
            )
        finally:
            connections.close_all()

    def after_snapshot(query, per_page):
        if not called:
            called.append(True)
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(change_text).result(timeout=15)
        return paginator(query, per_page)

    with monkeypatch.context() as patch:
        patch.setattr(publication_state, 'Paginator', after_snapshot)
        page = publication_state.state_page(candidates({'q': 'projectionneedle'}), 1)
    assert called and page.paginator.count == 0
    assert PublicationDirty.objects.filter(pk=listing.pk).exists()
    observation = {}
    fresh = publication_state.state_page(candidates({'q': 'projectionneedle'}), 1, observation=observation)
    assert observation['population'] == 'native_query' and fresh.paginator.count == 1
    assert [row.pk for row in fresh] == [listing.pk]
    publication_state.refresh_all()
    copied(listing.pk)
    fresh = publication_state.state_page(candidates({'q': 'projectionneedle'}), 1, observation=observation)
    assert observation['population'] == 'projection' and fresh.paginator.count == 1
