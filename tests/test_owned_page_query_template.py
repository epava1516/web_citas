"""Explicit parity gate for unevaluated page hydration templates; no product patch."""
import hashlib

import pytest
from django.core import signing
from django.db import connection
from django.test.utils import CaptureQueriesContext
from owned_page_query_template import build_page_template
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.listings import publication_state
from apps.listings.models import Listing, PublicationDirty
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture(autouse=True)
def explicit_only(request):
    if not any(str(x).split('::')[0] == 'tests/test_owned_page_query_template.py'
               for x in request.config.args):
        pytest.skip('Explicit owned page query structure prototype only')


def test_page_template_parity(request, monkeypatch, record_property):
    client = request.getfixturevalue('directory')
    data = populate(80)
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: stamp)
    with CaptureQueriesContext(connection) as queries:
        proposed, template, retained = build_page_template()
    assert len(queries) == 0
    original = publication_state._state_page
    victim = data['sample_ids'][0]
    observations = []
    for scenario in ('clean', 'dirty', 'paused'):
        publication_state.refresh_all()
        if scenario == 'dirty':
            publication_state.mark([victim])
        elif scenario == 'paused':
            Listing.objects.filter(pk=victim).update(status='paused')
        markers = list(PublicationDirty.objects.order_by('pk').values_list('pk', 'generation'))
        for language, term in [('es', ''), ('en', ''), ('es', 'photography'), ('en', 'synthetic')]:
            route = f'/{language}/'
            probe = client.get(route, {'q': term})
            last = probe.context['page'].paginator.num_pages
            for number in sorted({1, min(2, last)}):
                params = {'q': term, 'page': number}
                with monkeypatch.context() as patch:
                    patch.setattr(publication_state, '_state_page', original)
                    reference = client.get(route, params)
                with monkeypatch.context() as patch:
                    patch.setattr(publication_state, '_state_page', proposed)
                    candidate = client.get(route, params)
                assert reference.status_code == candidate.status_code == 200
                assert reference['Cache-Control'] == candidate['Cache-Control'] == 'no-store'
                assert reference.context['page'].paginator.count == candidate.context['page'].paginator.count
                assert [r.pk for r in reference.context['page']] == [r.pk for r in candidate.context['page']]
                assert reference.content == candidate.content
                assert markers == list(PublicationDirty.objects.order_by('pk').values_list('pk', 'generation'))
                observations.append({'scenario': scenario, 'language': language, 'term': term,
                                     'page': number, 'body_sha256': hashlib.sha256(candidate.content).hexdigest()})
    assert template.cache_info().hits > 0
    assert retained and all(q._result_cache is None for q in retained)
    before = [str(q.query) for q in retained]
    template('synthetic-new-version').filter(pk__in=())
    assert before == [str(q.query) for q in retained[:len(before)]]
    record_property('page_template_parity', observations)


@pytest.mark.parametrize('name', ['publishing_terms_replaced', 'category_inactive', 'expired'])
def test_page_template_rechecks_dependencies(request, monkeypatch, name):
    import test_publication_state as existing

    proposed, _, _ = build_page_template()
    monkeypatch.setattr(publication_state, '_state_page', proposed)
    existing.test_dependency_change_is_reflected_without_refresh(request, monkeypatch, name)
