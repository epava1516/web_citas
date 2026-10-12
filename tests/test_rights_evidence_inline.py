# ruff: noqa: F811
"""Read expressions must equal the unchanged producer functions on real PostgreSQL."""
import pytest
from django.db import connection, transaction
from test_rights_evidence_chain import base  # noqa: F401

from apps.safety import evidence_chain as chain
from apps.safety.evidence_chain_sql_v1 import EVENT, TABLES
from tests.capacity_chain_inline_candidate import (
    _EVENT_LINK_SQL,
    _SOURCE_HASH_SQL,
    candidate_functions,
    scope,
)

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('zone', ['UTC', 'Europe/Madrid', 'America/New_York', 'Asia/Kathmandu'])
@pytest.mark.parametrize('style', ['ISO, MDY', 'SQL, DMY', 'German, DMY'])
def test_all_families_and_tombstone_equal_producer(base, zone, style):
    case, _, _, _, rows = base
    chain.record_tombstone(case, 'expired_payload_purged')
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('TimeZone',%s,true),set_config('DateStyle',%s,true)", [zone, style])
        for table, (statement, params) in zip(TABLES, candidate_functions()[0](str(case.pk)), strict=True):
            cursor.execute(statement, params)
            actual = dict(cursor.fetchall())
            cursor.execute('SELECT s.id::text,public.rights_evidence_row_hash(to_jsonb(s)) '
                           f'FROM public."{table}" s JOIN public.safety_rightsaction a '
                           'ON a.id=s.action_id WHERE a.request_id=%s', [case.pk])
            expected = dict(cursor.fetchall())
            assert expected and actual == expected
        cursor.execute(f'SELECT {_EVENT_LINK_SQL},public.rights_evidence_link('
                       'request_id,sequence,kind,source_table,source_pk,payload_digest,previous_digest,created_at) '
                       f'FROM public."{EVENT}" WHERE request_id=%s', [case.pk])
        pairs = cursor.fetchall()
        assert len(pairs) == 8 and all(a == b for a, b in pairs)
    # The psycopg text timestamp loader requires ISO DateStyle; digest equality
    # above is entirely SQL and can be checked under the other session styles.
    with scope():
        assert chain.validate_chain(case).count == 8


@pytest.mark.parametrize('timestamp', [
    '2026-03-29 00:59:59.999999+00', '2026-03-29 01:00:00.000001+00',
    '2026-10-25 00:59:59.123456+00', '2026-10-25 01:00:00.654321+00',
    None, '2026-01-01 00:00:00.100000+00',
    '0001-01-01 00:00:00+00', '9999-12-31 23:59:59.999999+00',
])
def test_payload_unicode_json_and_dst(timestamp):
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SET LOCAL TimeZone='America/New_York'")
        cursor.execute(f'SELECT {_SOURCE_HASH_SQL},public.rights_evidence_row_hash(to_jsonb(s)) '
                       'FROM (SELECT %s::timestamptz AS created_at, %s::jsonb AS metadata, '
                       '9223372036854775807::bigint AS large, NULL::text AS optional) s',
                       [timestamp, '{"unicode":"ñ😀\\n\\\"","nested":[null,true,1.125,{"x":[]}]}'])
        actual, expected = cursor.fetchone()
        assert actual == expected


def test_caller_search_path_cannot_shadow_hash_builtins():
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute('CREATE SCHEMA inline_hostile')
        try:
            cursor.execute("CREATE FUNCTION inline_hostile.sha256(bytea) RETURNS bytea "
                           "LANGUAGE sql AS $$ SELECT '\\x00'::bytea $$")
            cursor.execute("SET LOCAL search_path=inline_hostile,pg_catalog,public")
            cursor.execute(f'SELECT {_SOURCE_HASH_SQL},public.rights_evidence_row_hash(pg_catalog.to_jsonb(s)) '
                           "FROM (SELECT '2026-10-25 01:00:00.100000+00'::timestamptz AS created_at) s")
            actual, expected = cursor.fetchone()
            assert actual == expected and len(actual) == 64
        finally:
            cursor.execute('DROP SCHEMA inline_hostile CASCADE')
