"""Versioned read-only set helpers; producer DDL and hash representation stay v1."""

from .evidence_chain_sql_v1 import EVENT, TABLES

SOURCE_FUNCTIONS = tuple(f"rights_evidence_source_{index}_v1" for index in range(len(TABLES)))
EVENT_FUNCTION = "rights_evidence_events_v1"
UTC_FORMAT = 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
SOURCE_HASH = (
    "pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
    "pg_catalog.jsonb_set(pg_catalog.to_jsonb(s),'{created_at}',"
    "pg_catalog.to_jsonb(pg_catalog.to_char(s.created_at AT TIME ZONE 'UTC',"
    f"'{UTC_FORMAT}')))::text,'UTF8')),'hex')"
)
EVENT_HASH = (
    "pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
    "pg_catalog.jsonb_build_array('rights-evidence-chain-v1',e.request_id::text,"
    "e.sequence,e.kind,e.source_table,e.source_pk,e.payload_digest,e.previous_digest,"
    f"pg_catalog.to_char(e.created_at AT TIME ZONE 'UTC','{UTC_FORMAT}'))"
    "::text,'UTF8')),'hex')"
)
EVENT_QUERY = (
    "SELECT sequence,kind,source_table,source_pk,payload_digest,"
    "previous_digest,digest,created_at,expected "
    f"FROM public.{EVENT_FUNCTION}(%s) ORDER BY sequence"
)


def install(cursor):
    # No function-wide TimeZone: to_jsonb(s) must retain caller formatting of
    # other timestamp columns. Only created_at is normalized, as by the producer.
    for table, function in zip(TABLES, SOURCE_FUNCTIONS, strict=True):
        cursor.execute(f'''CREATE FUNCTION public.{function}(case_id uuid)
RETURNS TABLE(row_id text,row_digest text)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
 SELECT s.id::text,{SOURCE_HASH} FROM public."{table}" s
 JOIN public.safety_rightsaction a ON a.id=s.action_id
 WHERE a.request_id=$1
$$''')
    cursor.execute(f'''CREATE FUNCTION public.{EVENT_FUNCTION}(case_id uuid)
RETURNS TABLE(sequence bigint,kind text,source_table text,source_pk text,
 payload_digest text,previous_digest text,digest text,created_at timestamptz,expected text)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog,public AS $$
 SELECT e.sequence,e.kind::text,e.source_table::text,e.source_pk::text,
 e.payload_digest::text,e.previous_digest::text,e.digest::text,e.created_at,{EVENT_HASH}
 FROM public."{EVENT}" e WHERE e.request_id=$1 ORDER BY e.sequence
$$''')


def uninstall(cursor):
    for function in (*SOURCE_FUNCTIONS, EVENT_FUNCTION):
        cursor.execute(f"DROP FUNCTION public.{function}(uuid)")
