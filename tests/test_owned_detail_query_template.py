"""Explicit parity and structural ownership checks before any ROI experiment."""
import pytest
import test_owned_detail_context_parity as existing
from django.db import connection
from django.test.utils import CaptureQueriesContext
from owned_detail_query_template import build_detail_template_view
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import moderation_views

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def explicit_only(request):
    if not any(str(x).split('::')[0] == 'tests/test_owned_detail_query_template.py'
               for x in request.config.args):
        pytest.skip('Explicit detail query template prototype only')


def test_owned_detail_query_template(request, monkeypatch, record_property):
    with CaptureQueriesContext(connection) as captured:
        candidate, template, retained = build_detail_template_view()
    assert not captured
    native = moderation_views.public_detail
    monkeypatch.setattr(existing, 'build_detail_context_prototype', lambda: candidate)
    monkeypatch.setattr(existing, 'build_native_detail_reference', lambda: native)
    existing.test_owned_detail_context_parity(request, monkeypatch, record_property)
    assert template.cache_info().hits > 0 and retained
    assert all(q._result_cache is None for q in retained)
    with CaptureQueriesContext(connection) as captured:
        first = template('synthetic-version-a')
        second = template('synthetic-version-b')
        clone = first.all()
    assert not captured and first is not second and clone is not first
    assert first.query is not clone.query and first._result_cache is None
    assert first.query.annotations is not clone.query.annotations
    record_property('template_cache', str(template.cache_info()))
    record_property('limits', 'Current RR product A versus resolved annotation template C. '
                    '19 HTTP comparisons, fresh model hydration, no result cache. '
                    'No ROI, concurrent mutation, individual actor or global acceptance claim.')


@pytest.mark.parametrize('mode', ['success', 'render_error', 'inherited_rc', 'inherited_rr'])
def test_template_transaction_scope(request, monkeypatch, mode):
    import test_owned_detail_context_scope as scope
    candidate, _, _ = build_detail_template_view()
    monkeypatch.setattr(scope, 'build_detail_context_prototype', lambda: candidate)
    scope.test_detail_transaction_ownership_and_restore(request, monkeypatch, mode)


@pytest.mark.parametrize('scenario', ['conflict_photo', 'grant_acceptance'])
def test_template_snapshot_transition(request, monkeypatch, record_property, scenario):
    import test_owned_detail_context_snapshot as snapshot
    candidate, _, _ = build_detail_template_view()
    monkeypatch.setattr(snapshot, 'build_detail_context_prototype', lambda **kwargs: candidate)
    snapshot.test_detail_snapshot_transition(request, monkeypatch, record_property,
                                            'trusted_rr', scenario)


def test_template_fresh_document_and_expiry(request, monkeypatch):
    from datetime import timedelta

    from django.utils import timezone
    from owned_detail_context import patch_detail_view

    from apps.core.models import LegalDocument
    from apps.listings.models import Listing
    from apps.listings.submissions import current_publishing_document

    client = request.getfixturevalue('directory')
    listing = Listing.objects.filter(status='published').first()
    candidate, template, retained = build_detail_template_view()
    native = moderation_views.public_detail
    path = f'/es/listing/{listing.pk}/'

    def compare(expected):
        with monkeypatch.context() as patch:
            patch_detail_view(patch, native)
            reference = client.get(path)
        with monkeypatch.context() as patch:
            patch_detail_view(patch, candidate)
            proposed = client.get(path)
        assert reference.status_code == proposed.status_code == expected
        if expected == 404:
            assert reference.content == proposed.content

    compare(200)
    document = current_publishing_document()
    active_ids = list(LegalDocument.objects.filter(slug='publishing', active=True).values_list('pk', flat=True))
    LegalDocument.objects.filter(pk__in=active_ids).update(active=False)
    newer = LegalDocument.objects.create(slug='publishing', version='synthetic-template-v2',
        language=document.language, title='Synthetic', body='Synthetic',
        published_at=timezone.now(), active=True)
    compare(404)
    newer.active = False
    newer.save(update_fields=['active'])
    LegalDocument.objects.filter(pk__in=active_ids).update(active=True)
    compare(200)
    Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now()-timedelta(seconds=1))
    compare(404)
    Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now()+timedelta(days=1))
    compare(200)
    assert template.cache_info().currsize == 2
    assert all(q._result_cache is None for q in retained)
