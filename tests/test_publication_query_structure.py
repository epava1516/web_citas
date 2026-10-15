"""Reused expression templates must preserve fresh authority and query isolation."""
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from django.db.models import Exists, Value
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import LegalDocument, Person
from apps.listings import public_validation
from apps.listings.discovery import candidates
from apps.listings.models import Listing
from apps.listings.moderation import publicly_visible
from apps.listings.submissions import current_publishing_document

pytestmark = pytest.mark.django_db(transaction=True)


def test_reused_structure_keeps_authority_fresh_after_revocation_and_document_rotation(request):
    request.getfixturevalue('directory')
    public_validation._publication_annotations.cache_clear()

    def decisions():
        context = public_validation.PublicationContext(candidates({}))
        return {row.pk: publicly_visible(row, context=context) for row in context.rows}

    before = decisions()
    listing = Listing.objects.filter(pk__in=[pk for pk, visible in before.items() if visible]).first()
    assert listing is not None
    # Warm the template, then change data without replacing the process/template.
    assert decisions() == before
    Person.objects.filter(pk=listing.person_id).update(consent_revoked_at=timezone.now())
    assert decisions()[listing.pk] is False
    Person.objects.filter(pk=listing.person_id).update(consent_revoked_at=None)
    assert decisions() == before
    document = current_publishing_document()
    previous_documents = list(LegalDocument.objects.filter(slug='publishing', active=True).values_list('pk', flat=True))
    LegalDocument.objects.filter(pk__in=previous_documents).update(active=False)
    LegalDocument.objects.create(slug='publishing', version=document.version + '-structure-proof',
                                 language=document.language,
                                 title='Synthetic new publishing terms', body='Synthetic terms',
                                 active=True, published_at=timezone.now())
    assert not any(decisions().values())
    LegalDocument.objects.filter(version=document.version + '-structure-proof').update(active=False)
    LegalDocument.objects.filter(pk__in=previous_documents).update(active=True)
    assert decisions() == before
    assert public_validation._publication_annotations.cache_info().hits > 0


def test_expression_templates_are_isolated_across_query_shapes_and_concurrent_resolution(request):
    request.getfixturevalue('directory')
    document = current_publishing_document()
    query = public_validation.publication_query(Listing.objects.all(), document)
    expected = query.query.sql_with_params()
    annotations = public_validation._publication_annotations(document.version)
    assert isinstance(annotations['_pv_grant'], Exists)
    assert annotations['_pv_grant'] is not query.query.annotations['_pv_grant']
    assert annotations['_pv_grant'].query is not query.query.annotations['_pv_grant'].query
    query.query.annotations['_pv_grant'] = Value(False)

    def compile_shape(index):
        # Compilation resolves structure only; no DB access from these threads.
        version = document if index % 2 else SimpleNamespace(version='synthetic-other-version')
        candidate = (Listing.objects.filter(status='paused') if index % 3 else Listing.objects.all())
        return public_validation.publication_query(candidate, version).query.sql_with_params()

    sequential = [compile_shape(i) for i in range(12)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(compile_shape, range(12))) == sequential
    assert public_validation.publication_query(Listing.objects.all(), document).query.sql_with_params() == expected
    for index in range(12):
        public_validation.publication_query(Listing.objects.all(), SimpleNamespace(version=str(index)))
    assert public_validation._publication_annotations.cache_info().currsize <= 8
