"""A foreign approved-revision FK cannot replace the context's actual owner."""
import pytest
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import public_validation
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize('ordering', ['pk', '-pk'])
def test_context_revision_index_preserves_ownership(request, monkeypatch, ordering):
    request.getfixturevalue("directory")
    owner, foreign = list(
        Listing.objects.filter(status='published').select_related('approved_revision').order_by('pk')[:2]
    )
    Listing.objects.filter(pk=foreign.pk).update(approved_revision_id=owner.approved_revision_id)
    original = public_validation.publication_query
    monkeypatch.setattr(
        public_validation, 'publication_query',
        lambda query, document: original(query, document).order_by(ordering),
    )
    context = public_validation.PublicationContext(
        Listing.objects.filter(pk__in=[owner.pk, foreign.pk]), page_read=True,
    )
    rows = {row.pk: row for row in context.rows}
    assert context.row(rows[owner.pk].approved_revision) is rows[owner.pk]
    assert publicly_visible(rows[owner.pk], context=context)
    assert not publicly_visible(rows[foreign.pk], context=context)
    for revision in [rows[foreign.pk].approved_revision, owner.approved_revision]:
        with pytest.raises(ValueError, match='own current revision instance'):
            context.row(revision)
    foreign_context = public_validation.PublicationContext(
        Listing.objects.filter(pk=foreign.pk), page_read=True,
    )
    with pytest.raises(ValueError, match='own current revision instance'):
        foreign_context.row(foreign_context.rows[0].approved_revision)
