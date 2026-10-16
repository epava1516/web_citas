"""A complete census narrows dirty reads only inside the owned RR snapshot."""
from contextlib import nullcontext

import pytest
from django.db import transaction
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_publication_state import assert_equivalent

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationState

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('boundary', ['current', 'missing', 'old_version', 'inherited'])
def test_dirty_census_keeps_native_page_and_inherited_read_semantics(request, monkeypatch, boundary):
    client = request.getfixturevalue('directory')
    publication_state.refresh_all()
    target = Listing.objects.filter(status='published').first()
    publication_state.mark([target.pk])
    if boundary == 'missing':
        PublicationState.objects.filter(listing_id=target.pk).delete()
    elif boundary == 'old_version':
        PublicationState.objects.filter(listing_id=target.pk).update(rules_version='0'*64)
    census = publication_state.all_state_current
    calls = []

    def observed(*, trusted_snapshot=False):
        calls.append(trusted_snapshot)
        return census(trusted_snapshot=trusted_snapshot)

    monkeypatch.setattr(publication_state, 'all_state_current', observed)
    with transaction.atomic() if boundary == 'inherited' else nullcontext():
        assert_equivalent(client, monkeypatch)
    if boundary == 'inherited':
        assert calls == []
    else:
        assert calls and all(calls)


@pytest.mark.parametrize('count', [48, 49])
def test_complete_dirty_census_keeps_native_unknown_limit(request, monkeypatch, settings, count):
    from apps.listings.discovery import candidates
    from apps.listings.models import PublicationDirty
    from scripts.synthetic_load_dataset import populate

    request.getfixturevalue('directory')
    monkeypatch.setattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False)
    populate(100)
    publication_state.refresh_all()
    ids = list(Listing.objects.filter(status='published').order_by('pk').values_list('pk', flat=True)[:count])
    assert len(ids) == count
    publication_state.mark(ids)
    assert PublicationDirty.objects.count() == count
    observation = {}
    page = publication_state.state_page(candidates({}), 1, observation=observation)
    if count == 48:
        assert page is not None
        assert observation['native_unknown'] == 48
    else:
        assert page is None
        assert observation['reason'] == 'state_unknown_over_limit'
