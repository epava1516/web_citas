"""Coverage counts are exact only with committed unique foreign-key membership."""

import uuid

import pytest
from django.db import connection, transaction
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.discovery import candidates
from apps.listings.models import Listing, PublicationState

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('mutation,expected', [
    ('none', True), ('ineligible', True), ('missing', False), ('stale', False),
])
def test_committed_coverage_matches_original_join(request, mutation, expected):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    state = PublicationState.objects.first()
    assert state is not None
    if mutation == 'ineligible':
        PublicationState.objects.filter(pk=state.pk).update(eligible=False)
    elif mutation == 'missing':
        state.delete()
    elif mutation == 'stale':
        PublicationState.objects.filter(pk=state.pk).update(rules_version='older-rules')
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        assert publication_state.all_state_current() is expected
        assert publication_state.all_state_current(trusted_snapshot=True) is expected


def test_empty_committed_population_has_complete_coverage():
    assert not Listing.objects.exists()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        assert publication_state.all_state_current()
        assert publication_state.all_state_current(trusted_snapshot=True)


def test_deferred_orphan_cannot_cancel_missing_state_in_inherited_transaction(request, monkeypatch):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    original = publication_state.all_state_current
    observed = []

    def observe(*, trusted_snapshot=False):
        observed.append(trusted_snapshot)
        return original(trusted_snapshot=trusted_snapshot)

    monkeypatch.setattr(publication_state, 'all_state_current', observe)
    with transaction.atomic():
        initial = PublicationState.objects.count()
        PublicationState.objects.first().delete()
        PublicationState.objects.create(
            listing_id=uuid.uuid4(), eligible=True, revision=None,
            rules_version=publication_state.rules_version(), computed_at=timezone.now(),
        )
        assert PublicationState.objects.count() == initial == Listing.objects.count()
        assert original() is False
        # Document the counterexample to unqualified use of cardinality equality.
        assert original(trusted_snapshot=True) is True
        page = publication_state.state_page(candidates({}), 1)
        assert page is not None
        assert observed == [False]
        transaction.set_rollback(True)
