"""Local opener transport contract; this is not real Caddy or capacity evidence."""
import urllib.request
from types import SimpleNamespace

import capacity_delivery_http as http
import pytest


class Response:
    def __init__(self, status, headers, body):
        self.status = self.code = status
        self.headers, self.body, self.reads, self.closed = headers, body, [], False

    def read(self, *args):
        self.reads.append(args)
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


class Opener:
    def __init__(self, response):
        self.response, self.calls = response, []

    def open(self, query, timeout):
        self.calls.append((query, timeout))
        return self.response


def run(monkeypatch, headers=None, location='/private-deliveries/synthetic-token', cache='private, no-store'):
    ticks = iter([1.0, 2.0, 3.0, 4.0])
    monkeypatch.setattr(http.time, 'perf_counter', lambda: next(ticks))
    posted = Response(303, {'Location': location}, b'redirect-body')
    delivered = Response(200, {'Cache-Control': cache}, b'complete-private-body' * 1024)
    proxy = Opener(delivered)
    client = Opener(posted)
    client.private_delivery = proxy
    result = http.post(client, 'http://app:8000/private/copy/', 'private-csrf',
                       {'reason': 'synthetic-reason'}, timeout=73, headers=headers)
    return SimpleNamespace(result=result, posted=posted, delivered=delivered, client=client, proxy=proxy)


@pytest.mark.parametrize('name', ['X-Capacity-Profile', 'x-capacity-profile'])
def test_explicit_profile_only_marker_reaches_private_get_with_full_timing(monkeypatch, name):
    observed = run(monkeypatch, {name: 'coverage_page_read', 'Authorization': 'private-authorization',
                                 'X-Other-Secret': 'private-other', 'Cookie': 'private-cookie'})
    query, timeout = observed.proxy.calls[0]
    assert isinstance(query, urllib.request.Request)
    assert query.get_method() == 'GET' and query.data is None
    assert query.full_url == 'http://app:8000/private-deliveries/synthetic-token'
    assert dict(query.header_items()) == {'X-capacity-profile': 'coverage_page_read_proxy'}
    assert timeout == 73
    assert len(observed.client.calls) == len(observed.proxy.calls) == 1
    assert observed.posted.reads == observed.delivered.reads == [()]
    assert observed.posted.closed and observed.delivered.closed
    assert observed.result.status == 200
    assert observed.result.body == observed.delivered.body
    assert observed.result.interval == [1.0, 4.0] and observed.result.seconds == 3.0
    assert [stage['method'] for stage in observed.result.stages] == ['POST', 'GET']
    assert [stage['interval'] for stage in observed.result.stages] == [[1.0, 2.0], [3.0, 4.0]]


@pytest.mark.parametrize('headers', [None, {}, {'X-Capacity-Profile': 'UPPER'},
    {'X-Capacity-Profile': 'a' * 35}, {'X-Capacity-Profile': 'stage/secret'},
    {'X-Capacity-Profile': 'stage proxy'}, {'X-Capacity-Profile': '1'},
    {'X-Capacity-Profile': 'stage', 'x-capacity-profile': 'other'}])
def test_missing_or_invalid_profile_keeps_original_string_get(monkeypatch, headers):
    observed = run(monkeypatch, headers)
    query, timeout = observed.proxy.calls[0]
    assert query == 'http://app:8000/private-deliveries/synthetic-token'
    assert isinstance(query, str) and timeout == 73
    assert observed.result.status == 200 and observed.result.seconds == 3.0
    assert observed.delivered.reads == [()]
    assert len(observed.proxy.calls) == 1


@pytest.mark.parametrize('location', ['http://foreign/private-deliveries/token', '/public/token',
                                       '/private-deliveries/token?secret=x'])
def test_profile_does_not_relax_original_redirect_scope(monkeypatch, location):
    with pytest.raises(AssertionError):
        run(monkeypatch, {'X-Capacity-Profile': 'coverage_page_read'}, location=location)


def test_profile_does_not_relax_private_cache_control(monkeypatch):
    with pytest.raises(AssertionError):
        run(monkeypatch, {'X-Capacity-Profile': 'coverage_page_read'}, cache='public')
