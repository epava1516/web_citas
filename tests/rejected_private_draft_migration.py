"""Observe actual draft upload invalidations versus native publication eligibility."""
import json
from importlib import import_module

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment, raw_image, upload  # noqa: F401

from apps.core.models import User
from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.public_validation import PublicationContext
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Match, Photo
from apps.mediafiles.services import process
from apps.mediafiles.tasks import process_blob
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)

def test_private_draft_upload_and_processing_keep_public_state_current(request, monkeypatch, record_property):
    client = request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    queued = []
    monkeypatch.setattr(process_blob, 'delay', lambda pk: queued.append(pk))
    populate(3)
    user = User.objects.get(username='fixture-v1-individual')
    owner = Listing.objects.get(person__individual=user)
    client.force_login(user)
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists() and (not Match.objects.exists())

    def native():
        context = PublicationContext(Listing.objects.filter(pk=owner.pk), page_read=True)
        assert len(context.rows) == 1
        return publication_state.eligible_ignoring_expiry(context.rows[0], context)

    def stats(cursor):
        cursor.execute('SELECT pg_stat_force_next_flush()')
        cursor.execute('SELECT pg_stat_clear_snapshot()')
        cursor.execute("SELECT funcname,calls,total_time FROM pg_stat_user_functions WHERE schemaname='public' AND (funcname LIKE 'lpd_%' OR funcname='listings_publication_mark')")
        return {name: {'calls': calls, 'ms': elapsed} for name, calls, elapsed in cursor.fetchall()}
    rows = []
    before_native = native()
    assert before_native
    with connection.cursor() as cursor:
        cursor.execute("SET track_functions='all'")
        try:
            for phase in ['ingest', 'process']:
                PublicationDirty.objects.all().delete()
                before = stats(cursor)
                if phase == 'ingest':
                    assert upload(client, draft, raw_image(782134)).status_code == 302
                    photo = Photo.objects.get(revision=draft)
                    assert len(queued) == 1 and str(photo.blob_id) == queued[0]
                else:
                    process(photo.blob_id)
                    photo.blob.refresh_from_db()
                    assert photo.blob.status == 'ready'
                after = stats(cursor)
                after_native = native()
                assert after_native == before_native
                assert not Match.objects.exists()
                dirty = set(PublicationDirty.objects.values_list('listing_id', flat=True))
                assert not dirty
                changed = {name: {'calls': v['calls'] - before.get(name, {}).get('calls', 0), 'ms': v['ms'] - before.get(name, {}).get('ms', 0)} for name, v in after.items() if v['calls'] > before.get(name, {}).get('calls', 0)}
                rows.append({'phase': phase, 'dirty_count': len(dirty), 'dirty_empty': True, 'native_eligible_unchanged': True, 'matches': 0, 'functions': changed})
        finally:
            cursor.execute("SET track_functions='none'")
    record_property('private_draft_actual', json.dumps(rows))
    record_property('limits', 'Actual migrated SQL; own synthetic3 PG profiles, actual ingest/process sequentially without Celery. Native eligibility unchanged and no dirty on independent draft; not a p95 proof.')

@pytest.mark.parametrize('change', ['approved_photo', 'shared_blob', 'revision_status', 'revision_title', 'revision_delete'])
def test_private_draft_keeps_relevant_and_unknown_writes_dirty(request, monkeypatch, change):
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    owner = Listing.objects.filter(status='published').first()
    photo = owner.approved_revision.photos.first()
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    Photo.objects.create(revision=draft, blob=photo.blob)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    if change == 'approved_photo':
        Photo.objects.filter(pk=photo.pk).update(comparison_complete=False)
    elif change == 'shared_blob':
        from apps.mediafiles.models import Blob
        Blob.objects.filter(pk=photo.blob_id).update(status='failed')
    elif change == 'revision_status':
        Revision.objects.filter(pk=draft.pk).update(status='pending')
    elif change == 'revision_title':
        Revision.objects.filter(pk=draft.pk).update(title='Synthetic changed draft content')
    else:
        draft.delete()
    assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()

@pytest.mark.parametrize('side', ['photo', 'candidate'])
def test_private_draft_retains_match_counterpart_invalidation(request, monkeypatch, side):
    from django.utils import timezone
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    rows = list(Listing.objects.filter(status='published').order_by('pk')[:2])
    owner, peer = rows
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    photo = Photo.objects.create(revision=draft, blob=owner.approved_revision.photos.first().blob)
    other = peer.approved_revision.photos.first()
    args = {'photo': photo, 'candidate': other} if side == 'photo' else {'photo': other, 'candidate': photo}
    Match.objects.create(**args, method='sha256', decision='conflict', resolved_at=timezone.now())
    publication_state.refresh_all()
    Photo.objects.filter(pk=photo.pk).update(removed_at=timezone.now())
    assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {owner.pk, peer.pk}
    assert publication_state.eligible_ignoring_expiry((context := PublicationContext(Listing.objects.filter(pk=peer.pk), page_read=True)).rows[0], context)

def test_private_draft_keeps_rights_references_conservative(request, monkeypatch):
    from test_photo_disposition_authority import ledger
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    owner = Listing.objects.filter(status='published').first()
    execution = ledger(owner.person)
    execution.corrected_revision_id = owner.approved_revision_id
    execution.save(update_fields=['corrected_revision'])
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    photo = Photo.objects.create(revision=draft, blob=owner.approved_revision.photos.first().blob)
    publication_state.refresh_all()
    Photo.objects.filter(pk=photo.pk).update(comparison_complete=True)
    assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()
    PublicationDirty.objects.all().delete()
    Revision.objects.filter(pk=draft.pk).update(edit_version=2)
    assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()

def test_private_draft_bulk_filters_only_private_rows_and_rollback_is_atomic(request, monkeypatch):
    from django.db import transaction
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    owner, peer = list(Listing.objects.filter(status='published').order_by('pk')[:2])
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    photo = Photo.objects.create(revision=draft, blob=owner.approved_revision.photos.first().blob)
    peer_photo = peer.approved_revision.photos.first()
    own_photo = owner.approved_revision.photos.first()
    publication_state.refresh_all()
    Photo.objects.filter(pk__in=[photo.pk, peer_photo.pk]).update(comparison_complete=False)
    assert set(PublicationDirty.objects.values_list('listing_id', flat=True)) == {peer.pk}
    PublicationDirty.objects.all().delete()

    class Rollback(Exception):
        pass
    with pytest.raises(Rollback), transaction.atomic():
        Photo.objects.filter(pk=own_photo.pk).update(comparison_complete=False)
        assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()
        raise Rollback
    own_photo.refresh_from_db()
    assert own_photo.comparison_complete and (not PublicationDirty.objects.exists())


migration = import_module('apps.listings.migrations.0021_private_draft_publication_dependencies')


def assert_runtime_sql():
    definitions = {
        'listings_publication_private_draft(uuid)': migration.PRIVATE,
        'listings_publication_lock(uuid[])': migration.LOCK,
        'listings_publication_mark(uuid[])': migration.MARK,
        **{f'lpd_{table}()': source for table, source in migration.TRIGGERS.items()},
    }
    with connection.cursor() as cursor:
        for name, source in definitions.items():
            cursor.execute('SELECT prosrc FROM pg_proc WHERE oid=%s::regprocedure', [name])
            assert cursor.fetchone()[0] == source.split('$$')[1]


@pytest.fixture(autouse=True)
def actual_migrated_schema(transactional_db):
    assert_runtime_sql()


def test_private_draft_upgrade_and_reverse_restore_exact_behavior(request, monkeypatch):
    from django.db.migrations.executor import MigrationExecutor
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    owner = Listing.objects.filter(status='published').first()
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    publication_state.refresh_all()
    leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
    try:
        MigrationExecutor(connection).migrate([('listings', '0020_publication_match_counterparts')])
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regprocedure('listings_publication_private_draft(uuid)'),to_regprocedure('listings_publication_lock(uuid[])')")
            assert cursor.fetchone() == (None, None)
        Revision.objects.filter(pk=draft.pk).update(edit_version=2)
        assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()
        publication_state.refresh_all()
        MigrationExecutor(connection).migrate(leaves)
        assert_runtime_sql()
        Revision.objects.filter(pk=draft.pk).update(edit_version=3)
        assert not PublicationDirty.objects.exists()
    finally:
        MigrationExecutor(connection).migrate(leaves)
        assert_runtime_sql()
