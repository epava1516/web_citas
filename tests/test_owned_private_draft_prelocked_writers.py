"""Bounded old/current control for writers already owning their Listing lock."""
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from threading import Barrier

import pytest
import test_publication_match_dependency_edges as controls
from django.db import connections, transaction
from django.utils import timezone
from private_draft_invalidation_candidate import baseline_installed
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState
from apps.listings.moderation import publicly_visible
from apps.mediafiles.models import Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def owned_explicit(request):
    if not any(str(x).split('::')[0] == 'tests/test_owned_private_draft_prelocked_writers.py' for x in request.config.args):
        pytest.skip('Explicit owned prelocked writer diagnostic only')
    assert os.environ.get('LOCAL_CI_POSTGRES_CONTAINER', '').startswith('web-modelos-ci-pg-')


@pytest.mark.parametrize('schema', ['baseline0020', 'candidate0021'])
def test_prelocked_opposite_photo_writers_complete(request, monkeypatch, schema):
    provider = baseline_installed if schema == 'baseline0020' else nullcontext
    with provider():
        _, rows, photos, _ = controls.setup(request, monkeypatch)
        start = Barrier(2)

        def write(listing_id, photo_id):
            connections.close_all()
            try:
                with transaction.atomic():
                    with connections['default'].cursor() as cursor:
                        cursor.execute("SET LOCAL lock_timeout = '5s'")
                    Listing.objects.select_for_update().get(pk=listing_id)
                    start.wait(timeout=5)
                    return Photo.objects.filter(pk=photo_id).update(removed_at=timezone.now())
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(write, row.pk, photo.pk) for row, photo in zip(rows, photos, strict=True)]
            outcomes = []
            for future in futures:
                try:
                    outcomes.append(future.result(timeout=15))
                except Exception as exc:
                    outcomes.append(f'{type(exc).__name__}: {exc}')
        assert outcomes == [1, 1], outcomes
        assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) >= {row.pk for row in rows}
        publication_state.refresh_all()
        assert not PublicationDirty.objects.exists()
        assert all(not publicly_visible(Listing.objects.get(pk=row.pk)) for row in rows)
        assert not PublicationState.objects.filter(listing_id__in=[r.pk for r in rows], eligible=True).exists()
