"""Diagnostic data-only prototype. Not an authority API or application fallback.

Private temporary PostgreSQL artifacts, no actors/proofs/latest/chain checks omitted
from an endpoint: this module is never connected to an endpoint. Current schema
binding is deliberately a screening mechanism, not a complete catalog attestation.
"""
import hashlib
import json
from datetime import timedelta

from cryptography.fernet import InvalidToken
from django.core.exceptions import ValidationError
from django.db import connection
from django.utils import timezone

from apps.safety.crypto import seal, unseal
from apps.safety.rights import fingerprint
from apps.safety.rights_exports import canonical
from apps.safety.rights_source_fingerprint import part_tables, source_fingerprint

SCHEMA = "diagnostic-data-manifest-v1"
MAX_XID_DISTANCE = 1 << 30


def metadata():
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_current_xact_id()::text, (SELECT oid FROM pg_database WHERE datname=current_database())")
        xid, database = cursor.fetchone()
        cursor.execute("SELECT c.oid,c.relkind,a.attnum,a.attname,a.atttypid,a.atttypmod,a.attgenerated,"
                       "a.attcollation,a.attnotnull,a.attmissingval::text,pg_get_expr(d.adbin,d.adrelid) "
                       "FROM pg_class c JOIN pg_attribute a ON a.attrelid=c.oid "
                       "LEFT JOIN pg_attrdef d ON d.adrelid=c.oid AND d.adnum=a.attnum "
                       "WHERE c.relnamespace='public'::regnamespace AND c.relname=ANY(%s) "
                       "AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.oid,a.attnum",
                       [list(part_tables().values())])
        shape = cursor.fetchall()
    return int(xid), database, hashlib.sha256(canonical(shape).encode()).hexdigest()


def binding(person, listing, case):
    return [str(person.pk), str(listing.pk), str(case.pk), case.version, person.manager_version]


def prepare(person, listing, case, source):
    if not connection.in_atomic_block:
        raise RuntimeError("Prototype preparation requires atomic context")
    xid, database, shape = metadata()
    manifest = dict(schema=SCHEMA, scope=binding(person, listing, case), xid=xid,
                    database=database, shape=shape, versions=source_fingerprint(person, listing, case),
                    source_digest=fingerprint(canonical(source)),
                    rows=len(source["revisions"]), expires=(timezone.now()+timedelta(minutes=5)).timestamp())
    # This caller builds the source under an unchanged before/after physical stamp.
    encrypted_manifest = seal(manifest)
    with connection.cursor() as cursor:
        cursor.execute("CREATE TEMP TABLE diagnostic_page_manifest (position integer PRIMARY KEY, manifest text, content text)")
        for start in range(0, manifest["rows"], 50):
            content = seal(dict(schema=SCHEMA, scope=manifest["scope"], source_digest=manifest["source_digest"],
                                position=start//50, rows=manifest["rows"], data=source["revisions"][start:start+50]))
            cursor.execute("INSERT INTO diagnostic_page_manifest VALUES(%s,%s,%s)",
                           [start//50, encrypted_manifest, content])
    return manifest["source_digest"]


def read(person, listing, case, position, expected_digest):
    if not connection.in_atomic_block:
        raise RuntimeError("Prototype read requires atomic context")
    before = source_fingerprint(person, listing, case)
    xid, database, shape = metadata()
    with connection.cursor() as cursor:
        cursor.execute("SELECT manifest,content FROM diagnostic_page_manifest WHERE position=%s", [position])
        record = cursor.fetchone()
    if record is None:
        raise ValidationError("Prototype chunk unavailable")
    try:
        manifest, content = (unseal(value) for value in record)
    except (InvalidToken, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ValidationError("Prototype chunk authentication failed") from error
    if (manifest["schema"] != SCHEMA or manifest["scope"] != binding(person, listing, case)
            or manifest["source_digest"] != expected_digest
            or manifest["database"] != database or manifest["shape"] != shape
            or not 0 <= xid-manifest["xid"] < MAX_XID_DISTANCE
            or manifest["expires"] <= timezone.now().timestamp()
            or manifest["versions"] != before
            or content["schema"] != SCHEMA or content["scope"] != manifest["scope"]
            or content["source_digest"] != manifest["source_digest"]
            or content["position"] != position or content["rows"] != manifest["rows"]
            or not 0 <= position*50 < manifest["rows"]
            or len(content["data"]) != min(50, manifest["rows"]-position*50)):
        raise ValidationError("Prototype data binding changed")
    if source_fingerprint(person, listing, case) != before:
        raise ValidationError("Prototype source changed during read")
    return content["data"]
