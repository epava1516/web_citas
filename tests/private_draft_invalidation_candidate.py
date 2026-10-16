"""Owned-PG prototype only. No application migration or automatic installation."""
from contextlib import contextmanager
from importlib import import_module

from django.db import connection

base = import_module('apps.listings.migrations.0015_publication_state')
TABLES = ('listings_revision', 'mediafiles_photo', 'mediafiles_blob')
SAFE = """
CREATE FUNCTION cr09_private_draft_revision(revision_id uuid) RETURNS boolean
LANGUAGE sql VOLATILE AS $$
SELECT EXISTS (
 SELECT 1 FROM listings_revision v JOIN listings_listing l ON l.id=v.listing_id
 WHERE v.id=revision_id AND v.status='draft' AND l.approved_revision_id IS DISTINCT FROM v.id
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


def body(table):
    if table == 'listings_revision':
        return """
CREATE OR REPLACE FUNCTION lpd_listings_revision() RETURNS trigger AS $$
BEGIN
 IF TG_OP='UPDATE' THEN
  PERFORM listings_publication_mark(ARRAY(
   SELECT n.listing_id FROM new_rows n LEFT JOIN old_rows o ON o.id=n.id
   WHERE NOT cr09_private_draft_revision(n.id)
      OR (to_jsonb(n)-ARRAY['edit_version','updated_at']) IS DISTINCT FROM (to_jsonb(o)-ARRAY['edit_version','updated_at'])
   UNION
   SELECT o.listing_id FROM old_rows o LEFT JOIN new_rows n ON n.id=o.id
   WHERE NOT cr09_private_draft_revision(o.id)
      OR (to_jsonb(n)-ARRAY['edit_version','updated_at']) IS DISTINCT FROM (to_jsonb(o)-ARRAY['edit_version','updated_at'])
  ));
 ELSIF TG_OP='INSERT' THEN
  PERFORM listings_publication_mark(ARRAY(SELECT listing_id FROM new_rows));
 ELSE
  PERFORM listings_publication_mark(ARRAY(SELECT listing_id FROM old_rows));
 END IF;
 RETURN NULL;
END $$ LANGUAGE plpgsql VOLATILE;
"""
    mapping = base.DEPENDENCIES[table][0]
    predicate = 'NOT cr09_private_draft_revision(v.id)'
    if table == 'mediafiles_blob':
        predicate += """ OR EXISTS (
          SELECT 1 FROM safety_rightsphotoreintroduction i
          LEFT JOIN safety_rightsrectificationphotodisposition d ON d.id=i.disposition_id
          WHERE i.uploaded_blob_id=r.id OR d.blob_id=r.id)
          OR EXISTS (SELECT 1 FROM safety_rightsrectificationphotodisposition d WHERE d.blob_id=r.id)"""
    def collect(rows, filtered):
        return mapping.format(rows=rows) + (' WHERE ' + predicate if filtered else '')
    return f"""
CREATE OR REPLACE FUNCTION lpd_{table}() RETURNS trigger AS $$
BEGIN
 IF TG_OP IN ('INSERT','UPDATE') THEN
  PERFORM listings_publication_mark(ARRAY({collect('new_rows', True)}));
 END IF;
 IF TG_OP='UPDATE' THEN
  PERFORM listings_publication_mark(ARRAY({collect('old_rows', True)}));
 ELSIF TG_OP='DELETE' THEN
  PERFORM listings_publication_mark(ARRAY({collect('old_rows', False)}));
 END IF;
 RETURN NULL;
END $$ LANGUAGE plpgsql VOLATILE;
"""


@contextmanager
def installed():
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    originals = {}
    with connection.cursor() as cursor:
        for table in TABLES:
            cursor.execute("SELECT pg_get_functiondef(%s::regprocedure)", [f'lpd_{table}()'])
            originals[table] = cursor.fetchone()[0]
        cursor.execute(SAFE)
    try:
        with connection.cursor() as cursor:
            for table in TABLES:
                cursor.execute(body(table))
        yield
    finally:
        with connection.cursor() as cursor:
            for source in originals.values():
                cursor.execute(source)
            for table, source in originals.items():
                cursor.execute("SELECT pg_get_functiondef(%s::regprocedure)", [f'lpd_{table}()'])
                assert cursor.fetchone()[0] == source
            cursor.execute('DROP FUNCTION cr09_private_draft_revision(uuid)')
            cursor.execute("SELECT to_regprocedure('cr09_private_draft_revision(uuid)')")
            assert cursor.fetchone()[0] is None


def lock_body():
    mark = import_module('apps.listings.migrations.0020_publication_match_counterparts').MARK
    start = '    WITH direct AS'
    stop = '    SELECT id FROM affected WHERE id IS NOT NULL ORDER BY id'
    assert mark.count(start) == mark.count(stop) == 1
    cte = 'WITH direct AS' + mark.split(start, 1)[1].split(stop, 1)[0]
    return f"""
CREATE FUNCTION cr09_lock_publication(ids uuid[]) RETURNS void AS $$
BEGIN
 PERFORM l.id FROM listings_listing l WHERE l.id IN (
  {cte} SELECT id FROM affected WHERE id IS NOT NULL
 ) ORDER BY l.id FOR NO KEY UPDATE OF l;
END $$ LANGUAGE plpgsql VOLATILE;
"""


def fenced_body(table):
    def mapped(rows):
        return ' UNION '.join(sql.format(rows=rows) for sql in base.DEPENDENCIES[table])
    fence = f"""
 IF TG_OP='INSERT' THEN
  PERFORM cr09_lock_publication(ARRAY({mapped('new_rows')}));
 ELSIF TG_OP='UPDATE' THEN
  PERFORM cr09_lock_publication(ARRAY({mapped('new_rows')} UNION {mapped('old_rows')}));
 ELSE
  PERFORM cr09_lock_publication(ARRAY({mapped('old_rows')}));
 END IF;
"""
    return body(table).replace('BEGIN\n', 'BEGIN\n' + fence, 1)


@contextmanager
def fenced_installed():
    """Retain ordered domain write locks even when no dirty result is needed."""
    with installed():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_get_functiondef('listings_publication_mark(uuid[])'::regprocedure)")
            original_mark = cursor.fetchone()[0]
        try:
            mark = import_module('apps.listings.migrations.0020_publication_match_counterparts').MARK
            with connection.cursor() as cursor:
                cursor.execute(lock_body())
                cursor.execute(SAFE.replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1).replace(
                    'WHERE v.id=revision_id', "WHERE current_setting('transaction_isolation')='read committed' AND v.id=revision_id"))
                cursor.execute(mark.replace('BEGIN\n', 'BEGIN\n  PERFORM cr09_lock_publication(ids);\n', 1))
                for table in TABLES:
                    cursor.execute(fenced_body(table))
            yield
        finally:
            with connection.cursor() as cursor:
                cursor.execute(original_mark)
                for table in TABLES:
                    cursor.execute(body(table))
                cursor.execute("SELECT pg_get_functiondef('listings_publication_mark(uuid[])'::regprocedure)")
                assert cursor.fetchone()[0] == original_mark
                cursor.execute('DROP FUNCTION IF EXISTS cr09_lock_publication(uuid[])')


@contextmanager
def baseline_installed():
    """Explicit old0020 control under a newer migrated schema; restore exactly."""
    originals = {}
    assert connection.settings_dict['NAME'].startswith('test_promotion_gate_')
    with connection.cursor() as cursor:
        for name in ['listings_publication_mark(uuid[])', *[f'lpd_{t}()' for t in TABLES]]:
            cursor.execute('SELECT pg_get_functiondef(%s::regprocedure)', [name])
            originals[name] = cursor.fetchone()[0]
    try:
        with connection.cursor() as cursor:
            cursor.execute(import_module('apps.listings.migrations.0020_publication_match_counterparts').MARK)
            for table in TABLES:
                cursor.execute(base.trigger_sql(table, base.DEPENDENCIES[table])[0].split('CREATE TRIGGER', 1)[0])
        yield
    finally:
        with connection.cursor() as cursor:
            for source in originals.values():
                cursor.execute(source)
            for name, source in originals.items():
                cursor.execute('SELECT pg_get_functiondef(%s::regprocedure)', [name])
                assert cursor.fetchone()[0] == source
