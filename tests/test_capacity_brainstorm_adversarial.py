"""Real PostgreSQL counterexamples for architectural hypotheses, not product gates."""
import json

import pytest
from django.db import connection
from psycopg import sql

pytestmark = pytest.mark.django_db(transaction=True)


HASH_FUNCTION = """CREATE OR REPLACE FUNCTION pg_temp.brainstorm_row_hash(body text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(body,'UTF8')),'hex')
$$"""


def test_restored_hash_function_does_not_repair_stored_generated_digest(record_property):
    assert connection.vendor == "postgresql" and connection.get_autocommit()
    with connection.cursor() as cursor:
        cursor.execute(HASH_FUNCTION)
        try:
            cursor.execute("CREATE TEMP TABLE brainstorm_generated (id integer PRIMARY KEY, payload text, "
                           "stored_digest text GENERATED ALWAYS AS (pg_temp.brainstorm_row_hash(payload)) STORED)")
            cursor.execute("CREATE TEMP TABLE brainstorm_head (sequence bigint, digest text)")
            cursor.execute("INSERT INTO brainstorm_generated(id,payload) VALUES(1,'alpha-synthetic')")
            cursor.execute("SELECT stored_digest FROM brainstorm_generated")
            original = cursor.fetchone()[0]
            cursor.execute("INSERT INTO brainstorm_head VALUES(1,%s)", [original])
            cursor.execute("SELECT pg_get_functiondef('pg_temp.brainstorm_row_hash(text)'::regprocedure)")
            definition = cursor.fetchone()[0]
            cursor.execute(sql.SQL("CREATE OR REPLACE FUNCTION pg_temp.brainstorm_row_hash(body text) "
                                   "RETURNS text LANGUAGE sql IMMUTABLE AS {}")
                           .format(sql.Literal("SELECT '" + original + "'::text")))
            cursor.execute("UPDATE brainstorm_generated SET payload='beta-synthetic' WHERE id=1")
            cursor.execute(HASH_FUNCTION)
            cursor.execute("SELECT pg_get_functiondef('pg_temp.brainstorm_row_hash(text)'::regprocedure)")
            assert cursor.fetchone()[0] == definition
            cursor.execute("SELECT stored_digest, pg_temp.brainstorm_row_hash(payload) FROM brainstorm_generated")
            stored, physical = cursor.fetchone()
            assert stored == original and physical != stored
            cursor.execute("SELECT sequence,digest FROM brainstorm_head")
            assert cursor.fetchone() == (1, original)
            record_property("generated_digest_counterexample", json.dumps({
                "current_function_definition_restored": True,
                "head_unchanged": True, "stored_digest_unchanged": True,
                "fresh_physical_digest_disagrees": True,
                "scope": "temporary_owner_DDL_model_not_product_optimization_or_acceptance"}))
        finally:
            cursor.execute("DROP TABLE IF EXISTS pg_temp.brainstorm_generated, pg_temp.brainstorm_head")
            cursor.execute("DROP FUNCTION pg_temp.brainstorm_row_hash(text)")


def test_freeze_and_reindex_preserve_observed_heap_versions_but_schema_can_change(record_property):
    assert connection.vendor == "postgresql" and connection.get_autocommit()
    with connection.cursor() as cursor:
        try:
            cursor.execute("CREATE TEMP TABLE brainstorm_versions (id integer PRIMARY KEY, payload text)")
            cursor.execute("INSERT INTO brainstorm_versions SELECT n,'synthetic-'||n::text FROM generate_series(1,1000) n")
            def read():
                cursor.execute("SELECT id,xmin::text,ctid::text FROM brainstorm_versions ORDER BY id")
                return cursor.fetchall()
            before = read()
            cursor.execute("VACUUM (FREEZE) pg_temp.brainstorm_versions")
            frozen = read()
            assert frozen == before
            cursor.execute("REINDEX TABLE pg_temp.brainstorm_versions")
            reindexed = read()
            assert reindexed == before
            cursor.execute("SELECT to_jsonb(t) FROM brainstorm_versions t WHERE id=1")
            payload_before = json.loads(cursor.fetchone()[0])
            cursor.execute("ALTER TABLE pg_temp.brainstorm_versions ADD COLUMN added text DEFAULT 'new-synthetic-default'")
            assert read() == before
            cursor.execute("SELECT to_jsonb(t) FROM brainstorm_versions t WHERE id=1")
            payload_after = json.loads(cursor.fetchone()[0])
            assert payload_after != payload_before
            assert payload_after["added"] == "new-synthetic-default"
            record_property("heap_version_counterexamples", json.dumps({
                "rows": len(before), "freeze_kept_observed_versions": True,
                "reindex_kept_observed_versions": True,
                "fast_default_kept_observed_versions": True,
                "generic_full_row_json_changed_after_schema_change": True,
                "limits": "not XID wrap test; not a claim static source_copy reads newly added columns; schema/code binding still required"}))
        finally:
            cursor.execute("DROP TABLE IF EXISTS pg_temp.brainstorm_versions")
