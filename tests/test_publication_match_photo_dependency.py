"""Photo writes invalidate the opposite listing whose conflict reads that photo."""
import json

import pytest
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision
from apps.listings.moderation import publicly_visible
from apps.mediafiles.models import Match, Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('mutation', ['photo_removed', 'revision_rights_stage'])
@pytest.mark.parametrize('changed_side', ['photo', 'candidate'])
def test_removed_conflict_photo_restores_other_listing_without_refresher(
    request, monkeypatch, record_property, changed_side, mutation,
):
    client = request.getfixturevalue('directory')
    rows = list(Listing.objects.filter(status='published').order_by('pk')[:2])
    assert len(rows) == 2 and all(publicly_visible(row) for row in rows)
    photos = [row.approved_revision.photos.filter(removed_at__isnull=True).first() for row in rows]
    assert all(photos)
    Match.objects.update_or_create(
        photo=photos[0], candidate=photos[1],
        defaults={'method':'sha256', 'decision':'conflict', 'resolved_at':timezone.now()},
    )
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    assert all(not publicly_visible(Listing.objects.get(pk=row.pk)) for row in rows)
    assert not PublicationState.objects.filter(listing_id__in=[row.pk for row in rows], eligible=True).exists()
    changed = 0 if changed_side == 'photo' else 1
    target = rows[1-changed]
    # Deliberately bypass signals: database invalidation is part of the contract.
    if mutation == 'photo_removed':
        Photo.objects.filter(pk=photos[changed].pk).update(removed_at=timezone.now())
    else:
        Revision.objects.filter(pk=rows[changed].approved_revision_id).update(status='rights-stage')
    assert publicly_visible(Listing.objects.get(pk=target.pk))
    reports=[]
    for language in ('es','en'):
        stored=client.get('/'+language+'/')
        with monkeypatch.context() as patch:
            patch.setattr(publication_state,'state_page',lambda *args,**kwargs:None)
            native=client.get('/'+language+'/')
        reports.append({'language':language,'stored_count':stored.context['page'].paginator.count,
                        'native_count':native.context['page'].paginator.count,
                        'target_dirty':PublicationDirty.objects.filter(listing_id=target.pk).exists(),
                        'target_in_native':target.pk in [r.pk for r in native.context['page']]})
        record_property('photo_match_dependency_'+language,json.dumps(reports[-1]))
        assert stored.status_code == native.status_code == 200
        assert stored.content == native.content
    assert all(r['target_dirty'] and r['target_in_native'] for r in reports)
    publication_state.refresh_all()
    assert PublicationState.objects.get(listing_id=target.pk).eligible
    if mutation == 'photo_removed':
        Photo.objects.filter(pk=photos[changed].pk).update(removed_at=None)
    else:
        Revision.objects.filter(pk=rows[changed].approved_revision_id).update(status='approved')
    assert PublicationDirty.objects.filter(listing_id=target.pk).exists()
    assert not publicly_visible(Listing.objects.get(pk=target.pk))
    for language in ('es','en'):
        stored=client.get('/'+language+'/')
        with monkeypatch.context() as patch:
            patch.setattr(publication_state,'state_page',lambda *args,**kwargs:None)
            native=client.get('/'+language+'/')
        assert stored.status_code == native.status_code == 200
        assert stored.content == native.content
        assert target.pk not in [r.pk for r in stored.context['page']]

