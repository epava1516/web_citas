"""Completeness of the row-version fingerprint against the real source copy (PostgreSQL)."""

import re
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.db import connection, transaction
from test_reports import directory, photo_environment  # noqa: F401

from apps.catalog.models import Category, Municipality, PostalCode, Service, Zone
from apps.core.models import (
    Agency,
    AgencyMember,
    LegalAcceptance,
    LegalDocument,
    Person,
    PhoneClaim,
    RepresentationAction,
    VerificationCheck,
)
from apps.listings.models import Favorite, Listing, Rate, Revision
from apps.listings.profile_contract import LEGACY_CONTRACT
from apps.safety import rights_inspection_source
from apps.safety.rights_exports import canonical, source_copy
from apps.safety.rights_source_fingerprint import part_tables, source_fingerprint, source_rows

# Exact previous municipality selector, retained only as an equivalence oracle.
LEGACY_MUNICIPALITY = (
    "SELECT DISTINCT m.id::text, m.xmin::text || ':' || m.ctid::text FROM catalog_municipality m "
    "JOIN listings_revision r ON r.listing_id = %(listing)s AND (r.municipality_id = m.id "
    "OR EXISTS (SELECT 1 FROM listings_revision_travel_areas rt "
    "WHERE rt.revision_id = r.id AND rt.municipality_id = m.id))"
)

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.usefixtures("directory")]


def complete_subject():
    """A subject with a romantic profile and every private historical source family."""
    person = (
        Person.objects.filter(subject__isnull=False, listing__isnull=False)
        .select_related("subject", "listing")
        .order_by("pk")
        .first()
    )
    user, listing = person.subject, person.listing
    revision = Revision.objects.create(
        listing=listing,
        manager_version=person.manager_version,
        content_contract=LEGACY_CONTRACT,
        status="archived",
        title="Private synthetic historical content",
    )
    category = Category.objects.create(
        slug="fingerprint-private-legacy", name_es="Histórico privado", name_en="Private legacy"
    )
    service = Service.objects.create(
        slug="fingerprint-private-service",
        category=category,
        name_es="Servicio histórico",
        name_en="Historical service",
    )
    revision.categories.add(category)
    revision.services.add(service)
    document = LegalDocument.objects.order_by("pk").first()
    if not person.phone_claim_id:
        person.phone_claim = PhoneClaim.objects.create(phone="+34600000001", individual=user)
        person.save(update_fields=["phone_claim"])
    PhoneClaim.objects.get_or_create(phone="+34600000002", individual=user, agency=None)
    LegalAcceptance.objects.create(user=user, document=document, action="fixture")
    owned = Agency.objects.create(name="Fingerprint agency", owner=user)
    AgencyMember.objects.create(agency=owned, user=user)
    Favorite.objects.create(user=user, listing=Listing.objects.exclude(pk=listing.pk).first())
    VerificationCheck.objects.create(
        person=person, subject=user, manager_version=person.manager_version, provider="simulator"
    )
    RepresentationAction.objects.create(
        person=person,
        subject=user,
        manager_version=person.manager_version,
        action="fixture",
        document=document,
    )
    municipality = Municipality.objects.order_by("pk").first()
    revision.travel_areas.add(municipality)
    postal_code = PostalCode.objects.order_by("pk").first() or PostalCode.objects.create(
        code="99999", source="synthetic-fingerprint"
    )
    zone = Zone.objects.order_by("pk").first() or Zone.objects.create(
        code="fingerprint-zone",
        name="Fingerprint zone",
        municipality=municipality,
        source="synthetic-fingerprint",
    )
    Revision.objects.filter(pk=revision.pk).update(postal_code=postal_code, zone=zone)
    if not revision.rates.exists():
        Rate.objects.create(revision=revision, concept="Session", mode="consult")
    return person, listing


def traced_tables(operation):
    statements = []

    def wrapper(execute, sql, params, many, context):
        statements.append(sql)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(wrapper):
        operation()
    return {table for sql in statements for table in re.findall(r'(?:FROM|JOIN) "(\w+)"', sql)}


def test_every_table_read_by_the_source_copy_is_fingerprinted():
    person, listing = complete_subject()
    with transaction.atomic():
        read = traced_tables(lambda: source_copy(person, listing))
    assert read - set(part_tables().values()) == set()
    tags = {tag for tag, _, _ in source_rows(person, listing)}
    # Every family is populated by the fixture, so each mutation below exercises a real row.
    assert tags == set(part_tables())


def test_each_fingerprinted_family_detects_update_insert_and_delete():
    person, listing = complete_subject()
    tables = part_tables()
    rows = source_rows(person, listing)
    for tag in sorted({tag for tag, _, _ in rows}):
        identifier = next(row_id for row_tag, row_id, _ in rows if row_tag == tag)
        before = source_fingerprint(person, listing)
        with connection.cursor() as cursor:
            # A no-op UPDATE is still a new tuple version: the conservative direction.
            cursor.execute(f'UPDATE "{tables[tag]}" SET id = id WHERE id = %s', [identifier])
        assert source_fingerprint(person, listing) != before, tag
    revision = listing.revisions.order_by("pk").first()
    before = source_fingerprint(person, listing)
    rate = Rate.objects.create(revision=revision, concept="Inserted", mode="consult")
    inserted = source_fingerprint(person, listing)
    assert inserted != before
    rate.delete()
    assert source_fingerprint(person, listing) not in {inserted}
    favorite = Favorite.objects.filter(user=person.subject).first()
    before = source_fingerprint(person, listing)
    favorite.delete()
    assert source_fingerprint(person, listing) != before


def test_unrelated_rows_do_not_change_the_fingerprint():
    person, listing = complete_subject()
    before = source_fingerprint(person, listing)
    other = Listing.objects.exclude(pk=listing.pk).first()
    with connection.cursor() as cursor:
        cursor.execute('UPDATE "listings_revision" SET id = id WHERE listing_id = %s', [other.pk])
    assert source_fingerprint(person, listing) == before


def test_equal_fingerprint_implies_equal_source_and_account_branch_is_covered():
    person, listing = complete_subject()
    with transaction.atomic():
        first, digest = source_copy(person, listing), source_fingerprint(person, listing)
        assert source_fingerprint(person, listing) == digest
        assert canonical(source_copy(person, listing)) == canonical(first)
    account = SimpleNamespace(account_subject_id=person.subject_id)
    before = source_fingerprint(None, None, account)
    with connection.cursor() as cursor:
        cursor.execute('UPDATE "core_user" SET id = id WHERE id = %s', [person.subject_id])
    assert source_fingerprint(None, None, account) != before


def test_change_committed_during_the_shared_source_rejects_the_operation():
    person, listing = complete_subject()
    case = SimpleNamespace(
        pk=1,
        version=1,
        person_id=person.pk,
        account_subject_id=None,
        manager_version=person.manager_version,
    )
    other = Listing.objects.exclude(pk=listing.pk).last()
    from concurrent.futures import ThreadPoolExecutor

    def concurrent_change():
        # Compatible with the copy's locks (key-share on the subject), committed mid-operation.
        from django.db import connections

        try:
            Favorite.objects.create(user_id=person.subject_id, listing_id=other.pk)
        finally:
            connections.close_all()

    with pytest.raises(Exception, match="changed before return"):
        with transaction.atomic():
            with rights_inspection_source.inspection_source(person, listing, case):
                with ThreadPoolExecutor(max_workers=1) as pool:
                    pool.submit(concurrent_change).result(timeout=30)


def test_two_updates_in_one_transaction_change_tuple_identity():
    person, listing = complete_subject()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("UPDATE core_person SET alias = %s WHERE id = %s", ["first", person.pk])
        before = source_fingerprint(person, listing)
        with connection.cursor() as cursor:
            cursor.execute("UPDATE core_person SET alias = %s WHERE id = %s", ["second", person.pk])
        assert source_fingerprint(person, listing) != before


def test_same_transaction_caller_field_drift_rejects_shared_source():
    from django.core.exceptions import ValidationError

    person, listing = complete_subject()
    case = SimpleNamespace(
        pk=1,
        version=1,
        person_id=person.pk,
        account_subject_id=None,
        manager_version=person.manager_version,
    )
    with pytest.raises(ValidationError, match="changed before return"):
        with transaction.atomic():
            Person.objects.filter(pk=person.pk).update(alias="first update")
            person.refresh_from_db()
            with rights_inspection_source.inspection_source(person, listing, case):
                Person.objects.filter(pk=person.pk).update(alias="second update")


def test_municipality_id_union_matches_exact_legacy_rows_and_full_digest():
    from apps.safety.rights_source_fingerprint import PROFILE_PARTS, _parts, _union

    person, listing = complete_subject()
    peer = Listing.objects.exclude(pk=listing.pk).first()
    base = Municipality.objects.first()
    municipalities = {
        name: Municipality.objects.create(
            code="fp-" + uuid4().hex[:12],
            name="Synthetic " + name,
            province=base.province,
            source=base.source,
        )
        for name in ("direct", "shared", "travel", "foreign", "foreign_travel", "unused")
    }
    # Preserve unrelated listings; isolate exactly this listing's municipal references.
    Revision.objects.filter(listing=listing).update(municipality=None)
    Revision.travel_areas.through.objects.filter(revision__listing=listing).delete()
    revisions = [
        Revision.objects.create(
            listing=listing, manager_version=person.manager_version, municipality=municipality
        )
        for municipality in (municipalities["direct"], municipalities["direct"], None, None)
    ]
    revisions[0].travel_areas.add(municipalities["direct"], municipalities["shared"])
    revisions[1].travel_areas.add(municipalities["shared"], municipalities["travel"])
    revisions[2].travel_areas.add(municipalities["travel"])
    other = Revision.objects.create(
        listing=peer,
        manager_version=peer.person.manager_version,
        municipality=municipalities["foreign"],
    )
    other.travel_areas.add(municipalities["foreign_travel"], municipalities["shared"])
    selector = dict(PROFILE_PARTS)["municipality"]
    expected = {str(municipalities[name].pk) for name in ("direct", "shared", "travel")}
    # Compare identical tuple versions in one transaction, including NULL and missing listing.
    with transaction.atomic(), connection.cursor() as cursor:
        for selected_listing in (listing, None):
            values = {"listing": selected_listing.pk if selected_listing else None}
            cursor.execute(LEGACY_MUNICIPALITY, values)
            old = set(cursor.fetchall())
            cursor.execute(selector, values)
            new = cursor.fetchall()
            assert set(new) == old and len(new) == len(old)
            assert {identifier for identifier, _ in new} == (
                expected if selected_listing else set()
            )
            parts, bindings = _parts(person, selected_listing, None)
            old_parts = [
                (tag, LEGACY_MUNICIPALITY if tag == "municipality" else sql) for tag, sql in parts
            ]
            cursor.execute(f"SELECT tag, id, version FROM ({_union(old_parts)}) AS rows", bindings)
            old_rows = set(cursor.fetchall())
            assert set(source_rows(person, selected_listing)) == old_rows
            cursor.execute(
                "SELECT encode(sha256(convert_to(coalesce(string_agg(tag || ':' || id || ':' || version, ',' "
                f"ORDER BY tag, id), ''), 'UTF8')), 'hex'), count(*) FROM ({_union(old_parts)}) AS rows",
                bindings,
            )
            digest, count = cursor.fetchone()
            assert source_fingerprint(person, selected_listing) == f"{digest}:{count}"
        account = SimpleNamespace(account_subject_id=person.subject_id)
        parts, bindings = _parts(None, None, account)
        assert "municipality" not in dict(parts)
        cursor.execute(f"SELECT tag, id, version FROM ({_union(parts)}) AS rows", bindings)
        assert set(source_rows(None, None, account)) == set(cursor.fetchall())
    before = source_fingerprint(person, listing)
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE catalog_municipality SET id=id WHERE id=%s", [municipalities["foreign"].pk]
        )
    assert source_fingerprint(person, listing) == before
    with connection.cursor() as cursor:
        cursor.execute(
            "UPDATE catalog_municipality SET id=id WHERE id=%s", [municipalities["travel"].pk]
        )
    assert source_fingerprint(person, listing) != before
