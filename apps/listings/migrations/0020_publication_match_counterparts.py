"""Invalidate indirect conflict readers as well as the written listing.

Conflict eligibility reads both photos and both revisions' history. A write to
either side can restore or withdraw the other listing without a Match write.
Expand the existing dependency set by one match edge; no recursive propagation
is needed because another listing's eligibility is not itself a rule input.
"""

from importlib import import_module

from django.db import migrations

base = import_module("apps.listings.migrations.0015_publication_state")

MARK = """
CREATE OR REPLACE FUNCTION listings_publication_mark(ids uuid[]) RETURNS void AS $$
BEGIN
  INSERT INTO listings_publicationdirty (listing_id, generation, marked_at)
  SELECT id, nextval('listings_publication_generation'), clock_timestamp()
  FROM (
    WITH direct AS (SELECT DISTINCT unnest(ids) AS id),
    affected AS (
      SELECT id FROM direct
      UNION
      SELECT counterpart_revision.listing_id
      FROM direct d
      JOIN listings_revision r ON r.listing_id = d.id
      JOIN mediafiles_photo p ON p.revision_id = r.id
      JOIN mediafiles_match m ON m.photo_id = p.id
      JOIN mediafiles_photo counterpart ON counterpart.id = m.candidate_id
      JOIN listings_revision counterpart_revision ON counterpart_revision.id = counterpart.revision_id
      UNION
      SELECT counterpart_revision.listing_id
      FROM direct d
      JOIN listings_revision r ON r.listing_id = d.id
      JOIN mediafiles_photo p ON p.revision_id = r.id
      JOIN mediafiles_match m ON m.candidate_id = p.id
      JOIN mediafiles_photo counterpart ON counterpart.id = m.photo_id
      JOIN listings_revision counterpart_revision ON counterpart_revision.id = counterpart.revision_id
    )
    SELECT id FROM affected WHERE id IS NOT NULL ORDER BY id
  ) changed
  ON CONFLICT (listing_id) DO UPDATE SET generation = EXCLUDED.generation;
END $$ LANGUAGE plpgsql;
"""

MARK_EXISTING = "SELECT listings_publication_mark(ARRAY(SELECT id FROM listings_listing));"


class Migration(migrations.Migration):
    dependencies = [("listings", "0019_publicationstate_public_read_projection")]
    operations = [
        migrations.RunSQL(MARK, base.MARK),
        # Previously trusted negative states can already have missed a write.
        migrations.RunSQL(MARK_EXISTING, MARK_EXISTING),
    ]
