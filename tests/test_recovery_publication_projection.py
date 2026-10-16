"""Recovery reapplies selected erasure to restored publication text copies."""
import pytest
from test_erasure_execution import PURPOSES, payload, plan_fixture
from test_recovery_apply import stored_receipt
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings import publication_state, tasks
from apps.listings.models import PublicationState
from apps.safety.crypto import unseal
from apps.safety.erasure_execution import execute
from apps.safety.models import RecoveryOutbox
from apps.safety.recovery_apply import reconcile

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('erase_publication', [True, False])
def test_recovery_clears_only_selected_restored_publication_without_refresher(
    request, settings, monkeypatch, tmp_path, erase_publication,
):
    request.getfixturevalue('directory')
    publication_state.refresh_all()
    monkeypatch.setattr(tasks.refresh_publication_state, 'delay', lambda: None)
    selected = ['profile', 'publication'] if erase_publication else PURPOSES
    case, actor, _, _, _, person, plan, _, _, _ = plan_fixture(
        request, settings, monkeypatch, selected_purposes=selected,
    )
    listing = person.listing
    restored = PublicationState.objects.filter(listing_id=listing.pk).values().get()
    assert restored['search_document'] and restored['expires_at']
    execution = execute(actor, case.pk, plan.pk, **(payload(case) | {'purposes': selected}))
    event = unseal(RecoveryOutbox.objects.get(execution=execution).encrypted_event)
    PublicationState.objects.update_or_create(
        listing_id=listing.pk,
        defaults={k:v for k,v in restored.items() if k != 'listing_id'},
    )
    peers = list(PublicationState.objects.exclude(listing_id=listing.pk).order_by('listing_id').values())
    store, start = stored_receipt(tmp_path, event)
    settings.RECOVERY_MODE = True
    assert reconcile(store, start)['applied'] == 1
    assert list(PublicationState.objects.exclude(listing_id=listing.pk).order_by('listing_id').values()) == peers
    remaining = list(PublicationState.objects.filter(listing_id=listing.pk).values())
    if erase_publication:
        assert all(not row['search_document'] and row['published_at'] is None
                   and row['expires_at'] is None for row in remaining)
    else:
        assert remaining == [restored]
    assert reconcile(store, start)['applied'] == 0
