"""Native form initialization already captures the selected M2M input."""

import pytest
from django.db import connection
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.submissions import validate_submission

pytestmark = pytest.mark.django_db(transaction=True)


def test_native_validation_does_not_read_each_input_membership_twice(request, record_property):
    request.getfixturevalue('directory')
    assert connection.vendor == 'postgresql'
    person = Person.objects.get(individual__username='fixture-v1-individual')
    revision = person.listing.approved_revision
    tables = {name: 0 for name in ('listings_revision_categories',
                                  'listings_revision_services',
                                  'listings_revision_travel_areas')}

    def observe(execute, sql, values, many, context):
        if sql.lstrip().upper().startswith('SELECT'):
            for table in tables:
                if '"' + table + '"' in sql:
                    tables[table] += 1
        return execute(sql, values, many, context)

    with connection.execute_wrapper(observe):
        document = validate_submission(revision, person)
    assert document.slug == 'publishing'
    record_property('membership_read_counts', tables)
    assert tables == dict.fromkeys(tables, 1)


@pytest.mark.parametrize('relation', ['categories', 'services'])
def test_native_validation_still_observes_catalog_change_after_initialization(
    request, monkeypatch, relation,
):
    from django.core.exceptions import ValidationError

    from apps.listings.forms import DetailsForm

    request.getfixturevalue('directory')
    person = Person.objects.get(individual__username='fixture-v1-individual')
    revision = person.listing.approved_revision
    target = getattr(revision, relation).first()
    assert target is not None
    original = DetailsForm.__init__
    observed = []

    def initialize_then_revoke(self, *args, **kwargs):
        original(self, *args, **kwargs)
        assert target.pk in [item.pk for item in self.initial[relation]]
        type(target).objects.filter(pk=target.pk).update(active=False)
        observed.append(True)

    monkeypatch.setattr(DetailsForm, '__init__', initialize_then_revoke)
    with pytest.raises(ValidationError, match='Correct details and location'):
        validate_submission(revision, person)
    assert observed == [True]
