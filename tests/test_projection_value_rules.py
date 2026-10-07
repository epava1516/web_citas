"""Differential value-rule oracle frozen before the R2 extraction."""
from copy import copy

import pytest
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import override
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import projected_publication as projection
from apps.listings import forms as listing_forms
from apps.listings.discovery import candidates
from apps.listings.forms import DetailsForm, validate_listing_text
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext

pytestmark = pytest.mark.django_db(transaction=True)

def legacy_details_clean(self):
    data = forms.ModelForm.clean(self)
    city, province, region = data.get("municipality"), data.get("province"), data.get("region")
    if province and region and province.region_id != region.pk:
        self.add_error("province", "Provincia incompatible / Incompatible province")
    if city and province and city.province_id != province.pk:
        self.add_error("municipality", "Ciudad incompatible / Incompatible city")
    postal = data.get("postal_code")
    if postal and city:
        if not self.postal_matches(postal, city):
            self.add_error(
                "postal_code", "CP no corresponde a la ciudad / Postal code does not match city"
            )
        elif not postal.public_safe:
            self.add_error(
                "postal_code",
                "Precisión restringida por privacidad / Precision restricted for privacy",
            )
    if data.get("zone") and city and data["zone"].municipality_id != city.pk:
        self.add_error("zone", "Zona incompatible / Incompatible area")
    categories = data.get("categories")
    if categories is not None and any(
        service.category_id not in {cat.pk for cat in categories}
        for service in data.get("services", [])
    ):
        self.add_error(
            "services", "Servicio fuera de las categorías / Service outside selected categories"
        )
    for field in ["description", "description_alternative", "title"]:
        try:
            validate_listing_text(data.get(field, ""))
        except ValidationError as error:
            self.add_error(field, error)
    return data

@pytest.mark.parametrize("language", ["es", "en"])
def test_extracted_rules_match_pre_change_clean_with_native_conversion(request, monkeypatch, language):
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    revision = next(row.approved_revision for row in context.rows
                    if publicly_visible(row, context=context))
    data = {name: getattr(revision, name) for name in DetailsForm.Meta.fields
            if not revision._meta.get_field(name).many_to_many}
    data.update({name: [item.pk for item in getattr(revision, "_pv_" + name)]
                 for name in ["categories", "services", "travel_areas"]})
    city = revision.municipality
    data.update(region=city.province.region_id, province=city.province_id,
                municipality=city.pk, postal_code=revision.postal_code_id or "",
                zone=revision.zone_id or "")
    current = DetailsForm.clean
    with override(language):
        for changes in [{}, {"description": "  Valid synthetic description  "},
                        {"description": "www.invalid.example", "title": "@contact"},
                        {"description": ""}, {"description_alternative": "www.invalid.example"},
                        {"description": "x" * 6001}, {"days": ["9"]},
                        {"municipality": "missing"}, {"services": [99999999]},
                        {"spoken_languages": ["invalid"]}]:
            values = {**data, **changes}
            monkeypatch.setattr(DetailsForm, "clean", legacy_details_clean)
            old = DetailsForm(values, instance=copy(revision))
            old_valid = old.is_valid()
            monkeypatch.setattr(DetailsForm, "clean", current)
            new = DetailsForm(values, instance=copy(revision))
            assert new.is_valid() == old_valid
            assert new.errors.as_json() == old.errors.as_json()
            assert new.cleaned_data.keys() == old.cleaned_data.keys()
            for name, value in new.cleaned_data.items():
                previous = old.cleaned_data[name]
                if hasattr(value, "values_list"):
                    assert list(value.values_list("pk", flat=True)) == list(previous.values_list("pk", flat=True))
                else:
                    assert value == previous


def test_shared_value_rule_helper_is_fingerprinted(monkeypatch):
    assert projection.supported()
    monkeypatch.setattr(listing_forms, "validate_details_values", lambda data, **kwargs: data)
    assert not projection.supported()


def test_shared_field_clean_helper_is_fingerprinted(monkeypatch):
    from apps.listings import public_validation
    assert projection.supported()
    monkeypatch.setattr(public_validation, "memoize_publication_field_clean", lambda *args: None)
    assert not projection.supported()


@pytest.mark.parametrize("kind", ["details", "contacts"])
def test_value_model_fields_match_native_model_path(request, kind):
    from django.db import models
    from apps.listings.forms import ContactsForm
    from apps.listings.models import Revision
    from apps.listings.public_validation import (validate_publication_value_fields,
        validate_publication_input_fields, SnapshotDetails)
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    revision = next(row.approved_revision for row in context.rows
                    if publicly_visible(row, context=context))
    assert Revision.clean is models.Model.clean
    assert not Revision._meta.constraints and not Revision._meta.unique_together
    assert [field.name for field in Revision._meta.fields if field.unique] == ["id"]
    if kind == "details":
        data = {name: getattr(revision, name) for name in DetailsForm.Meta.fields
                if not revision._meta.get_field(name).many_to_many}
        data.update({name: [item.pk for item in getattr(revision, "_pv_" + name)]
                     for name in ["categories", "services", "travel_areas"]})
        city = revision.municipality
        data.update(region=city.province.region_id, province=city.province_id,
                    municipality=city.pk, postal_code=revision.postal_code_id or "",
                    zone=revision.zone_id or "")
        factory = lambda values: SnapshotDetails(context.catalog, values,
            instance=copy(revision), prepared_fields=context.details_fields)
        cases = [{}, {"description": ""}, {"description": "  Valid content  "},
                 {"title": "@contact", "description": "www.invalid.example"},
                 {"description": "x" * 6001}, {"spoken_languages": []},
                 {"days": ["9"]}, {"categories": [99999999]},
                 {"municipality": "missing"}, {"time_slot": "invalid"}]
    else:
        data = {"whatsapp": False, "telegram": "@Valid_name",
                "contact_exposure_accepted": True, "accept_publishing": True,
                "legal_version": "synthetic"}
        factory = lambda values: ContactsForm(values, instance=copy(revision))
        cases = [{}, {"telegram": "a"}, {"telegram": ""},
                 {"telegram": "@ Valid_name "}, {"telegram": "x" * 33},
                 {"contact_exposure_accepted": False}, {"whatsapp": "false"}]
    for changes in cases:
        native = factory({**data, **changes})
        actual = factory({**data, **changes})
        native_valid = native.is_valid()
        assert "id" in native._get_validation_exclusions()
        actual._clean_fields = lambda: validate_publication_input_fields(actual)
        actual._post_clean = lambda: validate_publication_value_fields(actual)
        assert actual.is_valid() == native_valid
        assert actual.errors.as_json() == native.errors.as_json()
        assert actual.cleaned_data.keys() == native.cleaned_data.keys()
        for name, value in actual.cleaned_data.items():
            previous = native.cleaned_data[name]
            if hasattr(value, "values_list"):
                assert list(value.values_list("pk", flat=True)) == list(previous.values_list("pk", flat=True))
            else:
                assert value == previous


def test_value_model_kernel_change_disables_projection(monkeypatch):
    from apps.listings import public_validation
    assert projection.supported()
    monkeypatch.setattr(public_validation, "validate_publication_value_fields", lambda form: None)
    assert not projection.supported()



def test_missing_default_input_retains_native_model_path(request, monkeypatch):
    from apps.listings import public_validation
    from apps.listings.forms import ContactsForm
    request.getfixturevalue("directory")
    context = PublicationContext(candidates({}))
    revision = next(row.approved_revision for row in context.rows
                    if publicly_visible(row, context=context))
    values = {"telegram": "@Valid_name", "contact_exposure_accepted": True,
              "accept_publishing": True, "legal_version": "synthetic"}
    prototype = ContactsForm(values, instance=copy(revision))
    def unexpected(form):
        raise AssertionError("Omitted model-default input must stay native")
    monkeypatch.setattr(public_validation, "validate_publication_value_fields", unexpected)
    assert public_validation.validate_publication_binding(
        prototype, values, copy(revision), value_model=True) == ContactsForm(
            values, instance=copy(revision)).is_valid()


def test_input_kernel_helper_is_fingerprinted(monkeypatch):
    from apps.listings import public_validation
    assert projection.supported()
    monkeypatch.setattr(public_validation, "validate_publication_input_fields", lambda form: None)
    assert not projection.supported()


def test_native_bound_field_rule_changes_disable_projection(monkeypatch):
    from functools import wraps
    original = forms.Field._clean_bound_field
    assert projection.supported()
    @wraps(original)
    def changed(self, bound_field):
        raise ValidationError("Synthetic additional bound-field rule")
    monkeypatch.setattr(forms.Field, "_clean_bound_field", changed)
    assert not projection.supported()
