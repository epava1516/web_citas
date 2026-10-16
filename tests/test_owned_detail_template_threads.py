"""Owned shared-process concurrent body parity; no performance acceptance."""
import hashlib
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core import signing
from django.core.handlers.wsgi import WSGIHandler
from django.db import connections
from django.test import RequestFactory
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.public_validation import _detail_query_template
from apps.listings.submissions import current_publishing_document

pytestmark = pytest.mark.django_db(transaction=True)


def test_owned_detail_template_threads(request, monkeypatch, record_property):
    if not any(str(x).split('::')[0] == 'tests/test_owned_detail_template_threads.py'
               for x in request.config.args):
        pytest.skip('Explicit shared-process detail template parity only')
    request.getfixturevalue('directory')
    stamp = signing.TimestampSigner().timestamp()
    monkeypatch.setattr(signing.TimestampSigner, 'timestamp', lambda self: stamp)
    identities = [Person.objects.get(**lookup).listing.pk for lookup in [
        {'individual__username':'fixture-v1-individual'},
        {'subject__username':'fixture-v1-model-a'},
    ]]
    routes = [f'/{language}/listing/{identity}/' for identity in identities for language in ['es','en']]
    handler = WSGIHandler()

    def read(route):
        statuses = []
        def begin(status, headers, exc_info=None):
            statuses.append((status,dict(headers)))
        response = handler(RequestFactory().get(route).environ, begin)
        try:
            body = b''.join(response)
        finally:
            response.close()
        assert statuses[0][0].startswith('200 ')
        assert statuses[0][1]['Cache-Control'] == 'no-store'
        return hashlib.sha256(body).hexdigest()

    expected = {route:read(route) for route in routes}
    version = current_publishing_document().version
    template = _detail_query_template(version)
    before = template.query.sql_with_params()
    assert template._result_cache is None
    _detail_query_template.cache_clear()  # Exercise simultaneous cold template acquisition.
    barrier = Barrier(8, timeout=30)

    def worker(index):
        try:
            barrier.wait()
            for offset in range(3):
                route = routes[(index+offset) % len(routes)]
                assert read(route) == expected[route]
            return 3
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(worker, range(8))) == 24
    after = _detail_query_template(version)
    assert after._result_cache is None
    assert after.query.sql_with_params() == before
    assert _detail_query_template.cache_info().currsize == 1
    record_property('shared_template_parity', '24 requests,8 threads,individual+agency,ES+EN,200/no-store/body hash equal; cold cache acquisition and unchanged parameterized template')
