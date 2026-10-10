"""Versioned PostgreSQL DDL shared by migration and completeness checks."""

TABLES = (
    "safety_rightsportabilityread",
    "safety_rightsportabilityreview",
    "safety_rightsportabilityselectionread",
    "safety_rightsportabilityselectionreview",
    "safety_rightsportabilityimageread",
    "safety_rightsportabilitycoverageread",
    "safety_rightsportabilitycoveragereview",
)
HEAD = "safety_rightsevidencehead"
EVENT = "safety_rightsevidenceevent"
ZERO = "0" * 64

FUNCTIONS = r"""
CREATE FUNCTION public.rights_evidence_row_hash(body jsonb) RETURNS text
LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public SET timezone = 'UTC' AS $$
 SELECT encode(sha256(convert_to(
   jsonb_set(body, '{created_at}', to_jsonb(to_char(
     (body->>'created_at')::timestamptz AT TIME ZONE 'UTC',
     'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')))::text, 'UTF8')), 'hex')
$$;
CREATE FUNCTION public.rights_evidence_link(
 case_id uuid, seq bigint, kind text, source_table text, source_pk text,
 payload text, previous text, occurred timestamptz) RETURNS text
LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public SET timezone = 'UTC' AS $$
 SELECT encode(sha256(convert_to(jsonb_build_array(
   'rights-evidence-chain-v1', case_id::text, seq, kind, source_table,
   source_pk, payload, previous,
   to_char(occurred AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))::text, 'UTF8')), 'hex')
$$;
CREATE FUNCTION public.rights_evidence_locked_head(case_id uuid)
RETURNS TABLE(sequence bigint, digest text)
LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog, public AS $$
 SELECT h.sequence,h.digest FROM public.safety_rightsevidencehead h
 WHERE h.request_id=case_id FOR SHARE
$$;
REVOKE ALL ON FUNCTION public.rights_evidence_locked_head(uuid) FROM PUBLIC;
CREATE FUNCTION public.rights_evidence_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE owner_name text;
BEGIN
 SELECT pg_get_userbyid(relowner) INTO owner_name FROM pg_class WHERE oid = TG_RELID;
 IF current_user <> owner_name THEN
   RAISE EXCEPTION 'Immutable rights evidence cannot be modified' USING ERRCODE = '42501';
 END IF;
 IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
 IF TG_OP = 'TRUNCATE' THEN RETURN NULL; END IF;
 RETURN NEW;
END $$;
CREATE FUNCTION public.rights_evidence_action_scope_guard() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE owner_name text; source_name text; linked boolean;
BEGIN
 IF ROW(NEW.request_id,NEW.actor_id,NEW.operation,NEW.expected_version,NEW.key)
 IS NOT DISTINCT FROM ROW(OLD.request_id,OLD.actor_id,OLD.operation,OLD.expected_version,OLD.key)
 THEN RETURN NEW; END IF;
 SELECT pg_get_userbyid(relowner) INTO owner_name FROM pg_class WHERE oid=TG_RELID;
 IF current_user=owner_name THEN RETURN NEW; END IF;
 FOREACH source_name IN ARRAY ARRAY[
  'safety_rightsportabilityread','safety_rightsportabilityreview',
  'safety_rightsportabilityselectionread','safety_rightsportabilityselectionreview',
  'safety_rightsportabilityimageread','safety_rightsportabilitycoverageread',
  'safety_rightsportabilitycoveragereview'] LOOP
  EXECUTE format('SELECT EXISTS(SELECT 1 FROM public.%I WHERE action_id=$1)',source_name)
  INTO linked USING OLD.id;
  IF linked THEN
   RAISE EXCEPTION 'Immutable rights evidence action scope cannot change' USING ERRCODE='42501';
  END IF;
 END LOOP;
 RETURN NEW;
END $$;
CREATE FUNCTION public.rights_evidence_append(
 case_id uuid, event_kind text, source_name text, row_id text,
 row_hash text, occurred timestamptz) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public SET timezone = 'UTC' AS $$
DECLARE seq bigint; previous text; next_digest text;
BEGIN
 INSERT INTO public.safety_rightsevidencehead(request_id, sequence, digest)
 VALUES(case_id, 0, repeat('0',64)) ON CONFLICT(request_id) DO NOTHING;
 SELECT sequence, digest INTO seq, previous
 FROM public.safety_rightsevidencehead WHERE request_id = case_id FOR UPDATE;
 seq := seq + 1;
 next_digest := public.rights_evidence_link(case_id, seq, event_kind, source_name,
                                           row_id, row_hash, previous, occurred);
 INSERT INTO public.safety_rightsevidenceevent(
  request_id,sequence,kind,source_table,source_pk,payload_digest,previous_digest,digest,created_at)
 VALUES(case_id,seq,event_kind,source_name,row_id,row_hash,previous,next_digest,occurred);
 UPDATE public.safety_rightsevidencehead SET sequence=seq,digest=next_digest WHERE request_id=case_id;
END $$;
REVOKE ALL ON FUNCTION public.rights_evidence_append(uuid,text,text,text,text,timestamptz) FROM PUBLIC;
CREATE FUNCTION public.rights_evidence_insert() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public SET timezone = 'UTC' AS $$
DECLARE case_id uuid;
BEGIN
 SELECT request_id INTO STRICT case_id FROM public.safety_rightsaction WHERE id = NEW.action_id FOR UPDATE;
 PERFORM public.rights_evidence_append(case_id, 'row', TG_TABLE_NAME, NEW.id::text,
                                      public.rights_evidence_row_hash(to_jsonb(NEW)), NEW.created_at);
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION public.rights_evidence_insert() FROM PUBLIC;
CREATE FUNCTION public.rights_evidence_tombstone(case_id uuid, opaque_id uuid, reason text) RETURNS void
LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public SET timezone = 'UTC' AS $$
DECLARE previous_payload text;
BEGIN
 IF reason NOT IN ('expired_payload_purged', 'legal_erasure_recorded') OR reason IS NULL THEN
   RAISE EXCEPTION 'Unsupported evidence tombstone' USING ERRCODE='22023';
 END IF;
 INSERT INTO public.safety_rightsevidencehead(request_id,sequence,digest)
 VALUES(case_id,0,repeat('0',64)) ON CONFLICT(request_id) DO NOTHING;
 PERFORM 1 FROM public.safety_rightsevidencehead WHERE request_id=case_id FOR UPDATE;
 SELECT payload_digest INTO previous_payload FROM public.safety_rightsevidenceevent
 WHERE request_id=case_id AND kind='tombstone' AND source_pk=opaque_id::text;
 IF FOUND THEN
   IF previous_payload <> encode(sha256(convert_to(reason,'UTF8')),'hex') THEN
     RAISE EXCEPTION 'Conflicting evidence tombstone key' USING ERRCODE='22023';
   END IF;
   RETURN;
 END IF;
 PERFORM public.rights_evidence_append(case_id,'tombstone','rights_payload_purge',opaque_id::text,
   encode(sha256(convert_to(reason,'UTF8')),'hex'),clock_timestamp());
END $$;
REVOKE ALL ON FUNCTION public.rights_evidence_tombstone(uuid,uuid,text) FROM PUBLIC;
"""


def install(cursor):
    cursor.execute(FUNCTIONS)
    backfill(cursor)
    cursor.execute(
        "CREATE TRIGGER rights_evidence_action_scope BEFORE UPDATE ON public.safety_rightsaction "
        "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_action_scope_guard()"
    )
    for table in TABLES:
        cursor.execute(
            f'CREATE TRIGGER rights_evidence_record AFTER INSERT ON public."{table}" '
            "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_insert()"
        )
    for table in (*TABLES, HEAD, EVENT):
        cursor.execute(
            f'CREATE TRIGGER rights_evidence_no_modify BEFORE UPDATE OR DELETE ON public."{table}" '
            "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_guard()"
        )
        cursor.execute(
            f'CREATE TRIGGER rights_evidence_no_truncate BEFORE TRUNCATE ON public."{table}" '
            "FOR EACH STATEMENT EXECUTE FUNCTION public.rights_evidence_guard()"
        )
        cursor.execute(f'REVOKE UPDATE, DELETE, TRUNCATE ON public."{table}" FROM PUBLIC')
    for table in (HEAD, EVENT):
        cursor.execute(
            f'CREATE TRIGGER rights_evidence_no_direct_insert BEFORE INSERT ON public."{table}" '
            "FOR EACH ROW EXECUTE FUNCTION public.rights_evidence_guard()"
        )
        cursor.execute(f'REVOKE INSERT ON public."{table}" FROM PUBLIC')


def backfill(cursor):
    for table in sorted(TABLES):
        # Only adds missing rows: an altered already-linked row remains detectable.
        cursor.execute(
            f'''
          SELECT public.rights_evidence_append(a.request_id,'row',%s,s.id::text,
             public.rights_evidence_row_hash(to_jsonb(s)),s.created_at)
          FROM public."{table}" s JOIN public.safety_rightsaction a ON a.id=s.action_id
          WHERE NOT EXISTS(SELECT 1 FROM public.safety_rightsevidenceevent e
             WHERE e.kind='row' AND e.source_table=%s AND e.source_pk=s.id::text)
          ORDER BY s.id
        ''',
            [table, table],
        )


def uninstall(cursor):
    cursor.execute(
        "DROP TRIGGER IF EXISTS rights_evidence_action_scope ON public.safety_rightsaction"
    )
    for table in (*TABLES, HEAD, EVENT):
        for name in (
            "rights_evidence_record",
            "rights_evidence_no_modify",
            "rights_evidence_no_truncate",
            "rights_evidence_no_direct_insert",
        ):
            cursor.execute(f'DROP TRIGGER IF EXISTS "{name}" ON public."{table}"')
    for function in (
        "rights_evidence_tombstone(uuid,uuid,text)",
        "rights_evidence_insert()",
        "rights_evidence_append(uuid,text,text,text,text,timestamptz)",
        "rights_evidence_guard()",
        "rights_evidence_action_scope_guard()",
        "rights_evidence_locked_head(uuid)",
        "rights_evidence_link(uuid,bigint,text,text,text,text,text,timestamptz)",
        "rights_evidence_row_hash(jsonb)",
    ):
        cursor.execute("DROP FUNCTION public." + function)
