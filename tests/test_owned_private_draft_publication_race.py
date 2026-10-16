"""Dependency expansion race: an uncommitted private Blob becomes public."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from queue import Queue
from threading import Event
from uuid import uuid4

import pytest
from django.db import connection, connections, transaction
from private_draft_invalidation_candidate import fenced_installed as installed
from test_discovery import directory  # noqa: F401
from test_photo_reuse_races import observe_blocked
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState
from apps.listings.moderation import publicly_visible
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Blob
from scripts.synthetic_load_dataset import clone

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('variant', ['current', 'candidate'])
def test_private_write_concurrent_publication_keeps_negative_state_exact(request, monkeypatch, record_property, variant):
    if not any(str(x).split('::')[0] == 'tests/test_owned_private_draft_publication_race.py' for x in request.config.args):
        pytest.skip('Explicit owned prototype concurrency diagnostic only')
    assert os.environ.get('LOCAL_CI_POSTGRES_CONTAINER', '').startswith('web-modelos-ci-pg-')
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    owner = Listing.objects.filter(status='published').first()
    original = owner.approved_revision
    draft = clone(original, status='draft')
    draft.save()
    for name in ['categories', 'services', 'travel_areas']:
        getattr(draft, name).set(getattr(original, name).all())
    for rate in original.rates.all():
        clone(rate, revision_id=draft.pk).save()
    old_photo = original.photos.first()
    blob = clone(old_photo.blob, sha256=uuid4().hex * 2, status='queued')
    blob.save()
    clone(old_photo, revision_id=draft.pk, blob_id=blob.pk, comparison_complete=True).save()
    publication_state.refresh_all()
    assert publicly_visible(Listing.objects.get(pk=owner.pk))
    updated, release, refreshed = Event(), Event(), Event()
    pids = Queue()
    def writer():
        connections.close_all()
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pids.put(('writer', cursor.fetchone()[0]))
                Blob.objects.filter(pk=blob.pk).update(status='ready')
                updated.set()
                assert release.wait(20), 'Private writer release not received'
        finally:
            connections.close_all()
    def publish_and_refresh():
        connections.close_all()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT pg_backend_pid()')
                pids.put(('publisher', cursor.fetchone()[0]))
            with transaction.atomic():
                type(draft).objects.filter(pk=draft.pk).update(status='approved')
                Listing.objects.filter(pk=owner.pk).update(approved_revision_id=draft.pk)
            publication_state.refresh_all()
            refreshed.set()
        finally:
            connections.close_all()
    with installed() if variant == 'candidate' else nullcontext():
        with ThreadPoolExecutor(max_workers=2) as pool:
            write_future = pool.submit(writer)
            try:
                assert updated.wait(10)
                publish_future = pool.submit(publish_and_refresh)
                workers = dict(pids.get(timeout=5) for _ in range(2))
                observe_blocked(workers['publisher'], workers['writer'])
            finally:
                release.set()
            write_future.result(timeout=20)
            publish_future.result(timeout=20)
        native = publicly_visible(Listing.objects.get(pk=owner.pk))
        stored = PublicationState.objects.get(listing=owner).eligible
        dirty = PublicationDirty.objects.filter(listing_id=owner.pk).exists()
        record_property('private_publication_race', json.dumps({'variant':variant, 'native':native,
                         'stored':stored, 'dirty':dirty, 'writer_released':release.is_set(),
                         'refreshed':refreshed.is_set(), 'scope':'Synthetic valid FK clone, direct DB publication for trigger contract, not moderation approval evidence.'}))
        assert native
        assert dirty or stored == native, 'Uncommitted private write lost invalidation after concurrent publication'
