"""Pre-integration cost gate: freshly hash contents, never just tuple versions.

No production cache or authority API. This rejects silent physical content drift
and retains the prototype's schema/version/chunk checks. It is still not complete
catalog, permissions, lock, retention or endpoint equivalence.
"""
import re

from django.db import connection

from apps.listings.models import Revision
from apps.safety.rights_source_fingerprint import _parts, part_tables
from tests.capacity_page_manifest_prototype import read

# Exactly the seven already deferred source fields plus the original generated
# search vector. Do not charge this experiment for hashing unused large vectors.
REVISION_UNUSED = {
    "search_document", "source_revision", "step", "edit_version", "telegram",
    "contact_exposure_accepted", "publisher_acceptance", "updated_at",
}


def physical_stamp(person, listing, case):
    parts, params = _parts(person, listing, case)
    tables = part_tables()
    revision_columns = [field.column for field in Revision._meta.concrete_fields
                        if field.name not in REVISION_UNUSED]
    statements = []
    for tag, selector in parts:
        table = tables[tag]
        # Identifiers come only from the fixed SQL inventory/model, not a caller.
        assert re.fullmatch(r"[a-z_]+", table)
        if tag == "revision":
            projection = ",".join('physical."' + column + '"' for column in revision_columns)
            row = f"ROW({projection})"
        else:
            row = "physical"
        statements.append(
            f"SELECT '{tag}' AS tag,physical.id::text AS id,"
            "pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
            f"pg_catalog.row_to_json({row})::text,'UTF8')),'hex') AS digest "
            f"FROM public.{table} physical JOIN ({selector}) selected "
            "ON physical.id::text=selected.id"
        )
    query = (
        "SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to("
        "coalesce(string_agg(tag||':'||id||':'||digest,',' ORDER BY tag,id),''),"
        "'UTF8')),'hex'),count(*) FROM (" + " UNION ALL ".join(statements) + ") contents"
    )
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchone()


def read_physical(person, listing, case, position, expected_digest, expected_physical):
    before = physical_stamp(person, listing, case)
    if before != expected_physical:
        from django.core.exceptions import ValidationError

        raise ValidationError("Prepared physical source changed")
    value = read(person, listing, case, position, expected_digest)
    if physical_stamp(person, listing, case) != before:
        from django.core.exceptions import ValidationError

        raise ValidationError("Physical source changed during page read")
    return value


def materialize_physical(person, listing, case, expected_digest, expected_physical, encrypted_header):
    """Lower bound for the existing ordinary-dict consumer contract.

    All contents are freshly hashed before/after. Only two physical scans, one
    bulk chunk query and one manifest decryption, not 30 independent read calls.
    Caller header is encrypted synthetic fixture data, not a production store.
    Missing product locks/catalog/expiry callbacks can only add work to this gate.
    """
    from django.core.exceptions import ValidationError
    from django.utils import timezone

    from apps.safety.crypto import unseal
    from apps.safety.rights_source_fingerprint import source_fingerprint
    from tests.capacity_page_manifest_prototype import (
        MAX_XID_DISTANCE,
        SCHEMA,
        binding,
        metadata,
    )

    if physical_stamp(person, listing, case) != expected_physical:
        raise ValidationError("Prepared physical source changed")
    versions = source_fingerprint(person, listing, case)
    xid, database, shape = metadata()
    with connection.cursor() as cursor:
        cursor.execute("SELECT position,manifest,content FROM diagnostic_page_manifest ORDER BY position")
        records = cursor.fetchall()
    if not records:
        raise ValidationError("Prepared chunks unavailable")
    manifest_token = records[0][1]
    manifest = unseal(manifest_token)
    if (manifest['schema'] != SCHEMA or manifest['scope'] != binding(person, listing, case)
            or manifest['source_digest'] != expected_digest
            or manifest['database'] != database or manifest['shape'] != shape
            or manifest['versions'] != versions
            or not 0 <= xid-manifest['xid'] < MAX_XID_DISTANCE
            or manifest['expires'] <= timezone.now().timestamp()
            or len(records) != (manifest['rows']+49)//50):
        raise ValidationError("Prepared manifest changed")
    rows = []
    for index, (position, token, ciphertext) in enumerate(records):
        data = unseal(ciphertext)
        if (position != index or token != manifest_token or data['schema'] != SCHEMA
                or data['scope'] != manifest['scope'] or data['source_digest'] != expected_digest
                or data['position'] != index or data['rows'] != manifest['rows']
                or len(data['data']) != min(50, manifest['rows']-index*50)):
            raise ValidationError("Prepared chunk changed")
        rows.extend(data['data'])
    source = unseal(encrypted_header)
    if source['source_digest'] != expected_digest or source['scope'] != manifest['scope']:
        raise ValidationError("Prepared header changed")
    source = source['header']
    source['revisions'] = rows
    if (source_fingerprint(person, listing, case) != versions
            or physical_stamp(person, listing, case) != expected_physical
            or manifest['expires'] <= timezone.now().timestamp()):
        raise ValidationError("Prepared source changed during materialization")
    return source
