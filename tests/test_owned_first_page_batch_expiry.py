"""Controlled wall-clock advance after selection must retain the native guard."""
from datetime import timedelta

import pytest
from django.utils import timezone
from owned_first_page_batch import build_first_page_batch_prototype
from owned_state_page_before_batch import build_native_reference
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('victim_kind', ['pending', 'clean'])
def test_expiry_after_selection_keeps_guard_and_fallback(request, monkeypatch, victim_kind):
    client = request.getfixturevalue('directory')
    dataset = populate(80)
    pending, clean = dataset['sample_ids'][1:3]
    now = timezone.now()
    victim = pending if victim_kind == 'pending' else clean
    Listing.objects.filter(pk=victim).update(
        published_at=now + timedelta(days=1), expires_at=now + timedelta(seconds=1),
    )
    clock = [now]
    monkeypatch.setattr(timezone, 'now', lambda: clock[0])
    native = build_native_reference()
    counts = dict(batch_contexts=0, batch_sizes=[], page_reuses=0, missing_selected_fallbacks=0)
    proposed = build_first_page_batch_prototype(counts)
    native_guard = native.__globals__['publicly_visible']
    responses, terminal_marks = [], []
    for implementation in [native, proposed, publication_state._state_page]:
        clock[0] = now
        publication_state.refresh_all()
        assert not PublicationDirty.objects.exists()
        publication_state.mark([pending])
        calls = []

        def guard(row, **kwargs):
            if str(row.pk) == str(victim):
                calls.append(row.pk)
                if len(calls) == (2 if victim_kind == 'pending' else 1):
                    clock[0] = now + timedelta(seconds=2)
            return native_guard(row, **kwargs)

        with monkeypatch.context() as patch:
            patch.setitem(implementation.__globals__, 'publicly_visible', guard)
            patch.setattr(publication_state, '_state_page', implementation)
            response = client.get('/es/')
        assert response.status_code == 200
        assert clock[0] > now + timedelta(seconds=1)
        assert str(victim) not in {str(row.pk) for row in response.context['page']}
        assert response.wsgi_request._publication_route['reason'] == 'state_page_guard_changed'
        terminal_marks.append({str(pk) for pk in PublicationDirty.objects.values_list('pk', flat=True)})
        responses.append(response)
    assert responses[0].content == responses[1].content == responses[2].content
    assert all(marks == {str(pending), str(victim)} for marks in terminal_marks)
    assert counts['batch_contexts'] == counts['page_reuses'] == 1
