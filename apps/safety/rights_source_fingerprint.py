"""Row-version fingerprint of exactly the rows a rights source copy reads.

PostgreSQL gives every committed INSERT/UPDATE a new tuple version with its ``xmin`` and ``ctid``,
and a DELETE removes the row from the filtered set; locking with FOR UPDATE changes only
``xmax``. Comparing a fingerprint of (table, primary key, xmin, ctid) taken before a source read with
one taken at the end of the same operation therefore detects any committed change to those
rows without transferring their contents. It is used only to decide whether the full fresh
source re-read can be skipped; any difference keeps the original full comparison.

The row set must mirror ``source_copy`` exactly; completeness is enforced by tests that trace
the tables read by ``source_copy`` and mutate each family.
"""

from django.db import connection
from django.views.decorators.debug import sensitive_variables

# (tag, SQL selecting id/xmin with %(name)s parameters). Text interpolation is limited to
# constant table names below; all values are bound parameters.
PROFILE_PARTS = [
    (
        "user",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_user WHERE id = %(subject)s",
    ),
    (
        "person",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_person WHERE id = %(person)s",
    ),
    (
        "person_phone",
        "SELECT c.id::text, c.xmin::text || ':' || c.ctid::text FROM core_phoneclaim c "
        "JOIN core_person p ON p.phone_claim_id = c.id WHERE p.id = %(person)s",
    ),
    (
        "listing",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM listings_listing WHERE id = %(listing)s",
    ),
    (
        "revision",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM listings_revision WHERE listing_id = %(listing)s",
    ),
    (
        "revision_category",
        "SELECT rc.id::text, rc.xmin::text || ':' || rc.ctid::text FROM listings_revision_categories rc "
        "JOIN listings_revision r ON r.id = rc.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "category",
        "SELECT DISTINCT c.id::text, c.xmin::text || ':' || c.ctid::text FROM catalog_category c "
        "JOIN listings_revision_categories rc ON rc.category_id = c.id "
        "JOIN listings_revision r ON r.id = rc.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "revision_service",
        "SELECT rs.id::text, rs.xmin::text || ':' || rs.ctid::text FROM listings_revision_services rs "
        "JOIN listings_revision r ON r.id = rs.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "service",
        "SELECT DISTINCT s.id::text, s.xmin::text || ':' || s.ctid::text FROM catalog_service s "
        "JOIN listings_revision_services rs ON rs.service_id = s.id "
        "JOIN listings_revision r ON r.id = rs.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "revision_travel",
        "SELECT rt.id::text, rt.xmin::text || ':' || rt.ctid::text FROM listings_revision_travel_areas rt "
        "JOIN listings_revision r ON r.id = rt.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "municipality",
        "SELECT m.id::text, m.xmin::text || ':' || m.ctid::text FROM catalog_municipality m "
        "WHERE m.id IN (SELECT r.municipality_id FROM listings_revision r "
        "WHERE r.listing_id = %(listing)s UNION "
        "SELECT rt.municipality_id FROM listings_revision_travel_areas rt "
        "JOIN listings_revision r ON r.id = rt.revision_id WHERE r.listing_id = %(listing)s)",
    ),
    (
        "postal_code",
        "SELECT DISTINCT pc.id::text, pc.xmin::text || ':' || pc.ctid::text FROM catalog_postalcode pc "
        "JOIN listings_revision r ON r.postal_code_id = pc.id WHERE r.listing_id = %(listing)s",
    ),
    (
        "zone",
        "SELECT DISTINCT z.id::text, z.xmin::text || ':' || z.ctid::text FROM catalog_zone z "
        "JOIN listings_revision r ON r.zone_id = z.id WHERE r.listing_id = %(listing)s",
    ),
    (
        "rate",
        "SELECT t.id::text, t.xmin::text || ':' || t.ctid::text FROM listings_rate t "
        "JOIN listings_revision r ON r.id = t.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "photo",
        "SELECT ph.id::text, ph.xmin::text || ':' || ph.ctid::text FROM mediafiles_photo ph "
        "JOIN listings_revision r ON r.id = ph.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "blob",
        "SELECT DISTINCT b.id::text, b.xmin::text || ':' || b.ctid::text FROM mediafiles_blob b "
        "JOIN mediafiles_photo ph ON ph.blob_id = b.id "
        "JOIN listings_revision r ON r.id = ph.revision_id WHERE r.listing_id = %(listing)s",
    ),
    (
        "verification",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_verificationcheck "
        "WHERE person_id = %(person)s AND subject_id = %(subject)s",
    ),
    (
        "representation",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_representationaction "
        "WHERE person_id = %(person)s AND subject_id = %(subject)s",
    ),
    (
        "representation_document",
        "SELECT DISTINCT d.id::text, d.xmin::text || ':' || d.ctid::text FROM core_legaldocument d "
        "JOIN core_representationaction a ON a.document_id = d.id "
        "WHERE a.person_id = %(person)s AND a.subject_id = %(subject)s",
    ),
]
ACCOUNT_PARTS = [
    (
        "user",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_user WHERE id = %(subject)s",
    ),
    (
        "acceptance",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_legalacceptance WHERE user_id = %(subject)s",
    ),
    (
        "acceptance_document",
        "SELECT DISTINCT d.id::text, d.xmin::text || ':' || d.ctid::text FROM core_legaldocument d "
        "JOIN core_legalacceptance a ON a.document_id = d.id WHERE a.user_id = %(subject)s",
    ),
    (
        "personal_phone",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_phoneclaim "
        "WHERE individual_id = %(subject)s AND agency_id IS NULL",
    ),
    (
        "owned_agency",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_agency WHERE owner_id = %(subject)s",
    ),
    (
        "membership",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM core_agencymember WHERE user_id = %(subject)s",
    ),
    (
        "favorite",
        "SELECT id::text, xmin::text || ':' || ctid::text FROM listings_favorite WHERE user_id = %(subject)s",
    ),
]


def _parts(person, listing, case):
    if case and case.account_subject_id:
        return ACCOUNT_PARTS, {"subject": case.account_subject_id}
    subject = person.subject_id
    parts = [part for part in PROFILE_PARTS if part[0] != "listing" or listing]
    if subject:
        parts = parts + [part for part in ACCOUNT_PARTS if part[0] != "user"]
    return parts, {
        "subject": subject,
        "person": person.pk,
        "listing": listing.pk if listing else None,
    }


def _union(parts):
    return " UNION ALL ".join(
        f"SELECT '{tag}' AS tag, q.* FROM ({sql}) AS q(id, version)" for tag, sql in parts
    )


@sensitive_variables()
def source_fingerprint(person, listing, case=None):
    """SHA-256 over (tag, id, xmin, ctid) of every row the matching source_copy branch reads."""
    parts, values = _parts(person, listing, case)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT encode(sha256(convert_to(coalesce(string_agg(tag || ':' || id || ':' || version, ',' "
            f"ORDER BY tag, id), ''), 'UTF8')), 'hex'), count(*) FROM ({_union(parts)}) AS rows",
            values,
        )
        digest, count = cursor.fetchone()
    return f"{digest}:{count}"


def source_rows(person, listing, case=None):
    """The fingerprinted (tag, id, xmin) rows; used by completeness tests."""
    parts, values = _parts(person, listing, case)
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT tag, id, version FROM ({_union(parts)}) AS rows", values)
        return cursor.fetchall()


def part_tables():
    """First table of each part, i.e. the table whose rows the tag fingerprints."""
    import re

    return {
        tag: re.search(r"FROM (\w+)", sql).group(1) for tag, sql in PROFILE_PARTS + ACCOUNT_PARTS
    }
