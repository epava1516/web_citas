"""Real loopback HTTP policy parity; unchanged native reference remains authoritative."""

import hashlib
import json
import os
import re
import socket
import threading
import time
import urllib.request
from urllib.error import HTTPError

import pytest
import test_production_checked_combined_equivalence as reference
from django.db import connection
from django.test.testcases import LiveServerThread
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

pytestmark = pytest.mark.django_db(transaction=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise HTTPError(req.full_url, code, 'Redirect forbidden in policy parity', headers, fp)


@pytest.mark.parametrize('mode', ['normal', 'production'])
def test_policy_checked_real_http100(request, settings, monkeypatch, record_property, mode):
    from pathlib import Path

    run = os.environ.get('LOCAL_CI_ISOLATED_BROKER_RUN')
    assert run and connection.vendor == 'postgresql' and not settings.PRODUCTION
    assert connection.get_autocommit() and not connection.in_atomic_block
    client = request.getfixturevalue('directory')
    original_get = client.get
    reference_evidence, observations, handler_observations = {}, [], []
    main_thread = threading.get_ident()
    database = connection.settings_dict['NAME']
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def observe_handler(handler):
        def observed(environ, start_response):
            assert threading.get_ident() != main_thread
            assert settings.PRODUCTION == (mode == 'production')
            assert settings.VERIFICATION_PROVIDER == 'synthetic-policy-fixture.invalid'
            assert not settings.PROMOTION_TEST_MODE and not settings.RECOVERY_MODE
            assert connection.vendor == 'postgresql' and connection.settings_dict['NAME'] == database
            handler_observations.append({'production': settings.PRODUCTION,
                                         'synthetic_provider': True, 'postgresql_same_database': True})
            return handler(environ, start_response)
        return observed

    server = LiveServerThread('127.0.0.1', observe_handler)
    started = False
    port = None

    def http_get(path, *args, **kwargs):
        nonlocal started, port
        assert not args and not kwargs
        assert path.startswith(('/es/?', '/en/?'))
        if not started:
            server.start()
            started = True
            assert server.is_ready.wait(30), 'Owned WSGI startup deadline'
            assert server.error is None
            port = server.port
        assert server.is_alive() and server.error is None
        query = urllib.request.Request(f'http://127.0.0.1:{port}'+path,
                                       headers={'Host': 'testserver'})
        start = time.perf_counter()
        with opener.open(query, timeout=65) as response:
            body = response.read().decode('utf-8')
            elapsed = time.perf_counter()-start
            assert response.status == 200 and response.headers['Cache-Control'] == 'no-store'
        ids = re.findall(r'<h2><a href="/(?:es|en)/listing/([0-9a-f-]{36})/">', body)
        counts = re.findall(r'<p class="results-count" aria-live="polite">(\d+) (?:results|resultados)</p>', body)
        cards = re.findall(r'<article class="card listing-card">(.*?)</article>', body, re.S)
        assert len(counts) == 1 and len(cards) == len(ids) == len(set(ids))
        assert all('<p class="sponsored">' not in card for card in cards)
        # This response is subsequently checked against the unchanged native oracle.
        native_response = original_get(path)
        assert native_response.status_code == 200
        page = native_response.context['page']
        assert ids == [str(row.pk) for row in page.object_list]
        assert int(counts[0]) == page.paginator.count
        assert all(card['sponsorship'] is None for card in native_response.context['cards'])
        observations.append({'path': path, 'http_status': 200, 'cache_control': 'no-store',
                             'native_count': int(counts[0]), 'returned': len(ids),
                             'ordered_ids_sha256': hashlib.sha256('\n'.join(ids).encode()).hexdigest(),
                             'sponsorship': [None]*len(ids), 'http_wall_seconds': elapsed})
        return native_response

    def capture(name, value):
        assert name == 'production_checked_combined_equivalence' and not reference_evidence
        reference_evidence.update(value)

    try:
        with monkeypatch.context() as patch:
            patch.setattr(client, 'get', http_get)
            reference.test_combined_checked_native_pages_and_obsolete_proof(
                request, settings, capture, mode)
    finally:
        if started:
            server.terminate()
            assert not server.is_alive()
    assert client.get == original_get and started and port
    with socket.socket() as closed:
        closed.settimeout(1)
        assert closed.connect_ex(('127.0.0.1', port)) != 0
    expected = 114 if mode == 'normal' else 96
    assert len(observations) == len(handler_observations) == expected
    assert reference_evidence['pages_checked'] == expected
    assert reference_evidence['reads_do_not_repair'] and reference_evidence['manual_repair']
    for observed, native in zip(observations, reference_evidence['observations'], strict=True):
        assert observed['native_count'] == native['count']
        observed.update({key: native[key] for key in ('phase', 'city', 'checked', 'locale', 'page')})
    result = {'result': 'POLICY_CHECKED_HTTP100_INTEGRATION_NOT_CAPACITY',
              'mode': mode, 'population': 100, 'reference': reference_evidence,
              'observations': observations, 'handler_observations': handler_observations,
              'reference_sha256': hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
              'http_requests': expected, 'native_client_requests': expected,
              'server_thread_stopped': True, 'socket_closed': True,
              'native_parity_every_http_response': True,
              'capacity_accepted': False, 'real_provider_credited': False,
              'worker_execution_credited': False,
              'scope': 'Sequential loopback TCP through Django WSGI and middleware, same-process '
                       'settings and separate PostgreSQL request connections. Real socket, not Gunicorn '
                       'or deployment configuration. Synthetic policy metadata, no external provider. '
                       'Each HTML signature equals the response checked by the unchanged native oracle. '
                       'No redirects, no assets, no burst, no upload, no per-service CPU or SLO. '
                       'Production means the public eligibility policy, not production deployment.'}
    output = Path(settings.BASE_DIR)/'artifacts/local-ci'/run/f'beta-policy-checked-http100-{mode}.json'
    output.write_text(json.dumps(result, indent=2)+'\n')
    record_property('policy_checked_http', json.dumps(result))
