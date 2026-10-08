"""Cover conditional photo reintroduction dependencies on existing installations."""

from importlib import import_module

from django.db import migrations

base = import_module("apps.listings.migrations.0015_publication_state")

DEPENDENCIES = {
    "safety_rightsphotoreintroductiondecision": [
        "SELECT v.listing_id FROM {rows} r "
        "JOIN safety_rightsphotoreintroduction c ON c.id = r.candidate_id "
        "JOIN mediafiles_photo p ON p.id = c.photo_id "
        "JOIN listings_revision v ON v.id = p.revision_id"
    ],
    "safety_rightsproof": [
        "SELECT l.id FROM {rows} r "
        "JOIN safety_rightsrectificationexecution e ON e.proof_id = r.id "
        "JOIN safety_rightsrectificationnotification n ON n.id = e.notification_id "
        "JOIN safety_rightsrectificationreview rv ON rv.id = n.review_id "
        "JOIN safety_rightsrectificationproposal pr ON pr.id = rv.proposal_id "
        "JOIN listings_listing l ON l.person_id = pr.person_id"
    ],
}

# Previously trusted states may already have missed a write. Invalidate them before
# serving the new schema; refresh is optional for exactness, native fallback is not.
MARK_EXISTING = "SELECT listings_publication_mark(ARRAY(SELECT id FROM listings_listing));"


class Migration(migrations.Migration):
    dependencies = [("listings", "0016_drop_text_proof_indexes")]
    operations = [
        migrations.RunSQL(
            base.trigger_sql(table, mappings)[0],
            f"DROP TRIGGER IF EXISTS lpd_{table}_t ON {table}; "
            + base.trigger_sql(table, mappings)[1],
        )
        for table, mappings in DEPENDENCIES.items()
    ] + [migrations.RunSQL(MARK_EXISTING, MARK_EXISTING)]
