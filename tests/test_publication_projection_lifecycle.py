"""Installed migration, clock expiry and transactional refresh projection races."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import connection, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_projection import copied, target

from apps.listings import publication_state
from apps.listings.discovery import candidates
from apps.listings.models import Listing, PublicationDirty, PublicationState, Revision

pytestmark = pytest.mark.django_db(transaction=True)


def test_installed_projection_upgrade_invalidates_existing_states_before_use(request):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    executor = MigrationExecutor(connection)
    leaves = executor.loader.graph.leaf_nodes()
    previous = [('listings', '0018_listing_public_page_order')]
    try:
        executor.migrate(previous)
        old = executor.loader.project_state(previous).apps
        old.get_model('listings', 'PublicationState').objects.update(rules_version='before-projection')
        old.get_model('listings', 'PublicationDirty').objects.all().delete()
        executor = MigrationExecutor(connection)
        executor.migrate(leaves)
        assert PublicationDirty.objects.count() == Listing.objects.count()
        observation = {}
        assert publication_state.state_page(candidates({}), 1, observation=observation) is not None
        assert observation['population'] == 'native_query'
        publication_state.mark_stale()
        publication_state.refresh_all()
        assert not PublicationDirty.objects.exists()
        for pk in Listing.objects.values_list('pk', flat=True):
            copied(pk)
        assert publication_state.state_page(candidates({}), 1, observation=observation) is not None
        assert observation['population'] == 'projection'
    finally:
        MigrationExecutor(connection).migrate(leaves)


def test_projection_strict_expiry_cutoff_and_expiry_during_guard_falls_back(request, monkeypatch):
    request.getfixturevalue('directory')
    listing = target()
    boundary = timezone.now() + timedelta(seconds=30)
    Listing.objects.filter(pk=listing.pk).update(expires_at=boundary)
    publication_state.refresh_all()
    count = publication_state.state_page(candidates({}), 1).paginator.count
    with monkeypatch.context() as patch:
        patch.setattr(timezone, 'now', lambda: boundary)
        query = candidates({})
        projected = publication_state.state_page(query, 1)
        query = candidates({})
        query.__dict__.pop('_publication_projection')
        native = publication_state.state_page(query, 1)
        assert projected.paginator.count == native.paginator.count == count - 1
        assert [x.pk for x in projected] == [x.pk for x in native]
    context = publication_state.PublicationContext
    with monkeypatch.context() as patch:
        patch.setattr(timezone, 'now', lambda: boundary - timedelta(seconds=1))

        def expire_before_guard(*args, **kwargs):
            patch.setattr(timezone, 'now', lambda: boundary)
            return context(*args, **kwargs)

        patch.setattr(publication_state, 'PublicationContext', expire_before_guard)
        observation = {}
        assert publication_state.state_page(candidates({}), 1, observation=observation) is None
        assert observation['reason'] == 'state_page_guard_changed'
    assert PublicationDirty.objects.filter(pk=listing.pk).exists()


def test_refresher_copy_precedes_waiting_writer_and_keeps_new_generation(request, monkeypatch):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    listing = target()
    before = copied(listing.pk)
    publication_state.mark([listing.pk])
    with connection.cursor() as cursor:
        cursor.execute('SELECT pg_backend_pid()')
        root_pid = cursor.fetchone()[0]
    ready, start = threading.Event(), threading.Event()
    writer_pid, futures = [], []
    original_context = publication_state.PublicationContext

    def writer():
        try:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    writer_pid.append(cursor.fetchone()[0])
                ready.set()
                assert start.wait(5)
                Listing.objects.filter(pk=listing.pk).update(
                    expires_at=before.expires_at + timedelta(days=1), published_at=timezone.now(),
                )
                Revision.objects.filter(pk=listing.approved_revision_id).update(
                    title='Synthetic projectionwriterneedle photography',
                )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        def paused_context(*args, **kwargs):
            context = original_context(*args, **kwargs)
            futures.append(pool.submit(writer))
            assert ready.wait(5)
            start.set()
            deadline = time.monotonic() + 5
            while True:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_blocking_pids(%s)', [writer_pid[0]])
                    blockers = cursor.fetchone()[0]
                if root_pid in blockers:
                    break
                assert time.monotonic() < deadline, 'Writer must wait on claimed dirty generation'
                time.sleep(0.01)
            return context

        with monkeypatch.context() as patch:
            patch.setattr(publication_state, 'PublicationContext', paused_context)
            assert publication_state.refresh(10) == 1
        assert len(futures) == 1
        futures[0].result(timeout=15)
    after = PublicationState.objects.get(pk=listing.pk)
    assert after.expires_at == before.expires_at
    assert after.published_at == before.published_at
    assert after.search_document == before.search_document
    assert PublicationDirty.objects.filter(pk=listing.pk).exists()
    observation = {}
    fresh = publication_state.state_page(candidates({'q': 'projectionwriterneedle'}), 1,
                                         observation=observation)
    assert observation['population'] == 'native_query' and fresh.paginator.count == 1
    publication_state.refresh_all()
    copied(listing.pk)
    assert not PublicationDirty.objects.exists()
    fresh = publication_state.state_page(candidates({'q': 'projectionwriterneedle'}), 1,
                                         observation=observation)
    assert observation['population'] == 'projection' and fresh.paginator.count == 1
