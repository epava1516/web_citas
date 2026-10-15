"""Current page read selection, native tie behavior and post-guard freshness."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import close_old_connections, connection, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import VerificationCheck
from apps.listings import discovery, publication_state
from apps.listings.presentation import describe
from apps.listings.presentation_reads import PagePresentation
from apps.mediafiles.models import Blob, Photo
from scripts.synthetic_load_dataset import clone, populate

pytestmark = pytest.mark.django_db(transaction=True)


def selected_photo(row):
    return row.approved_revision.photos.filter(
        approved=True, removed_at__isnull=True, blob__status='ready').first()


def test_photo_and_check_selection_ties_absence_and_current_status(request, monkeypatch, settings):
    client = request.getfixturevalue('directory')
    rows = list(client.get('/es/').context['page'])
    target = rows[0]
    revision = target.approved_revision
    photo = revision.photos.first()
    initial = photo.created_at
    # Distinct blobs keep the existing active-photo uniqueness constraint.
    def extra(**values):
        blob = clone(photo.blob, sha256=uuid4().hex*2)
        blob.save()
        row = clone(photo, blob_id=blob.pk, **values)
        row.save()
        return row
    earlier = extra(position=photo.position, approved=True)
    Photo.objects.filter(pk=earlier.pk).update(created_at=initial-timedelta(days=1))
    extra(position=0, approved=False)
    extra(position=0, removed_at=timezone.now())
    not_ready = extra(position=0)
    Blob.objects.filter(pk=not_ready.blob_id).update(status='queued')
    for language in ['es', 'en']:
        batch = PagePresentation(rows)
        assert batch.photo(target).pk == selected_photo(target).pk == earlier.pk
        assert batch.describe(target, language) == describe(target, language)
    # Use exact current timestamps to create an actual ordering tie.
    earlier.refresh_from_db()
    Photo.objects.filter(pk=photo.pk).update(created_at=earlier.created_at)
    batch = PagePresentation(rows)
    assert len(batch.photos[revision.pk]) == 2
    assert batch.photo(target).pk == selected_photo(target).pk
    assert batch.stats['photo_native'] == 1
    for ordering in [['-position', '-created_at'], None, []]:
        with monkeypatch.context() as patch:
            patch.setattr(Photo._meta, 'ordering', ordering)
            batch = PagePresentation(rows)
            assert batch.photo(target).pk == selected_photo(target).pk
            assert batch.stats['photo_native'] == 1
    Photo.objects.filter(revision=revision).update(approved=False)
    batch = PagePresentation(rows)
    assert batch.photo(target) is selected_photo(target) is None
    assert batch.stats['photo_native'] == 1
    check = target.person.verificationcheck_set.order_by('-created_at').first()
    later = clone(check, status='failed', provider='synthetic-provider', procedure='age-v1')
    later.save()
    VerificationCheck.objects.filter(pk=later.pk).update(created_at=check.created_at+timedelta(seconds=1))
    settings.VERIFICATION_PROVIDER = 'synthetic-provider'
    batch = PagePresentation(rows)
    assert batch.checks[target.person_id][0].pk == later.pk
    assert batch.describe(target, 'en') == describe(target, 'en')
    assert 'Age: check not accredited' in batch.describe(target, 'en')['checks']
    VerificationCheck.objects.filter(pk=later.pk).update(created_at=check.created_at)
    batch = PagePresentation(rows)
    assert len(batch.checks[target.person_id]) == 2
    assert batch.describe(target, 'en') == describe(target, 'en')
    assert batch.stats['check_native'] == 1
    VerificationCheck.objects.filter(person=target.person).delete()
    batch = PagePresentation(rows)
    assert batch.describe(target, 'en') == describe(target, 'en')
    assert batch.stats['check_native'] == 1


def test_grouped_public_bodies_order_count_and_pages_match_individual(request, monkeypatch, record_property):
    client = request.getfixturevalue('directory')
    populate(50)
    while publication_state.refresh(500):
        pass
    observations = []
    for language in ['es', 'en']:
        for query in ['', 'q=photography&', 'checked=age&']:
            for page in ([1] if query.startswith('checked') else [1,2,3]):
                path = f'/{language}/?{query}page={page}'
                grouped = client.get(path)
                with monkeypatch.context() as patch:
                    patch.setattr(discovery, 'PagePresentation', lambda rows: PagePresentation(rows, grouped=False))
                    individual = client.get(path)
                assert grouped.status_code == individual.status_code == 200
                assert grouped.content == individual.content
                assert grouped.context['page'].paginator.count == individual.context['page'].paginator.count
                assert [x.pk for x in grouped.context['page']] == [x.pk for x in individual.context['page']]
                assert grouped.wsgi_request._publication_route == individual.wsgi_request._publication_route
                observations.append({'language':language,'query':query,'page':page,
                                     'route':grouped.wsgi_request._publication_route['route'],
                                     'presentation':grouped.wsgi_request._presentation_reads})
    record_property('equivalence', observations)


@pytest.mark.parametrize('grouped', [False, True])
def test_committed_changes_after_guard_precede_presentation_reads(request, monkeypatch, grouped, record_property):
    client = request.getfixturevalue('directory')
    target = list(client.get('/es/').context['page'])[0]
    photo = target.approved_revision.photos.first()
    check = target.person.verificationcheck_set.order_by('-created_at').first()
    committed = []

    def update_other_connection():
        close_old_connections()
        try:
            with transaction.atomic():
                Photo.objects.filter(pk=photo.pk).update(approved=False)
                later = clone(check, status='failed', provider='synthetic-provider', procedure='age-v1')
                later.save()
                VerificationCheck.objects.filter(pk=later.pk).update(created_at=check.created_at+timedelta(seconds=1))
            committed.append(True)
        finally:
            connection.close()

    def after_guard(rows):
        assert any(row.pk == target.pk for row in rows)
        # The guard's photo prefetch is deliberately stale; don't consume it.
        captured = next(row for row in rows if row.pk == target.pk)
        assert any(p.pk == photo.pk and p.approved for p in captured.approved_revision._pv_photos)
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(update_other_connection).result(timeout=30)
        return PagePresentation(rows, grouped=grouped)

    monkeypatch.setattr(discovery, 'PagePresentation', after_guard)
    response = client.get('/en/')
    assert committed == [True] and response.status_code == 200
    assert response.wsgi_request._publication_route['route'] == 'state'
    card = next(card for card in response.context['cards'] if card['listing'].pk == target.pk)
    assert card['photo'] is None
    assert 'Age: check not accredited' in card['public']['checks']
    record_property('post_guard_committed_change', {'grouped':grouped,'photo':None,'latest_check':'failed',
        'scope':'Both baseline and candidate read changes committed after guard, never old prefetch. READ COMMITTED; not a request-wide snapshot or a new authority guarantee after the guard.'})


def test_list_prefetch_preserves_relation_snapshot_against_manager_prefetch(request):
    from apps.catalog.models import Category
    from apps.listings.discovery import candidates
    from apps.listings.models import Listing
    from apps.listings.public_validation import PublicationContext

    request.getfixturevalue('directory')
    context = PublicationContext(candidates({}), page_read=True)
    row = context.rows[0]
    legacy = Listing.objects.select_related('approved_revision', 'person__phone_claim').prefetch_related(
        'approved_revision__categories', 'approved_revision__services',
        'approved_revision__travel_areas', 'approved_revision__rates',
    ).get(pk=row.pk)
    for name in ('categories', 'services', 'travel_areas', 'rates'):
        actual = getattr(row.approved_revision, '_pv_' + name)
        assert isinstance(actual, list)
        assert [x.pk for x in actual] == [x.pk for x in getattr(legacy.approved_revision, name).all()]
    category = legacy.approved_revision.categories.all()[0]
    Category.objects.filter(pk=category.pk).update(name_es='Nombre posterior', name_en='Later name')
    for language in ('es', 'en'):
        assert PagePresentation([row]).describe(row, language) == describe(legacy, language)
    fresh = Listing.objects.select_related('approved_revision', 'person__phone_claim').get(pk=row.pk)
    assert 'Later name' in describe(fresh, 'en')['categories']
    assert 'Later name' not in PagePresentation([row]).describe(row, 'en')['categories']
