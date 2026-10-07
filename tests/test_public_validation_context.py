"""Fresh batched publication checks must match the existing guard exactly."""

from copy import copy

import pytest
from django.db.models import QuerySet
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.discovery import candidates
from apps.listings.forms import DetailsForm
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext, SnapshotDetails

pytestmark = pytest.mark.django_db(transaction=True)


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
