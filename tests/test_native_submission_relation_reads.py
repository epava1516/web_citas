"""Native validation reads current profile membership after form initialization."""

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Service
from apps.core.models import Person
from apps.listings.submissions import validate_submission

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_validation_does_not_read_each_input_membership_twice(request, record_property):
    request.getfixturevalue("directory")
    assert connection.vendor == "postgresql"
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    tables = {
        name: 0
        for name in (
            "listings_revision_categories",
            "listings_revision_services",
            "listings_revision_travel_areas",
        )
    }

    def observe(execute, sql, values, many, context):
        if sql.lstrip().upper().startswith("SELECT"):
            for table in tables:
                if '"' + table + '"' in sql:
                    tables[table] += 1
        return execute(sql, values, many, context)

    with connection.execute_wrapper(observe):
        document = validate_submission(revision, person)
    assert document.slug == "publishing"
    record_property("membership_read_counts", tables)
    assert tables == dict.fromkeys(tables, 1)


@pytest.mark.parametrize("relation", ["categories", "services"])
def test_native_validation_still_observes_catalog_change_after_initialization(
    request,
    monkeypatch,
    relation,
):
    from django.core.exceptions import ValidationError

    from apps.listings.forms import DetailsForm

    request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    target = revision.categories.get()
    forbidden_service = (
        Service.objects.create(
            slug="forbidden-mid-validation",
            category=target,
            name_es="Sintético privado",
            name_en="Private synthetic",
        )
        if relation == "services"
        else None
    )
    original = DetailsForm.__init__
    observed = []

    def initialize_then_revoke(self, *args, **kwargs):
        original(self, *args, **kwargs)
        # A membership write may construct another form during state refresh.
        # Mutate exactly the native call under test, never that nested reader.
        if self.instance is not revision:
            return
        assert "categories" not in self.fields and "services" not in self.fields
        if relation == "categories":
            type(target).objects.filter(pk=target.pk).update(active=False)
        else:
            revision.services.add(forbidden_service)
        observed.append(True)

    monkeypatch.setattr(DetailsForm, "__init__", initialize_then_revoke)
    message = "Invalid profile catalogue" if relation == "categories" else "Services and rates"
    with pytest.raises(ValidationError, match=message):
        validate_submission(revision, person)
    assert observed == [True]
