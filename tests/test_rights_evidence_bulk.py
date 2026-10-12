# ruff: noqa: F811 -- imported fixtures requested by pytest
"""Set readers must match unchanged producers on real PostgreSQL."""
import pytest
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from test_rights_evidence_chain import base, runtime, set_role  # noqa: F401

from apps.safety import evidence_chain as chain
from apps.safety.evidence_chain_bulk_sql_v1 import EVENT_FUNCTION, EVENT_QUERY, SOURCE_FUNCTIONS
from apps.safety.evidence_chain_sql_v1 import EVENT, TABLES

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('zone', ['UTC', 'Europe/Madrid', 'America/New_York', 'Asia/Kathmandu'])
@pytest.mark.parametrize('style', ['ISO, MDY', 'SQL, DMY', 'German, DMY'])
def test_bulk_all_families_events_and_tombstone_equal_producers(base, runtime, zone, style):
    case = base[0]
    chain.record_tombstone(case, 'expired_payload_purged')
    set_role(runtime)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute("SELECT set_config('TimeZone',%s,true),set_config('DateStyle',%s,true)",
                       [zone, style])
        for table, (statement, params) in zip(TABLES, chain._source_statements(case.pk), strict=True):
            cursor.execute(statement, params)
            actual = dict(cursor.fetchall())
            cursor.execute('SELECT s.id::text,public.rights_evidence_row_hash(to_jsonb(s)) '
                           f'FROM public."{table}" s JOIN public.safety_rightsaction a '
                           'ON a.id=s.action_id WHERE a.request_id=%s', [case.pk])
            assert actual and actual == dict(cursor.fetchall())
        # Text timestamps avoid psycopg's ISO-only datetime loader for this check.
        cursor.execute(f'SELECT sequence,expected FROM public.{EVENT_FUNCTION}(%s) ORDER BY sequence',
                       [case.pk])
        actual = cursor.fetchall()
        cursor.execute('SELECT sequence,public.rights_evidence_link(request_id,sequence,kind,'
                       'source_table,source_pk,payload_digest,previous_digest,created_at) '
                       f'FROM public."{EVENT}" WHERE request_id=%s ORDER BY sequence', [case.pk])
        assert len(actual) == 8 and actual == cursor.fetchall()
    assert chain.validate_chain(case).count == 8


@pytest.mark.parametrize('position', range(7))
def test_bulk_detects_owner_changes_and_missing_rows_with_same_head(base, position):
    case, _, _, _, rows = base
    ticket = chain.validate_chain(case)
    row = rows[position]
    type(row).objects.filter(pk=row.pk).update(source_digest='0' * 64)
    with pytest.raises(ValidationError, match='source rows'):
        chain.validate_chain(case, ticket=ticket)
    # Restore the stored producer value and then remove the physical row via SQL
    # (ORM cascades would exercise unrelated domain relationships).
    type(row).objects.filter(pk=row.pk).update(source_digest='d' * 64)
    assert chain.validate_chain(case) == ticket
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(f'DELETE FROM public."{TABLES[position]}" WHERE id=%s', [row.pk])
        with pytest.raises(ValidationError, match='source rows'):
            chain.validate_chain(case)
        transaction.set_rollback(True)
    assert chain.validate_chain(case) == ticket


def test_bulk_invoker_properties_and_foreign_case_exclusion(base, runtime):
    case = base[0]
    with connection.cursor() as cursor:
        cursor.execute('SELECT proname,provolatile,prosecdef,proconfig FROM pg_proc '
                       'WHERE pronamespace=\'public\'::regnamespace AND proname=ANY(%s)',
                       [list(SOURCE_FUNCTIONS) + [EVENT_FUNCTION]])
        properties = cursor.fetchall()
        assert len(properties) == 8
        assert all(row[1:] == ('s', False, ['search_path=pg_catalog, public']) for row in properties)
    set_role(runtime)
    from uuid import uuid4
    assert chain._source_rows(uuid4()) == {}
    with connection.cursor() as cursor:
        cursor.execute(EVENT_QUERY, [uuid4()])
        assert cursor.fetchall() == []
    assert chain.validate_chain(case).count == 7


def test_new_physical_column_is_not_omitted_from_fresh_hash(base):
    case = base[0]
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute(f'ALTER TABLE public."{TABLES[0]}" ADD COLUMN bulk_extra text DEFAULT \'ñ😀\'')
        with pytest.raises(ValidationError, match='source rows'):
            chain.validate_chain(case)
        transaction.set_rollback(True)
    assert chain.validate_chain(case).count == 7


def test_bulk_pinned_search_path_cannot_shadow_table_or_hash(base):
    case = base[0]
    expected = chain._source_rows(case.pk)
    with transaction.atomic(), connection.cursor() as cursor:
        cursor.execute('CREATE SCHEMA bulk_hostile')
        cursor.execute("CREATE FUNCTION bulk_hostile.sha256(bytea) RETURNS bytea "
                       "LANGUAGE sql AS $$ SELECT '\\x00'::bytea $$")
        cursor.execute(f'CREATE TABLE bulk_hostile."{TABLES[0]}" (id text)')
        cursor.execute('SET LOCAL search_path=bulk_hostile,pg_catalog,public')
        assert chain._source_rows(case.pk) == expected
        assert chain.validate_chain(case).count == 7
        transaction.set_rollback(True)


@pytest.mark.parametrize('timestamp', [
    '2026-03-29 00:59:59.999999+00', '2026-03-29 01:00:00.000001+00',
    '2026-10-25 00:59:59.123456+00', '2026-10-25 01:00:00.654321+00',
    '0001-01-01 00:00:00+00', '9999-12-31 23:59:59.999999+00', None,
])
def test_bulk_real_row_extreme_dates_and_additional_timestamp(base, timestamp):
    case, _, _, _, rows = base
    with transaction.atomic(), connection.cursor() as cursor:
        table = TABLES[0]
        cursor.execute(f'ALTER TABLE public."{table}" ALTER COLUMN created_at DROP NOT NULL')
        cursor.execute(f'ALTER TABLE public."{table}" ADD COLUMN bulk_observed_at timestamptz '
                       "DEFAULT '2026-10-25 01:00:00.123456+00'")
        cursor.execute(f'UPDATE public."{table}" SET created_at=%s,assessment_digest=%s WHERE id=%s',
                       [timestamp, 'ñ😀', rows[0].pk])
        for zone in ('UTC', 'Europe/Madrid', 'America/New_York', 'Asia/Kathmandu'):
            for style in ('ISO, MDY', 'SQL, DMY', 'German, DMY'):
                cursor.execute("SELECT set_config('TimeZone',%s,true),set_config('DateStyle',%s,true)",
                               [zone, style])
                cursor.execute(chain._source_statements(case.pk)[0][0], [case.pk])
                actual = cursor.fetchall()
                cursor.execute('SELECT s.id::text,public.rights_evidence_row_hash(to_jsonb(s)) '
                               f'FROM public."{table}" s WHERE id=%s', [rows[0].pk])
                assert actual == cursor.fetchall()
        transaction.set_rollback(True)


def test_bulk_migration_reverse_and_reinstall_preserve_chain(base):
    from apps.safety.evidence_chain_bulk_sql_v1 import install, uninstall
    ticket = chain.validate_chain(base[0])
    with transaction.atomic(), connection.cursor() as cursor:
        uninstall(cursor)
        install(cursor)
        assert chain.validate_chain(base[0]) == ticket
        transaction.set_rollback(True)
    assert chain.validate_chain(base[0]) == ticket


def test_current_and_historical_sql_diagnostic_queries_equal_producer(base):
    from tests.capacity_chain_explain import statements
    with connection.cursor() as cursor:
        for name, variants in statements(base[0].pk):
            results = {}
            for variant in ('native_hash', 'inline_hash', 'set_hash'):
                cursor.execute(variants[variant], [base[0].pk])
                rows = cursor.fetchall()
                results[variant] = rows if name == 'events' else dict(rows)
            assert results['native_hash'] == results['inline_hash'] == results['set_hash']
            for variant in ('whole_row', 'jsonb_payload'):
                cursor.execute(variants[variant], [base[0].pk])
                assert len(cursor.fetchall()) == len(results['native_hash'])
