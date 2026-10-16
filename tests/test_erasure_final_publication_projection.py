"""Final erasure outcomes must account for copied publication text and dates."""
from uuid import uuid4

import pytest
from test_erasure_execution import REASON, plan_fixture
from test_erasure_final import material
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings import publication_state, tasks
from apps.listings.models import PublicationState
from apps.safety.erasure_execution import execute

pytestmark = pytest.mark.django_db(transaction=True)


def test_final_material_marks_restored_publication_projection_pending(request, settings, monkeypatch):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    monkeypatch.setattr(tasks.refresh_publication_state, 'delay', lambda: None)
    selected = ['profile', 'publication']
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=selected,
    )
    listing = person.listing
    original = PublicationState.objects.filter(listing_id=listing.pk).values().get()
    execution = execute(actor, case.pk, plan.pk, uuid4(), case.version, selected, REASON, True)
    case.refresh_from_db()
    assert 'publication' in material(case, execution)['completed_purposes']
    publication_state.refresh_all()
    clean = PublicationState.objects.filter(listing_id=listing.pk).values().get()
    assert 'publication' in material(case, execution)['completed_purposes']
    PublicationState.objects.filter(listing_id=listing.pk).update(
        **{k:v for k,v in original.items() if k != 'listing_id'},
    )
    observed = material(case, execution)
    assert 'publication' in observed['pending_execution_purposes']
    assert 'publication' not in observed['completed_purposes']
    PublicationState.objects.filter(listing_id=listing.pk).update(
        **{k:v for k,v in clean.items() if k != 'listing_id'},
    )
    assert 'publication' in material(case, execution)['completed_purposes']
