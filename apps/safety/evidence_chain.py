"""Scoped immutable evidence chain. Existing domain/authority guards remain required."""

from dataclasses import dataclass
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from psycopg import sql

from .evidence_chain_sql_v1 import EVENT, HEAD, TABLES, ZERO, backfill


@dataclass(frozen=True)
class ChainTicket:
    request: str
    count: int
    digest: str
    schema: str = "rights-evidence-chain-v1"


def configure_role(role):
    """Migrator operation; runtime must not own or inherit owner/admin privileges."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=%s",
            [role],
        )
        flags = cursor.fetchone()
        if flags is None or any(flags):
            raise ValidationError(
                "Evidence runtime role must exist without administrative privileges"
            )
        cursor.execute(
            "SELECT DISTINCT pg_get_userbyid(relowner) FROM pg_class WHERE relname = ANY(%s)",
            [list(TABLES) + [HEAD, EVENT, "safety_rightsaction"]],
        )
        for (owner,) in cursor.fetchall():
            cursor.execute("SELECT pg_has_role(%s,%s,'MEMBER')", [role, owner])
            if cursor.fetchone()[0]:
                raise ValidationError(
                    "Evidence runtime role cannot own or inherit the migrator role"
                )
        cursor.execute(
            "SELECT has_parameter_privilege(%s,'session_replication_role','SET')", [role]
        )
        if cursor.fetchone()[0]:
            raise ValidationError("Evidence runtime role cannot disable replication triggers")
        identifier = sql.Identifier(role)
        for table in TABLES:
            cursor.execute(
                sql.SQL("GRANT SELECT, INSERT ON public.{} TO {}").format(
                    sql.Identifier(table), identifier
                )
            )
            cursor.execute(
                sql.SQL("REVOKE UPDATE, DELETE, TRUNCATE ON public.{} FROM {}").format(
                    sql.Identifier(table), identifier
                )
            )
            cursor.execute(
                "SELECT attname FROM pg_attribute WHERE attrelid=%s::regclass "
                "AND attnum>0 AND NOT attisdropped",
                ["public." + table],
            )
            columns = sql.SQL(",").join(sql.Identifier(name) for (name,) in cursor.fetchall())
            cursor.execute(
                sql.SQL("REVOKE UPDATE ({}) ON public.{} FROM {}").format(
                    columns, sql.Identifier(table), identifier
                )
            )
            # PostgreSQL row locks require UPDATE on at least one column.
            # The immutable trigger rejects DML even on this lock-only grant.
            cursor.execute(
                sql.SQL("GRANT UPDATE(id) ON public.{} TO {}").format(
                    sql.Identifier(table), identifier
                )
            )
            cursor.execute("SELECT pg_get_serial_sequence(%s,'id')", [table])
            sequence = cursor.fetchone()[0]
            if sequence:
                cursor.execute(
                    sql.SQL("GRANT USAGE, SELECT ON SEQUENCE {} TO {}").format(
                        sql.Identifier(*sequence.split(".")), identifier
                    )
                )
        cursor.execute(
            sql.SQL(
                "REVOKE ALL ON FUNCTION public.rights_evidence_append(uuid,text,text,text,text,timestamptz) FROM {}"
            ).format(identifier)
        )
        for table in (HEAD, EVENT):
            cursor.execute(
                sql.SQL("GRANT SELECT ON public.{} TO {}").format(sql.Identifier(table), identifier)
            )
            cursor.execute(
                sql.SQL("REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON public.{} FROM {}").format(
                    sql.Identifier(table), identifier
                )
            )
        cursor.execute(
            sql.SQL(
                "GRANT EXECUTE ON FUNCTION public.rights_evidence_tombstone(uuid,uuid,text) TO {}"
            ).format(identifier)
        )

        cursor.execute(
            sql.SQL(
                "GRANT EXECUTE ON FUNCTION public.rights_evidence_locked_head(uuid) TO {}"
            ).format(identifier)
        )


def _runtime_is_trusted(cursor):
    # Ownership is administrative power, even if privileges have been REVOKEd.
    cursor.execute(
        "SELECT rolsuper,rolcreatedb,rolcreaterole,rolbypassrls FROM pg_roles WHERE rolname=current_user"
    )
    if any(cursor.fetchone()):
        return False
    cursor.execute(
        "SELECT has_parameter_privilege(current_user,'session_replication_role','SET'), "
        "has_function_privilege(current_user,'public.rights_evidence_append(uuid,text,text,text,text,timestamptz)','EXECUTE')"
    )
    if any(cursor.fetchone()):
        return False
    names = list(TABLES) + [HEAD, EVENT]
    cursor.execute(
        "SELECT relname, pg_get_userbyid(relowner), "
        "has_table_privilege(current_user,oid,'UPDATE'), "
        "has_table_privilege(current_user,oid,'DELETE'), "
        "has_table_privilege(current_user,oid,'TRUNCATE') "
        "FROM pg_class WHERE relnamespace='public'::regnamespace AND relname=ANY(%s)",
        [names],
    )
    tables = cursor.fetchall()
    if len(tables) != len(names) or any(any(row[2:]) for row in tables):
        return False
    cursor.execute(
        "SELECT c.relname,a.attname FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid "
        "WHERE c.relnamespace='public'::regnamespace AND c.relname=ANY(%s) "
        "AND a.attnum>0 AND NOT a.attisdropped "
        "AND has_column_privilege(current_user,c.oid,a.attnum,'UPDATE')",
        [names],
    )
    if any(table not in TABLES or column != "id" for table, column in cursor.fetchall()):
        return False
    # Observe memberships freshly after the column-grant phase, as before.
    owners = [owner for _, owner, *_ in tables]
    cursor.execute(
        "SELECT pg_has_role(current_user,owner::name,'MEMBER') "
        "FROM unnest(%s::text[]) AS owners(owner)",
        [owners],
    )
    memberships = cursor.fetchall()
    if len(memberships) != len(owners) or any(member for (member,) in memberships):
        return False
    cursor.execute(
        "SELECT pg_has_role(current_user,pg_get_userbyid(relowner),'MEMBER') "
        "FROM pg_class WHERE oid='public.safety_rightsaction'::regclass"
    )
    if cursor.fetchone()[0]:
        return False
    cursor.execute(
        "SELECT p.proname,t.tgenabled,p.prosecdef,p.pronamespace='public'::regnamespace "
        "FROM pg_trigger t JOIN pg_proc p ON p.oid=t.tgfoid "
        "WHERE t.tgrelid='public.safety_rightsaction'::regclass AND t.tgname='rights_evidence_action_scope'"
    )
    if cursor.fetchone() != ("rights_evidence_action_scope_guard", "O", False, True):
        return False
    # Check actual functions/trigger attachment, not merely a table/trigger name.
    cursor.execute(
        "SELECT c.relname,t.tgname,p.proname,t.tgenabled,p.prosecdef,"
        "p.pronamespace='public'::regnamespace "
        "FROM pg_trigger t JOIN pg_proc p ON p.oid=t.tgfoid "
        "JOIN pg_class c ON c.oid=t.tgrelid "
        "WHERE c.relnamespace='public'::regnamespace AND c.relname=ANY(%s) "
        "AND NOT t.tgisinternal",
        [names],
    )
    by_table = {table: {} for table in names}
    for table, name, function, enabled, definer, public in cursor.fetchall():
        if public:
            by_table[table][name] = (function, enabled, definer)
    for table in names:
        triggers = by_table[table]
        for name in ("rights_evidence_no_modify", "rights_evidence_no_truncate"):
            if triggers.get(name) != ("rights_evidence_guard", "O", False):
                return False
        expected = (
            ("rights_evidence_record", "rights_evidence_insert", True)
            if table in TABLES
            else ("rights_evidence_no_direct_insert", "rights_evidence_guard", False)
        )
        if triggers.get(expected[0]) != (expected[1], "O", expected[2]):
            return False
    cursor.execute(
        "SELECT has_table_privilege(current_user,%s,'INSERT'), "
        "has_table_privilege(current_user,%s,'INSERT')",
        ["public." + HEAD, "public." + EVENT],
    )
    if any(cursor.fetchone()):
        return False
    return True


@transaction.atomic
def validate_chain(request, ticket=None, count=None):
    """Return a head ticket only after complete validation or matching trusted ticket.

    This checks stored immutable metadata, NOT mutable origins/proofs/authority/time.
    A ticket never authorizes an operation by itself.
    """
    request = str(getattr(request, "pk", request))
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT sequence,digest FROM public.rights_evidence_locked_head(%s)", [request]
        )
        head = cursor.fetchone()
        if head is None:
            raise ValidationError("Evidence chain is unavailable")
        current = ChainTicket(request, head[0], head[1])
        if ticket is not None and (not isinstance(ticket, ChainTicket) or ticket != current):
            raise ValidationError("Evidence chain ticket changed")
        if count is not None and (type(count) is not int or count != current.count):
            raise ValidationError("Evidence chain count changed")
        if ticket is not None and _runtime_is_trusted(cursor):
            return current
        cursor.execute(
            f'''SELECT sequence,kind,source_table,source_pk,payload_digest,
            previous_digest,digest,created_at,
            public.rights_evidence_link(request_id,sequence,kind,source_table,source_pk,
                                      payload_digest,previous_digest,created_at)
            FROM public."{EVENT}" WHERE request_id=%s ORDER BY sequence''',
            [request],
        )
        events = cursor.fetchall()
        previous = ZERO
        rows = {}
        for position, event in enumerate(events, 1):
            seq, kind, table, pk, payload, prev, digest, created, expected = event
            if seq != position or prev != previous or digest != expected:
                raise ValidationError("Evidence chain link changed")
            if kind == "row":
                if table not in TABLES:
                    raise ValidationError("Evidence chain source unavailable")
                rows[table, pk] = payload
            elif kind != "tombstone" or table != "rights_payload_purge":
                raise ValidationError("Evidence chain event kind changed")
            previous = digest
        if len(events) != current.count or previous != current.digest:
            raise ValidationError("Evidence chain head changed")
        actual = {}
        for table in TABLES:
            # Only these internal, whitelisted identifiers become SQL text. Keep
            # the request bound separately; arbitrary driver Composed statements
            # still decline validation seals at the recorder boundary.
            quoted_table = connection.ops.quote_name(table)
            cursor.execute(
                "SELECT s.id::text,public.rights_evidence_row_hash(to_jsonb(s)) "
                f"FROM public.{quoted_table} s JOIN public.safety_rightsaction a ON a.id=s.action_id "
                "WHERE a.request_id=%s",
                [request],
            )
            actual.update({(table, pk): digest for pk, digest in cursor.fetchall()})
        if actual != rows:
            raise ValidationError("Evidence chain source rows changed")
        return current


@transaction.atomic
def record_tombstone(request, reason, key=None):
    """Append a minimized audit marker; callers still perform and authorize actual purge."""
    request = str(getattr(request, "pk", request))
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT public.rights_evidence_tombstone(%s,%s,%s)", [request, key or uuid4(), reason]
        )
    return validate_chain(request)


@transaction.atomic
def backfill_missing():
    """Migrator recovery only; cannot rewrite existing evidence hashes."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT pg_get_userbyid(relowner)=current_user FROM pg_class WHERE oid=%s::regclass",
            ["public." + EVENT],
        )
        if not cursor.fetchone()[0]:
            raise ValidationError("Evidence backfill requires the table owner")
        backfill(cursor)


def require_runtime_chain(request):
    """Opt-in enforcement; keeps every existing domain guard in its caller."""
    from django.conf import settings

    if not getattr(settings, "RIGHTS_EVIDENCE_ENFORCED", False):
        return None
    with connection.cursor() as cursor:
        if not _runtime_is_trusted(cursor):
            raise ValidationError("Evidence enforcement requires a separate trusted runtime role")
    return validate_chain(request)
