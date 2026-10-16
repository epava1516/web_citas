"""Owned prototype: retain refresh/foreign-key lock order and new dependency safety."""
import os
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event

import pytest
import test_publication_match_dependency_edges as match_controls
import test_publication_refresh_lock_order as reference_controls
from django.db import connection, connections, transaction
from django.utils import timezone
from private_draft_invalidation_candidate import fenced_installed
from test_discovery import directory  # noqa: F401
from test_photo_reuse_races import observe_blocked
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision
from apps.listings.moderation import publicly_visible
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Match, Photo

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def owned_explicit(request, monkeypatch):
    if not any(str(x).split('::')[0] == 'tests/test_owned_private_draft_fenced_concurrency.py' for x in request.config.args):
        pytest.skip('Explicit owned prototype concurrency controls only')
    assert os.environ.get('LOCAL_CI_POSTGRES_CONTAINER', '').startswith('web-modelos-ci-pg-')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    request.getfixturevalue('directory')


@pytest.mark.parametrize('reference', ['listing', 'revision'])
def test_fenced_locked_reference_still_defers_refresh(request, monkeypatch, reference):
    with fenced_installed():
        reference_controls.test_locked_reference_defers_refresh_without_losing_dirty_generation(
            request, monkeypatch, reference)


def test_fenced_refresher_wait_preserves_new_generation(request, monkeypatch):
    with fenced_installed():
        match_controls.test_counterpart_generation_survives_observed_refresh_wait(request, monkeypatch)


def test_fenced_opposite_photo_writes_complete(request, monkeypatch):
    with fenced_installed():
        match_controls.test_concurrent_opposite_photo_writes_drain_without_losing_marks(request, monkeypatch)


@pytest.mark.parametrize('isolation', ['REPEATABLE READ', 'SERIALIZABLE'])
def test_fenced_stronger_isolation_keeps_conservative_dirty(isolation):
    owner = Listing.objects.filter(status='published').first()
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    photo = Photo.objects.create(revision=draft, blob=owner.approved_revision.photos.first().blob)
    publication_state.refresh_all()
    with fenced_installed(), transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL ' + isolation)
        Photo.objects.filter(pk=photo.pk).update(comparison_complete=True)
        assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()


def test_fenced_new_match_waits_for_private_photo_commit():
    owner, peer = list(Listing.objects.filter(status='published').order_by('pk')[:2])
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    photo = Photo.objects.create(revision=draft, blob=owner.approved_revision.photos.first().blob)
    other = peer.approved_revision.photos.first()
    publication_state.refresh_all()
    updated, release = Event(), Event()
    pids = Queue()
    def writer():
        connections.close_all()
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pids.put(('writer', cursor.fetchone()[0]))
                Photo.objects.filter(pk=photo.pk).update(removed_at=timezone.now())
                updated.set()
                assert release.wait(20)
        finally:
            connections.close_all()
    def new_match():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                pids.put(('match', cursor.fetchone()[0]))
            Match.objects.create(photo_id=photo.pk, candidate_id=other.pk, method='sha256',
                                 decision='conflict', resolved_at=timezone.now())
            publication_state.refresh_all()
        finally:
            connections.close_all()
    with fenced_installed(), ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(writer)
        try:
            assert updated.wait(10)
            second = pool.submit(new_match)
            workers = dict(pids.get(timeout=5) for _ in range(2))
            observe_blocked(workers['match'], workers['writer'])
        finally:
            release.set()
        first.result(timeout=20)
        second.result(timeout=20)
        assert publicly_visible(Listing.objects.get(pk=peer.pk))
        assert PublicationState.objects.get(listing=peer).eligible
        assert not PublicationDirty.objects.exists()
