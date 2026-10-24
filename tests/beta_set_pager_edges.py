"""Boundary parity for the isolated set pager; no product implementation changes."""

from datetime import timedelta

import pytest
from beta_set_pager_diagnostic import ORIGINAL, SetPager, candidate
from django.test import Client
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_exposure import purchased

from apps.catalog import promotion_paging
from apps.catalog.promotion_exposure import ranked
from apps.catalog.promotion_order_models import PromotionEntitlement
from apps.listings import publication_state
from apps.listings.models import Listing

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('state', ['none', 'future', 'starts_now', 'ends_now', 'suspended', 'active'])
@pytest.mark.parametrize('search', [False, True])
def test_temporal_and_empty_rights(request, settings, monkeypatch, record_property, state, search):
    _, listing, entitlement = purchased(request, settings)
    instant = timezone.now()
    if state == 'none':
        PromotionEntitlement.objects.filter(pk=entitlement.pk).delete()
    else:
        starts = instant if state == 'starts_now' else instant - timedelta(hours=1)
        ends = instant if state == 'ends_now' else instant + timedelta(hours=1)
        if state == 'future':
            starts, ends = instant + timedelta(hours=1), instant + timedelta(hours=2)
        PromotionEntitlement.objects.filter(pk=entitlement.pk).update(
            starts_at=starts, ends_at=ends,
            suspended_at=instant if state == 'suspended' else None,
        )
    publication_state.refresh_all()
    expected = state in {'starts_now', 'active'}
    assert bool(ranked([listing], text_search=search, now=instant)[1]) == expected
    monkeypatch.setattr(promotion_paging.timezone, 'now', lambda: instant)
    path = '/en/?q=photography' if search else '/es/'
    client = Client()
    baseline = client.get(path)
    assert baseline.status_code == 200
    selected = []

    def bound(*args, **kwargs):
        result = candidate(*args, **kwargs)
        assert isinstance(result, SetPager)
        selected.append(True)
        return result

    monkeypatch.setattr(promotion_paging, '_snapshot_order_population', bound)
    response = client.get(path)
    assert selected == [True]
    assert response.status_code == 200 and response['Cache-Control'] == 'no-store'
    assert response.wsgi_request._publication_route['route'] == 'state'
    assert response.content == baseline.content
    assert response.context['page'].paginator.count == baseline.context['page'].paginator.count
    assert [row.pk for row in response.context['page'].object_list] == [
        row.pk for row in baseline.context['page'].object_list
    ]
    cards = {c['listing'].pk: c['sponsorship'] for c in response.context['cards']}
    assert listing.pk in cards and bool(cards[listing.pk]) == expected
    record_property('set_pager_boundary', state)
    record_property('set_pager_used', True)
    record_property('native_and_http_parity', True)


@pytest.mark.parametrize('shape', ['distinct', 'unknown_order', 'sliced'])
def test_unknown_shapes_preserve_original_behavior(request, settings, record_property, shape):
    purchased(request, settings)
    query = Listing.objects.order_by('-published_at', 'pk')
    if shape == 'distinct':
        query = query.distinct()
    elif shape == 'unknown_order':
        query = query.order_by('pk')
    else:
        query = query[:1]
    now = timezone.now()
    if shape == 'sliced':
        # Existing implementation rejects this shape. Preserve that behavior;
        # fallback is not a claim of adding supported sliced populations.
        for function in (ORIGINAL, candidate):
            with pytest.raises(TypeError, match='Cannot reorder a query once a slice has been taken'):
                function(query, 'pk', now=now)
    else:
        actual = candidate(query, 'pk', now=now)
        assert not isinstance(actual, SetPager)
        assert list(actual.values_list('pk', '_promotion_priority')) == list(
            ORIGINAL(query, 'pk', now=now).values_list('pk', '_promotion_priority')
        )
    record_property('original_shape_behavior_preserved', shape)
    record_property('set_pager_used', False)
