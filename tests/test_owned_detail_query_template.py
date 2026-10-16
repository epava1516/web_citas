"""Explicit parity and structural ownership checks before any ROI experiment."""
import pytest
import test_owned_detail_context_parity as existing
from django.db import connection
from django.test.utils import CaptureQueriesContext
from owned_detail_query_template import build_detail_template_view
from owned_detail_rr_reference import build_previous_rr_detail
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
    native = build_previous_rr_detail()
    monkeypatch.setattr(existing, 'build_detail_context_prototype', lambda: moderation_views.public_detail)
    monkeypatch.setattr(existing, 'build_native_detail_reference', lambda: native)
    existing.test_owned_detail_context_parity(request, monkeypatch, record_property)
    from apps.listings.public_validation import _detail_query_template
    assert _detail_query_template.cache_info().hits > 0
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
    candidate = moderation_views.public_detail
    native = build_previous_rr_detail()
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
    from apps.listings.public_validation import _detail_query_template
    assert _detail_query_template.cache_info().currsize >= 2
    assert all(q._result_cache is None for q in retained)


@pytest.mark.parametrize('scenario', ['localization_catalog', 'production_provenance', 'privacy_hold'])
def test_template_existing_controls(request, monkeypatch, settings, scenario):
    import test_owned_detail_context_existing_guards as guards
    candidate, _, _ = build_detail_template_view()
    monkeypatch.setattr(guards, 'build_detail_context_prototype', lambda: candidate)
    guards.test_existing_controls_under_rr_detail(request, monkeypatch, settings, scenario)


def test_template_fresh_expiry_during_request(request, monkeypatch):
    import test_owned_detail_context_existing_guards as guards
    candidate, _, _ = build_detail_template_view()
    monkeypatch.setattr(guards, 'build_detail_context_prototype', lambda: candidate)
    guards.test_expiry_clock_not_frozen_by_rr(request, monkeypatch)


def test_template_both_actors_languages(request, monkeypatch, record_property):
    from django.core import signing
    from owned_detail_context import patch_detail_view

    from apps.core.models import Person

    client = request.getfixturevalue('directory')
    candidate, template, retained = build_detail_template_view()
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: stamp)
    cases = []
    for lookup in [{'individual__username':'fixture-v1-individual'},
                   {'subject__username':'fixture-v1-model-a'}]:
        person = Person.objects.get(**lookup)
        for language in ['es', 'en']:
            path = f'/{language}/listing/{person.listing.pk}/'
            with monkeypatch.context() as patch:
                patch_detail_view(patch, build_previous_rr_detail())
                reference = client.get(path)
            with monkeypatch.context() as patch:
                patch_detail_view(patch, candidate)
                proposed = client.get(path)
            assert reference.status_code == proposed.status_code == 200
            assert reference.content == proposed.content
            assert reference.headers['Cache-Control'] == proposed.headers['Cache-Control'] == 'no-store'
            cases.append((next(iter(lookup)), language))
    assert template.cache_info().hits >= 3
    assert all(q._result_cache is None for q in retained)
    record_property('actor_language_parity', str(cases))
