"""Fresh batched publication checks must match the existing guard exactly."""

import pytest
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.discovery import candidates
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext

pytestmark = pytest.mark.django_db(transaction=True)


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
