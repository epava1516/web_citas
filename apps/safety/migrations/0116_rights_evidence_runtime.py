"""Serialize validation and append before taking action/head row locks."""

from django.db import migrations

from apps.safety.evidence_chain_sql_v1 import FUNCTIONS


def runtime_functions(apps, schema_editor):
    sql = FUNCTIONS[FUNCTIONS.index("CREATE FUNCTION public.rights_evidence_locked_head") :]
    # Only replace these three functions; all other version-one DDL stays untouched.
    for name in ("locked_head", "insert", "tombstone"):
        marker = "CREATE FUNCTION public.rights_evidence_" + name
        start = sql.index(marker)
        end = (
            sql.index("END $$;", start) + len("END $$;")
            if name != "locked_head"
            else sql.index("$$;", start) + 3
        )
        definition = sql[start:end].replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1)
        if name == "locked_head":
            definition = """CREATE OR REPLACE FUNCTION public.rights_evidence_locked_head(case_id uuid)
RETURNS TABLE(sequence bigint,digest text)
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended(case_id::text, 817115));
 RETURN QUERY SELECT h.sequence,h.digest::text FROM public.safety_rightsevidencehead h
 WHERE h.request_id=case_id FOR UPDATE;
END $$;"""
        elif name == "insert":
            definition = definition.replace(
                " SELECT request_id INTO STRICT case_id",
                """ SELECT request_id INTO STRICT case_id FROM public.safety_rightsaction WHERE id=NEW.action_id;
 PERFORM pg_advisory_xact_lock(hashtextextended(case_id::text,817115));
 SELECT request_id INTO STRICT case_id""",
                1,
            )
        else:
            definition = definition.replace(
                "BEGIN\n",
                "BEGIN\n PERFORM pg_advisory_xact_lock(hashtextextended(case_id::text,817115));\n",
                1,
            )
        schema_editor.execute(definition)


class Migration(migrations.Migration):
    dependencies = [
        ("safety", "0112_export_validation_seal"),
        ("safety", "0115_rights_evidence_chain"),
    ]
    operations = [migrations.RunPython(runtime_functions, migrations.RunPython.noop)]
