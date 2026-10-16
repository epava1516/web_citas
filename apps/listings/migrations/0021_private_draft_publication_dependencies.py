"""Skip independent draft invalidation while retaining domain writer serialization.

Only RC may skip. Other isolation modes and unknown dependencies stay dirty.
Ordered NO KEY UPDATE locks retain serialization without adding persistent data.
"""
from importlib import import_module

from django.db import migrations

base = import_module("apps.listings.migrations.0015_publication_state")
previous = import_module("apps.listings.migrations.0020_publication_match_counterparts")

PRIVATE = """
CREATE FUNCTION listings_publication_private_draft(revision_id uuid) RETURNS boolean
LANGUAGE sql VOLATILE AS $$
SELECT EXISTS (
 SELECT 1 FROM listings_revision v JOIN listings_listing l ON l.id=v.listing_id
 WHERE current_setting('transaction_isolation')='read committed' AND v.id=revision_id AND v.status='draft' AND l.approved_revision_id IS DISTINCT FROM v.id
 AND NOT EXISTS (
   SELECT 1 FROM mediafiles_match m JOIN mediafiles_photo p ON p.id=m.photo_id OR p.id=m.candidate_id
   JOIN listings_revision r ON r.id=p.revision_id WHERE r.listing_id=l.id)
 AND NOT EXISTS (SELECT 1 FROM safety_rightsrectificationproposal p WHERE p.person_id=l.person_id)
 AND NOT EXISTS (
   SELECT 1 FROM safety_rightsphotoreintroduction i JOIN mediafiles_photo p ON p.id=i.photo_id
   JOIN listings_revision r ON r.id=p.revision_id WHERE r.listing_id=l.id)
 AND NOT EXISTS (
   SELECT 1 FROM safety_rightsrectificationphotoupload u JOIN mediafiles_photo p ON p.id=u.photo_id
   JOIN listings_revision r ON r.id=p.revision_id WHERE r.listing_id=l.id)
 AND NOT EXISTS (
   SELECT 1 FROM safety_rightsrectificationphotodisposition d JOIN mediafiles_photo p ON p.id=d.source_photo_id
   JOIN listings_revision r ON r.id=p.revision_id WHERE r.listing_id=l.id)
);
$$;
"""

LOCK = """
CREATE FUNCTION listings_publication_lock(ids uuid[]) RETURNS void AS $$
BEGIN
 PERFORM l.id FROM listings_listing l WHERE l.id IN (
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
 SELECT id FROM affected WHERE id IS NOT NULL
 ) ORDER BY l.id FOR NO KEY UPDATE OF l;
END $$ LANGUAGE plpgsql VOLATILE;
"""

MARK = """
CREATE OR REPLACE FUNCTION listings_publication_mark(ids uuid[]) RETURNS void AS $$
BEGIN
  PERFORM listings_publication_lock(ids);
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

TRIGGERS = {
    'listings_revision': """
CREATE OR REPLACE FUNCTION lpd_listings_revision() RETURNS trigger AS $$
BEGIN

 IF TG_OP='INSERT' THEN
  PERFORM listings_publication_lock(ARRAY(SELECT r.listing_id FROM new_rows r));
 ELSIF TG_OP='UPDATE' THEN
  PERFORM listings_publication_lock(ARRAY(SELECT r.listing_id FROM new_rows r UNION SELECT r.listing_id FROM old_rows r));
 ELSE
  PERFORM listings_publication_lock(ARRAY(SELECT r.listing_id FROM old_rows r));
 END IF;
 IF TG_OP='UPDATE' THEN
  PERFORM listings_publication_mark(ARRAY(
   SELECT n.listing_id FROM new_rows n LEFT JOIN old_rows o ON o.id=n.id
   WHERE NOT listings_publication_private_draft(n.id)
      OR (to_jsonb(n)-ARRAY['edit_version','updated_at']) IS DISTINCT FROM (to_jsonb(o)-ARRAY['edit_version','updated_at'])
   UNION
   SELECT o.listing_id FROM old_rows o LEFT JOIN new_rows n ON n.id=o.id
   WHERE NOT listings_publication_private_draft(o.id)
      OR (to_jsonb(n)-ARRAY['edit_version','updated_at']) IS DISTINCT FROM (to_jsonb(o)-ARRAY['edit_version','updated_at'])
  ));
 ELSIF TG_OP='INSERT' THEN
  PERFORM listings_publication_mark(ARRAY(SELECT listing_id FROM new_rows));
 ELSE
  PERFORM listings_publication_mark(ARRAY(SELECT listing_id FROM old_rows));
 END IF;
 RETURN NULL;
END $$ LANGUAGE plpgsql VOLATILE;
""",
    'mediafiles_photo': """
CREATE OR REPLACE FUNCTION lpd_mediafiles_photo() RETURNS trigger AS $$
BEGIN

 IF TG_OP='INSERT' THEN
  PERFORM listings_publication_lock(ARRAY(SELECT v.listing_id FROM new_rows r JOIN listings_revision v ON v.id = r.revision_id));
 ELSIF TG_OP='UPDATE' THEN
  PERFORM listings_publication_lock(ARRAY(SELECT v.listing_id FROM new_rows r JOIN listings_revision v ON v.id = r.revision_id UNION SELECT v.listing_id FROM old_rows r JOIN listings_revision v ON v.id = r.revision_id));
 ELSE
  PERFORM listings_publication_lock(ARRAY(SELECT v.listing_id FROM old_rows r JOIN listings_revision v ON v.id = r.revision_id));
 END IF;
 IF TG_OP IN ('INSERT','UPDATE') THEN
  PERFORM listings_publication_mark(ARRAY(SELECT v.listing_id FROM new_rows r JOIN listings_revision v ON v.id = r.revision_id WHERE NOT listings_publication_private_draft(v.id)));
 END IF;
 IF TG_OP='UPDATE' THEN
  PERFORM listings_publication_mark(ARRAY(SELECT v.listing_id FROM old_rows r JOIN listings_revision v ON v.id = r.revision_id WHERE NOT listings_publication_private_draft(v.id)));
 ELSIF TG_OP='DELETE' THEN
  PERFORM listings_publication_mark(ARRAY(SELECT v.listing_id FROM old_rows r JOIN listings_revision v ON v.id = r.revision_id));
 END IF;
 RETURN NULL;
END $$ LANGUAGE plpgsql VOLATILE;
""",
    'mediafiles_blob': """
CREATE OR REPLACE FUNCTION lpd_mediafiles_blob() RETURNS trigger AS $$
BEGIN

 IF TG_OP='INSERT' THEN
  PERFORM listings_publication_lock(ARRAY(SELECT v.listing_id FROM new_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id));
 ELSIF TG_OP='UPDATE' THEN
  PERFORM listings_publication_lock(ARRAY(SELECT v.listing_id FROM new_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id UNION SELECT v.listing_id FROM old_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id));
 ELSE
  PERFORM listings_publication_lock(ARRAY(SELECT v.listing_id FROM old_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id));
 END IF;
 IF TG_OP IN ('INSERT','UPDATE') THEN
  PERFORM listings_publication_mark(ARRAY(SELECT v.listing_id FROM new_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id WHERE NOT listings_publication_private_draft(v.id) OR EXISTS (
          SELECT 1 FROM safety_rightsphotoreintroduction i
          LEFT JOIN safety_rightsrectificationphotodisposition d ON d.id=i.disposition_id
          WHERE i.uploaded_blob_id=r.id OR d.blob_id=r.id)
          OR EXISTS (SELECT 1 FROM safety_rightsrectificationphotodisposition d WHERE d.blob_id=r.id)));
 END IF;
 IF TG_OP='UPDATE' THEN
  PERFORM listings_publication_mark(ARRAY(SELECT v.listing_id FROM old_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id WHERE NOT listings_publication_private_draft(v.id) OR EXISTS (
          SELECT 1 FROM safety_rightsphotoreintroduction i
          LEFT JOIN safety_rightsrectificationphotodisposition d ON d.id=i.disposition_id
          WHERE i.uploaded_blob_id=r.id OR d.blob_id=r.id)
          OR EXISTS (SELECT 1 FROM safety_rightsrectificationphotodisposition d WHERE d.blob_id=r.id)));
 ELSIF TG_OP='DELETE' THEN
  PERFORM listings_publication_mark(ARRAY(SELECT v.listing_id FROM old_rows r JOIN mediafiles_photo p ON p.blob_id = r.id JOIN listings_revision v ON v.id = p.revision_id));
 END IF;
 RETURN NULL;
END $$ LANGUAGE plpgsql VOLATILE;
""",
}


FORWARD = [PRIVATE, LOCK, MARK, *TRIGGERS.values()]
REVERSE = [previous.MARK] + [
    base.trigger_sql(table, base.DEPENDENCIES[table])[0].split("CREATE TRIGGER", 1)[0]
    for table in TRIGGERS
] + [
    "DROP FUNCTION listings_publication_private_draft(uuid)",
    "DROP FUNCTION listings_publication_lock(uuid[])",
]


class Migration(migrations.Migration):
    dependencies = [("listings", "0020_publication_match_counterparts")]
    operations = [migrations.RunSQL(FORWARD, REVERSE)]
