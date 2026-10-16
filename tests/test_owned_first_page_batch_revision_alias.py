"""Regression: a rejected foreign approved revision must not poison its owner."""
from datetime import timedelta

import pytest
from django.utils import timezone
from owned_first_page_batch import build_first_page_batch_prototype
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation, publication_state
from apps.listings.models import Listing, PublicationDirty
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize('hydration_order', ['pk', '-pk'])
def test_foreign_revision_pending_row_preserves_clean_owner(request, monkeypatch, hydration_order):
    if not any(str(x).split('::')[0] == 'tests/test_owned_first_page_batch_revision_alias.py'
               for x in request.config.args):
        pytest.skip('Explicit own foreign-revision alias regression only')
    client = request.getfixturevalue('directory')
    dataset = populate(80)
    # Both are cloned synthetic rows with no copied Match edges.
    ids = sorted(dataset['sample_ids'][1:])
    owner = Listing.objects.select_related('approved_revision').get(pk=ids[0])
    rejected = Listing.objects.get(pk=ids[-1])
    Listing.objects.filter(pk=owner.pk).update(published_at=timezone.now() + timedelta(days=1))
    publication_state.refresh_all()
    assert not PublicationDirty.objects.exists()
    Listing.objects.filter(pk=rejected.pk).update(approved_revision_id=owner.approved_revision_id)
    assert set(PublicationDirty.objects.values_list('pk', flat=True)) == {rejected.pk}
    assert not PublicationDirty.objects.filter(pk=owner.pk).exists()
    counts = dict(batch_contexts=0, batch_sizes=[], page_reuses=0, missing_selected_fallbacks=0)
    proposed = build_first_page_batch_prototype(counts)
    original_query = public_validation.publication_query

    def deterministic_hydration(query, document):
        # Enforce one ordering permitted by the otherwise unordered hydration.
        # It affects both arms equally; candidate population/page ordering stays native.
        return original_query(query, document).order_by(hydration_order)

    monkeypatch.setattr(public_validation, 'publication_query', deterministic_hydration)
    context = public_validation.PublicationContext(
        Listing.objects.filter(pk__in=[owner.pk, rejected.pk]), page_read=True,
    )
    rows = {row.pk: row for row in context.rows}
    assert context.row(rows[owner.pk].approved_revision) is rows[owner.pk]
    with pytest.raises(ValueError, match='own current revision instance'):
        context.row(rows[rejected.pk].approved_revision)
    with pytest.raises(ValueError, match='own current revision instance'):
        context.row(owner.approved_revision)
    reference = client.get('/es/')
    assert reference.status_code == 200
    assert owner.pk in {row.pk for row in reference.context['page']}
    assert rejected.pk not in {row.pk for row in reference.context['page']}
    with monkeypatch.context() as patch:
        patch.setattr(publication_state, '_state_page', proposed)
        candidate = client.get('/es/')
    assert candidate.status_code == reference.status_code == 200
    assert candidate.content == reference.content
    assert counts['batch_contexts'] == counts['page_reuses'] == 1
    assert set(PublicationDirty.objects.values_list('pk', flat=True)) == {rejected.pk}
