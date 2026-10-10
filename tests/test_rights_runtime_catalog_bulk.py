"""Fresh catalogue guards through real PostgreSQL LOGIN; no cached trust result."""

from uuid import uuid4

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from psycopg import sql
from test_rights_enforced_validation_seal import login

from apps.safety.evidence_chain import _runtime_is_trusted
from apps.safety.evidence_chain_sql_v1 import EVENT, HEAD, TABLES

pytestmark = pytest.mark.django_db(transaction=True)


def trusted():
    with connection.cursor() as cursor:
        return _runtime_is_trusted(cursor)


def test_actual_login_checks_nine_queries_each_time_without_cached_trust(settings):
    with login(settings):
        with CaptureQueriesContext(connection) as queries:
            assert trusted()
        assert len(queries) == 9
        with CaptureQueriesContext(connection) as queries:
            assert trusted()
            assert trusted()
        assert len(queries) == 18
        statements = [query["sql"] for query in queries]
        columns = next(index for index, query in enumerate(statements) if "pg_attribute" in query)
        owners = next(index for index, query in enumerate(statements) if "unnest(" in query)
        assert columns < owners


@pytest.mark.parametrize(
    "mutation",
    [
        "column",
        "update",
        "delete",
        "truncate",
        "head_insert",
        "event_insert",
        "append_execute",
        "replication",
        "inherited_owner",
    ],
)
def test_grant_between_actual_login_checks_is_rejected(settings, mutation):
    with login(settings) as (admin, role):
        assert trusted()
        with admin.cursor() as cursor:
            if mutation in {"column", "update", "delete", "truncate"}:
                privilege = "UPDATE(source_digest)" if mutation == "column" else mutation.upper()
                cursor.execute(
                    sql.SQL("GRANT " + privilege + " ON public.{} TO {}").format(
                        sql.Identifier(TABLES[0]), sql.Identifier(role)
                    )
                )
            elif mutation in {"head_insert", "event_insert"}:
                cursor.execute(
                    sql.SQL("GRANT INSERT ON public.{} TO {}").format(
                        sql.Identifier(HEAD if mutation == "head_insert" else EVENT),
                        sql.Identifier(role),
                    )
                )
            elif mutation == "append_execute":
                cursor.execute(
                    sql.SQL(
                        "GRANT EXECUTE ON FUNCTION "
                        "public.rights_evidence_append(uuid,text,text,text,text,timestamptz) TO {}"
                    ).format(sql.Identifier(role))
                )
            elif mutation == "replication":
                cursor.execute(
                    sql.SQL("GRANT SET ON PARAMETER session_replication_role TO {}").format(
                        sql.Identifier(role)
                    )
                )
            else:
                cursor.execute(
                    "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid=%s::regclass",
                    ["public." + TABLES[0]],
                )
                owner = cursor.fetchone()[0]
                cursor.execute(
                    sql.SQL("GRANT {} TO {}").format(sql.Identifier(owner), sql.Identifier(role))
                )
        assert trusted() is False


@pytest.mark.parametrize(
    "mutation", ["disabled", "replica", "missing", "wrong_definer", "wrong_namespace"]
)
def test_trigger_change_between_actual_login_checks_is_rejected(settings, mutation):
    with login(settings) as (admin, _):
        assert trusted()
        # Commit before the independent LOGIN's next observation. Uncommitted DDL
        # would test its old snapshot rather than a changed catalogue.
        namespace_name = "runtime_guard_" + uuid4().hex[:12]
        with admin.cursor() as cursor:
            table = sql.Identifier(TABLES[0])
            if mutation == "disabled":
                cursor.execute(
                    sql.SQL("ALTER TABLE public.{} DISABLE TRIGGER rights_evidence_record").format(
                        table
                    )
                )
            elif mutation == "replica":
                cursor.execute(
                    sql.SQL(
                        "ALTER TABLE public.{} ENABLE REPLICA TRIGGER rights_evidence_record"
                    ).format(table)
                )
            elif mutation == "missing":
                cursor.execute(
                    sql.SQL("DROP TRIGGER rights_evidence_record ON public.{}").format(table)
                )
            elif mutation == "wrong_definer":
                cursor.execute("ALTER FUNCTION public.rights_evidence_insert() SECURITY INVOKER")
            else:
                namespace = sql.Identifier(namespace_name)
                cursor.execute(sql.SQL("CREATE SCHEMA {}").format(namespace))
                cursor.execute(
                    sql.SQL("ALTER FUNCTION public.rights_evidence_insert() SET SCHEMA {}").format(
                        namespace
                    )
                )
        try:
            assert trusted() is False
        finally:
            with admin.cursor() as cursor:
                if mutation in {"disabled", "replica"}:
                    cursor.execute(
                        sql.SQL(
                            "ALTER TABLE public.{} ENABLE TRIGGER rights_evidence_record"
                        ).format(table)
                    )
                elif mutation == "missing":
                    cursor.execute(
                        sql.SQL(
                            "CREATE TRIGGER rights_evidence_record AFTER INSERT ON public.{} "
                            "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_insert()"
                        ).format(table)
                    )
                elif mutation == "wrong_definer":
                    cursor.execute(
                        "ALTER FUNCTION public.rights_evidence_insert() SECURITY DEFINER"
                    )
                else:
                    cursor.execute(
                        sql.SQL(
                            "ALTER FUNCTION {}.rights_evidence_insert() SET SCHEMA public"
                        ).format(sql.Identifier(namespace_name))
                    )
                    cursor.execute(sql.SQL("DROP SCHEMA {}").format(sql.Identifier(namespace_name)))
        assert trusted()


def test_extra_trigger_is_accepted_and_id_only_update_remains_allowed(settings):
    with login(settings) as (admin, role):
        with admin.cursor() as cursor:
            cursor.execute(
                sql.SQL("GRANT UPDATE(id) ON public.{} TO {}").format(
                    sql.Identifier(TABLES[0]), sql.Identifier(role)
                )
            )
            cursor.execute(
                sql.SQL(
                    "CREATE TRIGGER extra_runtime_guard BEFORE UPDATE ON public.{} "
                    "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_guard()"
                ).format(sql.Identifier(TABLES[0]))
            )
        try:
            assert trusted()
        finally:
            with admin.cursor() as cursor:
                cursor.execute(
                    sql.SQL("DROP TRIGGER extra_runtime_guard ON public.{}").format(
                        sql.Identifier(TABLES[0])
                    )
                )
        assert trusted()


def test_owner_membership_is_observed_after_column_phase_in_the_same_call(settings):
    with login(settings) as (admin, role):
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid=%s::regclass",
                ["public." + TABLES[0]],
            )
            owner = cursor.fetchone()[0]
        changed = []

        def grant_after_columns(execute, statement, params, many, context):
            result = execute(statement, params, many, context)
            if "pg_attribute" in statement and not changed:
                with admin.cursor() as cursor:
                    cursor.execute(
                        sql.SQL("GRANT {} TO {}").format(
                            sql.Identifier(owner), sql.Identifier(role)
                        )
                    )
                changed.append(True)
            return result

        try:
            with connection.execute_wrapper(grant_after_columns):
                assert trusted() is False
            assert changed == [True]
        finally:
            with admin.cursor() as cursor:
                cursor.execute(
                    sql.SQL("REVOKE {} FROM {}").format(sql.Identifier(owner), sql.Identifier(role))
                )
        assert trusted()


@pytest.mark.parametrize("mutation", ["direct_owner", "missing_table"])
def test_direct_owner_or_missing_table_is_not_trusted(settings, mutation):
    with login(settings) as (admin, role):
        table = sql.Identifier(TABLES[0])
        renamed = sql.Identifier("runtime_missing_" + uuid4().hex[:12])
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid=%s::regclass",
                ["public." + TABLES[0]],
            )
            owner = cursor.fetchone()[0]
            if mutation == "direct_owner":
                cursor.execute(
                    sql.SQL("ALTER TABLE public.{} OWNER TO {}").format(table, sql.Identifier(role))
                )
            else:
                cursor.execute(sql.SQL("ALTER TABLE public.{} RENAME TO {}").format(table, renamed))
        try:
            assert trusted() is False
        finally:
            with admin.cursor() as cursor:
                if mutation == "direct_owner":
                    cursor.execute(
                        sql.SQL("ALTER TABLE public.{} OWNER TO {}").format(
                            table, sql.Identifier(owner)
                        )
                    )
                else:
                    cursor.execute(
                        sql.SQL("ALTER TABLE public.{} RENAME TO {}").format(renamed, table)
                    )
