"""Historical migration writes must not dispatch current-schema worker tasks."""

import importlib
from types import SimpleNamespace

import pytest
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Category
from apps.listings import tasks
from apps.listings.models import Listing, PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def test_catalogue_migration_preserves_data_without_scheduling_live_worker(monkeypatch):
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))
    Category.objects.filter(slug="romantic-dating").delete()
    queued.clear()  # Ignore the deliberately observed live-model setup deletion.
    historical_apps = MigrationExecutor(connection).loader.project_state().apps
    migration = importlib.import_module("apps.listings.migrations.0023_romantic_profile_contract")
    with transaction.atomic():
        migration.catalogue(historical_apps, SimpleNamespace(connection=connection))
        assert Category.objects.filter(slug="romantic-dating", active=True).exists()
        assert queued == []
    assert queued == []


def test_live_catalogue_write_still_schedules_after_commit(monkeypatch):
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))
    with transaction.atomic():
        Category.objects.create(slug="live-signal-control", name_es="Control", name_en="Control", version=1)
        assert queued == []
    assert queued == [1]


def test_live_many_to_many_through_still_schedules_after_commit(request, monkeypatch):
    request.getfixturevalue("directory")
    row = Listing.objects.filter(status="published").select_related("approved_revision").first()
    assert row is not None
    relation = row.approved_revision.categories
    category = relation.get(slug="romantic-dating")
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))
    with transaction.atomic():
        relation.remove(category)
        assert not relation.filter(pk=category.pk).exists()
        relation.add(category)
        assert relation.filter(pk=category.pk).exists()
        assert queued == []
    assert queued == [1]


def test_historical_catalogue_write_keeps_database_invalidation_and_native_rejection(
    request, monkeypatch,
):
    # Use the normal application fixture; do not manufacture eligibility.
    from apps.listings import publication_state
    from apps.listings.moderation import publicly_visible

    client = request.getfixturevalue("directory")
    publication_state.refresh_all()
    row = Listing.objects.filter(
        status="published", approved_revision__categories__slug="romantic-dating",
    ).first()
    assert row is not None and publicly_visible(row)
    assert not PublicationDirty.objects.exists()
    queued = []
    monkeypatch.setattr(tasks.refresh_publication_state, "delay", lambda: queued.append(1))
    historical = MigrationExecutor(connection).loader.project_state().apps.get_model("catalog", "Category")
    category = historical.objects.get(slug="romantic-dating")
    category.active = False
    category.save(update_fields=["active"])
    assert queued == []
    assert PublicationDirty.objects.filter(listing_id=row.pk).exists()
    assert not publicly_visible(Listing.objects.get(pk=row.pk))
    assert client.get(f"/es/listing/{row.pk}/").status_code == 404
