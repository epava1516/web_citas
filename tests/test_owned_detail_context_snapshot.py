"""A native-detail context must not combine mutually ineligible committed states."""
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.db import connection, connections, transaction
from django.db.models import Q
from owned_detail_context import build_detail_context_prototype, patch_detail_view
from owned_detail_native_reference import build_native_detail_reference
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import RepresentationAction
from apps.listings.models import Listing
from apps.mediafiles.models import Match, Photo
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('policy', ['legacy_rc_negative_control', 'trusted_rr'])
@pytest.mark.parametrize('scenario', ['conflict_photo', 'grant_acceptance'])
def test_detail_snapshot_transition(request, monkeypatch, record_property, policy, scenario):
    client = request.getfixturevalue('directory')
    data = populate(80)
    listing = Listing.objects.get(pk=data['sample_ids'][1])
    peer = Listing.objects.get(pk=data['sample_ids'][2])
    photo = Photo.objects.get(revision_id=listing.approved_revision_id, removed_at__isnull=True)
    counterpart = Photo.objects.get(revision_id=peer.approved_revision_id, removed_at__isnull=True)
    assert not Match.objects.filter(Q(photo=photo) | Q(candidate=photo), decision='conflict').exists()
    revision = listing.approved_revision
    grant_ids = list(RepresentationAction.objects.filter(
        person_id=listing.person_id, action='grant', document__slug='publishing',
        document__version=revision.publisher_acceptance.document.version,
    ).values_list('pk', flat=True))
    assert grant_ids
    if scenario == 'conflict_photo':
        Photo.objects.filter(pk=photo.pk).update(comparison_complete=False)
    else:
        type(revision.publisher_acceptance).objects.filter(
            pk=revision.publisher_acceptance_id).update(action='inspect')
    path = f'/es/listing/{listing.pk}/'
    # State A is ineligible because comparison is pending.
    native=build_native_detail_reference()
    with monkeypatch.context() as patch:
        patch_detail_view(patch,native)
        before = client.get(path)
    assert before.status_code == 404
    committed = []

    def writer():
        try:
            with transaction.atomic():
                if scenario == 'conflict_photo':
                    Photo.objects.filter(pk=photo.pk).update(comparison_complete=True)
                    result = Match.objects.create(photo_id=photo.pk, candidate_id=counterpart.pk,
                                                  method='phash', decision='conflict').pk
                else:
                    type(revision.publisher_acceptance).objects.filter(
                        pk=revision.publisher_acceptance_id).update(action='publish')
                    result = RepresentationAction.objects.filter(pk__in=grant_ids).update(action='revoke')
            return result
        finally:
            connections.close_all()

    def transition(execute, sql, params, many, context):
        result = execute(sql, params, many, context)
        if not committed and '_pv_conflict' in str(sql) and 'listings_listing' in str(sql):
            # Main SELECT completed in A; prefetches will read committed state B.
            with ThreadPoolExecutor(max_workers=1) as pool:
                committed.append(pool.submit(writer).result(timeout=15))
        return result

    proposed = build_detail_context_prototype(trusted_snapshot=policy == 'trusted_rr')
    with monkeypatch.context() as patch:
        patch_detail_view(patch, proposed)
        with connection.execute_wrapper(transition):
            candidate = client.get(path)
    assert len(committed) == 1
    if scenario == 'conflict_photo':
        assert Photo.objects.get(pk=photo.pk).comparison_complete
        assert Match.objects.get(pk=committed[0]).decision == 'conflict'
    else:
        assert committed[0] == len(grant_ids)
        assert not RepresentationAction.objects.filter(pk__in=grant_ids, action='grant').exists()
    # State B is ineligible because the conflict was committed atomically.
    with monkeypatch.context() as patch:
        patch_detail_view(patch,native)
        after = client.get(path)
    assert after.status_code == 404
    record_property('detail_snapshot_transition', dict(native_A=before.status_code,
                    native_B=after.status_code, candidate=candidate.status_code,
                    atomic_writer_committed=True, scenario=scenario, policy=policy))
    assert candidate.status_code == (404 if policy == 'trusted_rr' else 200)
