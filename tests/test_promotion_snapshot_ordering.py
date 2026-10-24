"""Snapshot ownership, fresh next-request rights and positive checked filters."""

from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import close_old_connections, connection, connections, transaction
from django.test import Client
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_exposure import purchased

from apps.catalog import promotion_paging
from apps.core.models import PhoneClaim, User
from apps.listings import publication_state
from apps.listings.models import PublicationDirty

pytestmark = pytest.mark.django_db(transaction=True)


def sponsorship(response, listing):
    assert response.status_code == 200
    return {c['listing'].pk:c['sponsorship'] for c in response.context['cards']}.get(listing.pk)


def test_inherited_read_committed_does_not_reuse_a_rights_map(request, settings, monkeypatch):
    _, listing, _ = purchased(request, settings)
    publication_state.refresh_all()

    def forbidden(*args, **kwargs):
        raise AssertionError('An inherited READ COMMITTED transaction cannot reuse authority across statements')

    monkeypatch.setattr(promotion_paging, '_snapshot_order_population', forbidden)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute('SHOW transaction_isolation')
            assert cursor.fetchone()[0] == 'read committed'
        response = Client().get('/es/')
        assert sponsorship(response, listing) == 'premium'
        assert response.wsgi_request._publication_route['route'] == 'state'


def test_snapshot_map_does_not_survive_next_request(request, settings, monkeypatch, record_property):
    buyer, listing, _ = purchased(request, settings)
    publication_state.refresh_all()
    original = promotion_paging._snapshot_order_population
    observed = []

    def revoke():
        close_old_connections()
        try:
            User.objects.filter(pk=buyer.pk).update(is_active=False)
        finally:
            connections.close_all()

    def snapshot(*args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute('SHOW transaction_isolation')
            observed.append(cursor.fetchone()[0])
        assert observed[-1] == 'repeatable read'
        query = original(*args, **kwargs)
        if len(observed) == 1:
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(revoke).result(timeout=10)
        return query

    monkeypatch.setattr(promotion_paging, '_snapshot_order_population', snapshot)
    assert sponsorship(Client().get('/es/'), listing) == 'premium'
    assert sponsorship(Client().get('/es/'), listing) is None
    assert observed == ['repeatable read', 'repeatable read']
    record_property('commercial_snapshot_boundary', 'Concurrent buyer revocation after map read; first response retains its read snapshot, next request denies sponsorship; no persistent result cache')


@pytest.mark.parametrize('language', ['es', 'en'])
def test_positive_checked_filter_with_promotions_and_delayed_refresh(request, settings, monkeypatch, language, record_property):
    _, listing, _ = purchased(request, settings)
    phone_id = listing.person.phone_claim_id
    # Synthetic records exercise the existing procedure rule; no SMS/provider is contacted.
    PhoneClaim.objects.filter(pk=phone_id).update(verified_at=timezone.now(), verification_procedure='sms-v1')
    publication_state.refresh_all()
    client = Client()
    response = client.get(f'/{language}/', {'checked':['contact']})
    assert sponsorship(response, listing) == 'premium'
    assert response.context['page'].paginator.count == 1
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, 'state_page', lambda *args, **kwargs: None)
        native = client.get(f'/{language}/', {'checked':['contact']})
    assert native.content == response.content
    PhoneClaim.objects.filter(pk=phone_id).update(verification_procedure='simulator-v1')
    assert PublicationDirty.objects.filter(listing_id=listing.pk).exists()
    response = client.get(f'/{language}/', {'checked':['contact']})
    assert sponsorship(response, listing) is None and response.context['page'].paginator.count == 0
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, 'state_page', lambda *args, **kwargs: None)
        native = client.get(f'/{language}/', {'checked':['contact']})
    assert native.content == response.content
    record_property('synthetic_contact_rule_only', True)
