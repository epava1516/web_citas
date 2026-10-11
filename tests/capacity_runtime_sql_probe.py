"""Experimental only: ordered runtime SQL trace, never a production trust producer.

Trace records all fetched rows, not merely the resulting trust decision. Timing
includes independent function attestation. No credentials or SQL are reported.
"""

import ast
import inspect
import json
import re

from apps.safety.evidence_chain import _runtime_is_trusted
from apps.safety.evidence_chain_sql_v1 import EVENT, HEAD, TABLES


def source_queries():
    tree = ast.parse(inspect.getsource(_runtime_is_trusted))
    queries = [ast.literal_eval(node.args[0]) for node in ast.walk(tree)
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and node.func.attr == "execute"]
    if len(queries) != 9:
        raise ValueError("Runtime reference stages changed")
    return queries


def _literal(value):
    return "'" + value.replace("'", "''") + "'"


def _name(value):
    if not re.fullmatch(r"mod08_probe_[a-z0-9_]+", value):
        raise ValueError("Invalid experimental object name")
    return "public." + value


class TraceCursor:
    def __init__(self, raw, after_stage=None):
        self.raw = raw
        self.stages = []
        self.after_stage = after_stage

    def execute(self, statement, params=None):
        self.raw.execute(statement, params)

    def _record(self, rows):
        self.stages.append([list(row) for row in rows])
        if self.after_stage:
            self.after_stage(len(self.stages))

    def fetchone(self):
        row = self.raw.fetchone()
        self._record([] if row is None else [row])
        return row

    def fetchall(self):
        rows = self.raw.fetchall()
        self._record(rows)
        return rows


def reference(cursor, after_stage=None):
    traced = TraceCursor(cursor, after_stage)
    trusted = _runtime_is_trusted(traced)
    return {"trusted": trusted, "stages": traced.stages}


def definition(name, *, sequence=None, pause_stage=None, pause_key=None):
    qualified = _name(name)
    names = list(TABLES) + [HEAD, EVENT]
    names_sql = "ARRAY[" + ",".join(map(_literal, names)) + "]::text[]"
    queries = source_queries()
    queries[2] = queries[2].replace("%s", names_sql)
    queries[3] = queries[3].replace("%s", names_sql)
    queries[4] = queries[4].replace("%s::text[]", "owners")
    queries[7] = queries[7].replace("%s", names_sql)
    for value in ("public." + HEAD, "public." + EVENT):
        queries[8] = queries[8].replace("%s", _literal(value), 1)
    widths = [4, 2, 5, 2, 1, 1, 4, 6, 2]
    checks = [
        "IF n=0 THEN RETURN jsonb_build_object('error','missing_role','stages',trace); END IF; "
        "IF EXISTS(SELECT FROM jsonb_array_elements(rows->0) e WHERE e='true'::jsonb) THEN trusted:=false; END IF;",
        "IF EXISTS(SELECT FROM jsonb_array_elements(rows->0) e WHERE e='true'::jsonb) THEN trusted:=false; END IF;",
        f"IF n<>{len(names)} OR EXISTS(SELECT FROM jsonb_array_elements(rows) r WHERE "
        "r->2='true'::jsonb OR r->3='true'::jsonb OR r->4='true'::jsonb) THEN trusted:=false; END IF; "
        "SELECT array_agg(r->>1) INTO owners FROM jsonb_array_elements(rows) r;",
        "IF EXISTS(SELECT FROM jsonb_array_elements(rows) r WHERE "
        f"NOT (r->>0=ANY(ARRAY[{','.join(map(_literal, TABLES))}])) OR r->>1<>'id') "
        "THEN trusted:=false; END IF;",
        "IF n<>cardinality(owners) OR EXISTS(SELECT FROM jsonb_array_elements(rows) r "
        "WHERE r->0='true'::jsonb) THEN trusted:=false; END IF;",
        "IF n=0 THEN RETURN jsonb_build_object('error','missing_action','stages',trace); END IF; "
        "IF rows->0->0='true'::jsonb THEN trusted:=false; END IF;",
        "IF rows->0 IS DISTINCT FROM '[\"rights_evidence_action_scope_guard\",\"O\",false,true]'::jsonb "
        "THEN trusted:=false; END IF;",
        "FOR item IN SELECT value FROM jsonb_array_elements(rows) LOOP "
        "IF item->5='true'::jsonb THEN "
        "by_table:=jsonb_set(by_table,ARRAY[item->>0], "
        "coalesce(by_table->(item->>0),'{}'::jsonb) || "
        "jsonb_build_object(item->>1,jsonb_build_array(item->2,item->3,item->4))); END IF; END LOOP; "
        "FOREACH tab IN ARRAY names LOOP "
        "IF by_table->tab->'rights_evidence_no_modify' IS DISTINCT FROM "
        "'[\"rights_evidence_guard\",\"O\",false]'::jsonb OR "
        "by_table->tab->'rights_evidence_no_truncate' IS DISTINCT FROM "
        "'[\"rights_evidence_guard\",\"O\",false]'::jsonb THEN trusted:=false; EXIT; END IF; "
        "IF tab=ANY(evidence_tables) THEN "
        "IF by_table->tab->'rights_evidence_record' IS DISTINCT FROM "
        "'[\"rights_evidence_insert\",\"O\",true]'::jsonb THEN trusted:=false; EXIT; END IF; "
        "ELSE IF by_table->tab->'rights_evidence_no_direct_insert' IS DISTINCT FROM "
        "'[\"rights_evidence_guard\",\"O\",false]'::jsonb THEN trusted:=false; EXIT; END IF; END IF; END LOOP;",
        "IF EXISTS(SELECT FROM jsonb_array_elements(rows->0) e WHERE e='true'::jsonb) THEN trusted:=false; END IF;",
    ]
    stages = []
    for stage, (query, width, check) in enumerate(zip(queries, widths, checks), 1):
        # Every query retains its original projection and ordering. Column aliases
        # avoid JSONB silently dropping repeated has_table_privilege column names.
        aliases = ",".join(f"c{i}" for i in range(width))
        fields = ",".join(f"rec.c{i}" for i in range(width))
        block = (f"rows:='[]'::jsonb; n:=0; FOR rec IN SELECT * FROM ({query}) q({aliases}) LOOP "
                 f"rows:=rows || jsonb_build_array(jsonb_build_array({fields})); n:=n+1; END LOOP; "
                 "trace:=trace || jsonb_build_array(rows); ")
        if stage == pause_stage:
            if type(pause_key) is not int:
                raise ValueError("Experimental pause requires an integer key")
            block += f"PERFORM pg_catalog.pg_advisory_xact_lock({pause_key}); "
        stages.append(block + check + " IF NOT trusted THEN RETURN "
                      "jsonb_build_object('trusted',false,'stages',trace); END IF;")
    counter = f"PERFORM pg_catalog.nextval({_literal(_name(sequence))}::regclass);" if sequence else ""
    return f"""CREATE FUNCTION {qualified}() RETURNS jsonb LANGUAGE plpgsql
VOLATILE SECURITY INVOKER PARALLEL UNSAFE SET search_path=pg_catalog,pg_temp AS $probe$
DECLARE trace jsonb:='[]'; rows jsonb; rec record; item jsonb; n integer;
trusted boolean:=true; owners text[]; by_table jsonb:='{{}}'; tab text;
names text[]:={names_sql}; evidence_tables text[]:=ARRAY[{','.join(map(_literal, TABLES))}];
BEGIN {counter} {' '.join(stages)}
RETURN jsonb_build_object('trusted',true,'stages',trace); END $probe$"""


def install(cursor, name, **options):
    cursor.execute(definition(name, **options))
    cursor.execute(
        "SELECT pg_get_functiondef(p.oid),pg_get_userbyid(p.proowner) "
        "FROM pg_catalog.pg_proc p WHERE p.oid=%s::regprocedure", [_name(name) + "()"],
    )
    return cursor.fetchone()


def attest(cursor, name, expected):
    cursor.execute(
        "SELECT pg_get_functiondef(p.oid),p.provolatile,p.prosecdef,p.proparallel,p.proconfig,"
        "l.lanname,pg_get_userbyid(p.proowner),current_user,"
        "pg_has_role(current_user,p.proowner,'MEMBER') "
        "FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_language l ON l.oid=p.prolang "
        "WHERE p.oid=%s::regprocedure", [_name(name) + "()"],
    )
    row = cursor.fetchone()
    if (row is None or row[:6] != (expected[0], "v", False, "u", ["search_path=pg_catalog, pg_temp"], "plpgsql")
            or row[6] != expected[1] or row[6] == row[7] or row[8]):
        raise ValueError("Experimental runtime helper attestation failed")


def probe(cursor, name, expected):
    attest(cursor, name, expected)
    cursor.execute(f"SELECT {_name(name)}() AS evidence")
    value = cursor.fetchone()[0]
    if isinstance(value, str):
        value = json.loads(value)
    if value.get("error") == "missing_role":
        raise TypeError("'NoneType' object is not iterable")
    if value.get("error") == "missing_action":
        raise TypeError("'NoneType' object is not subscriptable")
    return value
