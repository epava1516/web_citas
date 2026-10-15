"""Real PostgreSQL upgrade of existing publication state, restoring the full schema."""

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty, PublicationState

pytestmark = pytest.mark.django_db(transaction=True)


def test_conditional_migration_invalidates_existing_state(request, record_property):
    request.getfixturevalue("directory")
    while publication_state.refresh(500):
        pass
    ids = set(Listing.objects.values_list("pk", flat=True))
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    previous = [("listings", "0016_drop_text_proof_indexes")]
    historical = executor.loader.project_state(previous).apps.get_model("listings", "PublicationState")
    fields = [field.attname for field in historical._meta.concrete_fields]
    # Preserve the fields that existed at this upgrade, not later projections
    # deliberately dropped/rebuilt by traversing subsequent migrations.
    states = list(PublicationState.objects.order_by("listing_id").values(*fields))
    assert ids and states and not PublicationDirty.objects.exists()
    added = {"safety_rightsproof", "safety_rightsphotoreintroductiondecision"}

    def triggers():
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT event_object_table FROM information_schema.triggers "
                           "WHERE trigger_name LIKE 'lpd_%%'")
            return {r[0] for r in cursor.fetchall()}

    try:
        executor.migrate(previous)
        assert not added & triggers()
        PublicationDirty.objects.all().delete()
        assert list(historical.objects.order_by("listing_id").values(*fields)) == states
        MigrationExecutor(connection).migrate(latest)
        assert added <= triggers()
        assert set(PublicationDirty.objects.values_list("listing_id", flat=True)) == ids
        assert list(PublicationState.objects.order_by("listing_id").values(*fields)) == states
        record_property("upgrade", {"existing_listings_invalidated": len(ids),
                                     "stored_states_preserved": len(states),
                                     "preserved_fields": fields,
                                     "conditional_triggers_restored": True})
    finally:
        MigrationExecutor(connection).migrate(latest)
    while publication_state.refresh(500):
        pass
    assert not PublicationDirty.objects.exists()
