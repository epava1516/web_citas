"""Directed ordering and off-page relation controls; not a latency benchmark."""
from datetime import timedelta

import pytest
from django.utils import timezone
from owned_first_page_batch import build_first_page_batch_prototype
from owned_state_page_before_batch import build_native_reference
from test_discovery import directory  # noqa: F401
from test_owned_first_page_batch_edges import pair
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Municipality
from apps.listings import public_validation, publication_state
from apps.listings.models import Listing, PublicationDirty, Revision
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def ordered_case(request):
    client = request.getfixturevalue('directory')
    populate(80)
    ids = list(Listing.objects.filter(status='published').order_by('pk').values_list('pk', flat=True))
    assert len(ids) >= 60
    now = timezone.now()
    Listing.objects.filter(pk__in=ids).update(published_at=now)
    Revision.objects.filter(listing_id__in=ids).update(title='Synthetic boundaryneedle')
    return client, ids, now


@pytest.mark.parametrize('scenario', ['date_ties', 'rank_ties', 'clean_null'])
def test_clean_prefix_boundary_order(ordered_case, monkeypatch, record_property, scenario):
    client, ids, _ = ordered_case
    if scenario == 'clean_null':
        Listing.objects.filter(pk__in=[ids[25], ids[26]]).update(published_at=None)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    # Dirty rows straddle the page boundary and the clean prefix's boundary.
    publication_state.mark([ids[0], ids[23], ids[24], ids[47]])
    marks = list(PublicationDirty.objects.order_by('pk').values_list('pk', 'generation'))
    counts = dict(batch_contexts=0, batch_sizes=[], page_reuses=0, missing_selected_fallbacks=0)
    proposed = build_first_page_batch_prototype(counts)
    params = {'q': 'boundaryneedle'} if scenario == 'rank_ties' else {}
    _, candidate = pair(client, build_native_reference(), proposed, monkeypatch, params)
    selected = [row.pk for row in candidate.context['page']]
    expected = ([ids[25], ids[26]] + [pk for pk in ids if pk not in ids[25:27]])[:24] \
        if scenario == 'clean_null' else ids[:24]
    assert selected == expected
    assert counts['batch_contexts'] == counts['page_reuses'] == 1
    assert counts['missing_selected_fallbacks'] == 0
    # Also execute the uninstrumented product entrypoint under normal collection.
    actual = client.get('/es/', params)
    assert actual.status_code == 200
    assert actual.content == candidate.content
    assert list(PublicationDirty.objects.order_by('pk').values_list('pk', 'generation')) == marks
    record_property('directed_order', dict(scenario=scenario, selected=[str(pk) for pk in selected], counters=counts))


def test_offpage_clean_fanout_is_observed(ordered_case, monkeypatch, record_property):
    client, ids, now = ordered_case
    pending, victim = ids[:24], ids[24]
    Listing.objects.filter(pk__in=pending).update(published_at=now + timedelta(days=2))
    Listing.objects.filter(pk=victim).update(published_at=now + timedelta(days=1))
    revision = Revision.objects.get(pk=Listing.objects.get(pk=victim).approved_revision_id)
    city = Municipality.objects.first()
    cities = Municipality.objects.bulk_create([
        Municipality(code=f'owned-fanout-{n}', name=f'Synthetic fanout {n}',
                     province_id=city.province_id, source_id=city.source_id)
        for n in range(128)
    ])
    revision.travel_areas.add(*cities)
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    publication_state.mark(pending)
    counts = dict(batch_contexts=0, batch_sizes=[], page_reuses=0, missing_selected_fallbacks=0)
    proposed = build_first_page_batch_prototype(counts)
    original = public_validation.PublicationContext.__init__
    observations = []

    def observed(context, *args, **kwargs):
        original(context, *args, **kwargs)
        observations.append({
            'parents': len(context.rows),
            'victim_children': sum(len(row.approved_revision._pv_travel_areas)
                                   for row in context.rows if row.pk == victim),
        })

    monkeypatch.setattr(public_validation.PublicationContext, '__init__', observed)
    _, candidate = pair(client, build_native_reference(), proposed, monkeypatch)
    assert {row.pk for row in candidate.context['page']} == set(pending)
    assert counts['batch_contexts'] == counts['page_reuses'] == 1
    # Native has separate pending/page contexts; the batch adds off-page parents.
    assert len(observations) == 3
    assert all(item['victim_children'] == 0 for item in observations[:2])
    assert observations[2]['parents'] == 48
    assert observations[2]['victim_children'] >= 128
    record_property('offpage_fanout', dict(contexts=observations, counters=counts,
                                         scope='Materialized rows only; no latency or memory claim'))
