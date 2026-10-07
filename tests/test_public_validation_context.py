"""Fresh batched publication checks must match the existing guard exactly."""

from copy import copy

import pytest
from django.db.models import QuerySet
from django.db import connection
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.discovery import candidates
from apps.listings.forms import ContactsForm, DetailsForm
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext, SnapshotDetails
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


def test_shared_fk_records_are_fresh_and_do_not_share_authorization(request):
    request.getfixturevalue("directory")
    populate(100)
    context = PublicationContext(candidates({}))
    assert len(context.rows) == 100
    agency_rows = [row for row in context.rows if row.person.agency_id]
    for attribute in [lambda row: row.person.agency,
                      lambda row: row.approved_revision.publisher_acceptance,
                      lambda row: row.approved_revision.municipality,
                      lambda row: row.approved_revision._pv_photos[0].blob]:
        grouped = {}
        for row in agency_rows:
            value = attribute(row)
            grouped.setdefault(value.pk, set()).add(id(value))
        assert all(len(identities) == 1 for identities in grouped.values())
    assert all(publicly_visible(row, context=context) for row in context.rows)
    person = agency_rows[0].person
    person.consent_revoked_at = timezone.now()
    person.save(update_fields=["consent_revoked_at"])
    fresh = PublicationContext(candidates({}))
    decisions = {row.pk: publicly_visible(row, context=fresh) for row in fresh.rows}
    assert decisions[agency_rows[0].pk] is False
    assert sum(decisions.values()) == 99
    agency = agency_rows[0].person.agency
    agency.verification_status = "failed"
    agency.save(update_fields=["verification_status"])
    fresh = PublicationContext(candidates({}))
    assert not any(publicly_visible(row, context=fresh)
                   for row in fresh.rows if row.person.agency_id == agency.pk)


def test_guard_defers_photo_signatures_without_changing_photo_eligibility(request):
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    row = next(row for row in context.rows if publicly_visible(row, context=context))
    revision = row.approved_revision
    photo = revision._pv_photos[0]
    assert {"signature", "regional_hashes"} <= photo.blob.get_deferred_fields()
    sql_seen = []

    def record(execute, sql, params, many, context):
        sql_seen.append(sql)
        return execute(sql, params, many, context)

    with connection.execute_wrapper(record):
        assert publicly_visible(row, context=context)
    assert not any("mediafiles_blob" in sql for sql in sql_seen)

    def equivalent(expected):
        fresh = PublicationContext(candidates({}))
        current = next(item for item in fresh.rows if item.pk == row.pk)
        assert publicly_visible(current, context=fresh) is expected
        assert publicly_visible(next(item for item in candidates({}) if item.pk == row.pk)) is expected

    blob_class, photo_class = type(photo.blob), type(photo)
    blob_class.objects.filter(pk=photo.blob_id).update(status="queued")
    equivalent(False)
    blob_class.objects.filter(pk=photo.blob_id).update(status="ready")
    equivalent(True)
    photo_class.objects.filter(pk=photo.pk).update(comparison_complete=False)
    equivalent(False)
    photo_class.objects.filter(pk=photo.pk).update(comparison_complete=True)
    equivalent(True)
    photo_class.objects.filter(pk=photo.pk).update(removed_at=timezone.now())
    equivalent(False)


def test_prepared_details_preserve_cleaning_and_independent_fields(request):
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    row = next(row for row in context.rows if publicly_visible(row, context=context))
    revision = row.approved_revision
    data = {
        name: getattr(revision, name)
        for name in SnapshotDetails.Meta.fields
        if not revision._meta.get_field(name).many_to_many
    }
    data.update({name: [item.pk for item in getattr(revision, "_pv_" + name)]
                 for name in ["categories", "services", "travel_areas"]})
    city = revision.municipality
    data.update(region=city.province.region_id, province=city.province_id,
                municipality=city.pk, postal_code=revision.postal_code_id or "",
                zone=revision.zone_id or "")
    first = context.details(data, revision)
    second = context.details(data, revision)
    assert first.fields is not second.fields
    for name in first.fields:
        assert first.fields[name] is not second.fields[name]
        assert first.fields[name].widget is not second.fields[name].widget
        if hasattr(first.fields[name], "queryset"):
            assert first.fields[name].queryset is not second.fields[name].queryset
        elif name in context.catalog:
            assert first.fields[name].snapshot is context.catalog[name]
            assert first.fields[name].prepare_value("missing") == "missing"
            target = next(iter(context.catalog[name].values()), None)
            if target is not None:
                assert first.fields[name].prepare_value(target) == target.pk
    first.fields["description"].required = False
    assert second.fields["description"].required
    assert context.details_fields["description"].required
    for changes in [{}, {"description": ""}, {"description": "www.invalid.example"},
                    {"description": "x" * 6001}, {"municipality": "missing"},
                    {"categories": [999999999]}, {"content_language": "invalid"}]:
        values = {**data, **changes}
        prepared_instance, fresh_instance = copy(revision), copy(revision)
        prepared = SnapshotDetails(context.catalog, values, instance=prepared_instance,
                                   prepared_fields=context.details_fields)
        fresh = SnapshotDetails(context.catalog, values, instance=fresh_instance)
        native = DetailsForm(values, instance=copy(revision))
        assert prepared.is_valid() == fresh.is_valid()
        assert prepared.is_valid() == native.is_valid()
        bound_instance = revision
        assert context.details_valid(values, bound_instance) == fresh.is_valid()
        assert prepared.errors.as_data() == fresh.errors.as_data()
        # Snapshot invalid-choice messages differ only by the submitted value
        # parameter. Compare field names and error codes with the native form.
        assert {name: [error.code for error in errors]
                for name, errors in prepared.errors.as_data().items()} == {
                    name: [error.code for error in errors]
                    for name, errors in native.errors.as_data().items()}
        assert prepared.cleaned_data.keys() == fresh.cleaned_data.keys()
        for name, value in prepared.cleaned_data.items():
            other = fresh.cleaned_data[name]
            if isinstance(value, QuerySet):
                assert isinstance(other, QuerySet)
                assert list(value) == list(other)
            else:
                assert value == other
        for name in SnapshotDetails.Meta.fields:
            if not revision._meta.get_field(name).many_to_many:
                assert getattr(prepared_instance, name) == getattr(fresh_instance, name)


def test_validation_bindings_do_not_share_cleaned_data_errors_or_instances(request, monkeypatch):
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    seen = []
    original = ContactsForm.full_clean

    def capture(form):
        original(form)
        seen.append(form)

    monkeypatch.setattr(ContactsForm, "full_clean", capture)
    rows = context.rows[:2]
    assert len(rows) == 2
    for index, row in enumerate(rows):
        data = {"whatsapp": bool(index), "telegram": "@Valid_name",
                "contact_exposure_accepted": True, "accept_publishing": True,
                "legal_version": context.document.version}
        assert context.contacts_valid(data, row.approved_revision)
        assert row.approved_revision.telegram == "Valid_name"
        assert row.approved_revision.whatsapp is bool(index)
        assert not context.contacts_valid({**data, "telegram": "not valid!"}, row.approved_revision)
        assert context.contacts_valid(data, row.approved_revision)
    assert len({id(form) for form in seen}) == len(seen)
    assert len({id(form.cleaned_data) for form in seen}) == len(seen)
    assert len({id(form.errors) for form in seen}) == len(seen)
    assert len({id(form._bound_fields_cache) for form in seen}) == len(seen)
    assert seen[0].instance is rows[0].approved_revision
    assert seen[-1].instance is rows[1].approved_revision
    assert seen[0].cleaned_data["telegram"] == "Valid_name"
    stats = context.field_clean_cache_stats["ContactsForm.telegram"]
    # Raw CharField cleaning is reused; form-specific normalization and rejection
    # still execute for every independent binding, including cached raw values.
    assert stats == {"calls": 6, "hits": 4, "misses": 2}


def test_field_clean_reuse_preserves_mutable_results_and_typed_keys(request, monkeypatch):
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    row = next(row for row in context.rows if publicly_visible(row, context=context))
    revision = row.approved_revision
    data = {name: getattr(revision, name) for name in SnapshotDetails.Meta.fields
            if not revision._meta.get_field(name).many_to_many}
    data.update({name: [item.pk for item in getattr(revision, "_pv_" + name)]
                 for name in ["categories", "services", "travel_areas"]})
    city = revision.municipality
    data.update(region=city.province.region_id, province=city.province_id,
                municipality=city.pk, postal_code=revision.postal_code_id or "",
                zone=revision.zone_id or "")
    seen = []
    original = SnapshotDetails.full_clean

    def capture(form):
        original(form)
        seen.append(form)

    monkeypatch.setattr(SnapshotDetails, "full_clean", capture)
    assert context.details_valid(data, revision)
    expected = list(seen[-1].cleaned_data["categories"])
    seen[-1].cleaned_data["categories"].clear()
    assert context.details_valid(data, revision)
    assert seen[-1].cleaned_data["categories"] == expected
    assert seen[-1].cleaned_data["categories"] is not seen[-2].cleaned_data["categories"]
    before = dict(context.field_clean_cache_stats["SnapshotDetails.province"])
    assert context.details_valid({**data, "province": str(city.province_id)}, revision)
    after = context.field_clean_cache_stats["SnapshotDetails.province"]
    assert after["misses"] == before["misses"] + 1
    # A new request obtains fresh catalog and fresh field memo tables.
    fresh = PublicationContext(candidates({}))
    assert fresh.field_clean_cache_stats == {}


def test_context_matches_ordinary_visibility_and_fresh_catalog_changes(request):
    request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision

    def verify(expected):
        ordinary = {row.pk for row in candidates({}) if publicly_visible(row)}
        context = PublicationContext(candidates({}))
        batched = {row.pk for row in context.rows if publicly_visible(row, context=context)}
        assert batched == ordinary
        assert (person.listing.pk in batched) is expected

    verify(True)
    original = revision.description
    for invalid in ["", "www.invalid.example", "hidden @contactname", "x" * 6001]:
        type(revision).objects.filter(pk=revision.pk).update(description=invalid)
        verify(False)
    type(revision).objects.filter(pk=revision.pk).update(description=original)
    verify(True)
    category = revision.categories.first()
    category.active = False
    category.save(update_fields=["active"])
    verify(False)
    category.active = True
    category.save(update_fields=["active"])
    verify(True)
    city = revision.municipality
    city.active = False
    city.save(update_fields=["active"])
    verify(False)
    city.active = True
    city.save(update_fields=["active"])
    verify(True)
    person.consent_revoked_at = timezone.now()
    person.save(update_fields=["consent_revoked_at"])
    verify(False)
    person.consent_revoked_at = None
    person.save(update_fields=["consent_revoked_at"])
    verify(True)
    grant_ids = list(
        person.representationaction_set.filter(action="grant").values_list("pk", flat=True)
    )
    grants = person.representationaction_set.filter(pk__in=grant_ids)
    grants.update(action="revoke")
    verify(False)
    grants.update(action="grant")
    verify(True)
    check = person.verificationcheck_set.latest("created_at")
    check.status = "failed"
    check.save(update_fields=["status"])
    verify(False)
    check.status = "passed"
    check.save(update_fields=["status"])
    verify(True)
