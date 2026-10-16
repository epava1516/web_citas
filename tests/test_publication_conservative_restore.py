"""Corrective migration restores baseline SQL and private-write invalidations."""
from importlib import import_module

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from apps.listings.tasks import refresh_publication_state
from apps.mediafiles.models import Photo

pytestmark = pytest.mark.django_db(transaction=True)
base = import_module('apps.listings.migrations.0015_publication_state')
previous = import_module('apps.listings.migrations.0020_publication_match_counterparts')
rejected = import_module('apps.listings.migrations.0021_private_draft_publication_dependencies')


def assert_restored():
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regprocedure('listings_publication_private_draft(uuid)'),to_regprocedure('listings_publication_lock(uuid[])')")
        assert cursor.fetchone() == (None, None)
        definitions = {'listings_publication_mark(uuid[])': previous.MARK}
        definitions.update({f'lpd_{table}()': base.trigger_sql(table, base.DEPENDENCIES[table])[0] for table in rejected.TRIGGERS})
        for name, source in definitions.items():
            cursor.execute('SELECT prosrc FROM pg_proc WHERE oid=%s::regprocedure', [name])
            assert cursor.fetchone()[0] == source.split('$$')[1]


def test_corrective_up_down_preserves_conservative_dirty(request, monkeypatch):
    request.getfixturevalue('directory')
    monkeypatch.setattr(refresh_publication_state, 'delay', lambda: None)
    assert_restored()
    owner = Listing.objects.filter(status='published').first()
    draft = Revision.objects.create(listing=owner, manager_version=owner.person.manager_version)
    photo = Photo.objects.create(revision=draft, blob=owner.approved_revision.photos.first().blob)
    publication_state.refresh_all()
    leaves = MigrationExecutor(connection).loader.graph.leaf_nodes()
    try:
        MigrationExecutor(connection).migrate([('listings', '0021_private_draft_publication_dependencies')])
        Revision.objects.filter(pk=draft.pk).update(edit_version=2)
        assert not PublicationDirty.objects.exists()
        MigrationExecutor(connection).migrate(leaves)
        assert_restored()
        Revision.objects.filter(pk=draft.pk).update(edit_version=3)
        assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()
        publication_state.refresh_all()
        Photo.objects.filter(pk=photo.pk).update(comparison_complete=True)
        assert PublicationDirty.objects.filter(listing_id=owner.pk).exists()
    finally:
        MigrationExecutor(connection).migrate(leaves)
        assert_restored()
