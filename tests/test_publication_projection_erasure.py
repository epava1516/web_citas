"""New publication copies respect synchronous scoped erasure without a worker."""

import pytest
from django.urls import reverse
from test_erasure_execution import PURPOSES, payload, plan_fixture
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings import publication_state, tasks
from apps.listings.models import PublicationState

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('erase_publication', [True, False])
def test_projection_erasure_matches_selected_purpose_when_refresher_is_unavailable(
    request, settings, monkeypatch, erase_publication,
):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    queued = []
    # Keep actual PG triggers/domain/HTTP. Only task execution is intentionally
    # unavailable: committing erasure cannot rely on worker progress.
    monkeypatch.setattr(tasks.refresh_publication_state, 'delay', lambda: queued.append(True))
    selected = ['profile', 'publication'] if erase_publication else PURPOSES
    case, _, staff, client, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=selected,
    )
    listing = person.listing
    original = PublicationState.objects.get(pk=listing.pk)
    assert original.search_document and original.expires_at
    peers = list(PublicationState.objects.exclude(pk=listing.pk).order_by('pk').values())
    path = reverse('erasure_execute', kwargs={'case_id': case.pk, 'plan_id': plan.pk})
    submitted = payload(case) | {'purposes': selected}
    assert staff.post(path, submitted).status_code == 200
    assert staff.post(path, submitted).status_code == 200
    assert list(PublicationState.objects.exclude(pk=listing.pk).order_by('pk').values()) == peers
    if erase_publication:
        remaining = list(PublicationState.objects.filter(pk=listing.pk).values(
            'search_document', 'expires_at', 'published_at',
        ))
        assert all(not row['search_document'] and row['expires_at'] is None
                   and row['published_at'] is None for row in remaining), (
                       'Publication text/date copy must not survive selected erasure awaiting a worker'
                   )
        assert queued
        assert client.get(f'/en/listing/{listing.pk}/').status_code == 404
        publication_state.refresh_all()
        recreated = PublicationState.objects.get(pk=listing.pk)
        assert not recreated.eligible and recreated.revision_id is None
        assert recreated.search_document is recreated.expires_at is recreated.published_at is None
    else:
        retained = PublicationState.objects.get(pk=listing.pk)
        assert retained.search_document == original.search_document
        assert retained.expires_at == original.expires_at
        assert retained.published_at == original.published_at
