"""Actual TCP/CSRF clients for the owned capacity flow; no forwarded-IP override."""

import hashlib
import http.client
import http.cookiejar
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from types import SimpleNamespace

from django.test import Client


class SourceHTTPHandler(urllib.request.HTTPHandler):
    def __init__(self, address):
        super().__init__()
        self.address = address
        self.observed_addresses = []

    def http_open(self, request):
        handler = self

        class Connection(http.client.HTTPConnection):
            def connect(self):
                super().connect()
                address = self.sock.getsockname()[0]
                handler.observed_addresses.append(address)
                assert address == handler.address

        return self.do_open(
            lambda host, **kwargs: Connection(host, source_address=(self.address, 0), **kwargs),
            request,
        )



class PrivateDeliveryRedirect(urllib.request.HTTPRedirectHandler):
    """Return303 to the measurement, preserving ordinary workflow302 behavior."""
    def redirect_request(self, request, response, code, message, headers, newurl):
        if code == 303 and urllib.parse.urlsplit(newurl).path.startswith("/private-deliveries/"):
            return None
        return super().redirect_request(request, response, code, message, headers, newurl)


class PrivateProxyTransport(urllib.request.HTTPHandler):
    """Cookie URL retains the original host; only private GET uses own Caddy TCP."""
    def http_open(self, request):
        assert request.get_method() == "GET"
        assert urllib.parse.urlsplit(request.full_url).path.startswith("/private-deliveries/")
        return self.do_open(lambda host, **kwargs: http.client.HTTPConnection("caddy:8080", **kwargs), request)

def operator(actor):
    browser = Client()
    browser.force_login(actor)
    actor.refresh_from_db()
    session = browser.session
    session["mfa_version"] = actor.mfa_version
    session["account_version"] = actor.session_version
    session.save()
    return browser


def open_client(settings, server, path, *, actor=None, source_address=None):
    cookies = http.cookiejar.CookieJar()
    handler = SourceHTTPHandler(source_address) if source_address else None
    if actor is not None:
        browser = operator(actor)
        host = urllib.parse.urlparse(server.url).hostname
        cookie_host = host if "." in host else host + ".local"
        cookies.set_cookie(http.cookiejar.Cookie(
            0, settings.SESSION_COOKIE_NAME, browser.cookies[settings.SESSION_COOKIE_NAME].value,
            None, False, cookie_host, False, False, "/", True, False, None, True, None, None, {},
        ))
    objects = getattr(settings, "CAPACITY_OBJECT_DELIVERY", False)
    handlers = [urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(cookies)]
    if objects:
        handlers.append(PrivateDeliveryRedirect())
    if handler:
        handlers.append(handler)
    client = urllib.request.build_opener(*handlers)
    if objects:
        client.private_delivery = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(cookies), PrivateProxyTransport())
    begin = time.perf_counter()
    with client.open(server.url + path, timeout=120) as response:
        body = response.read()
        assert response.status == 200 and "no-store" in response.headers["Cache-Control"]
    elapsed = time.perf_counter() - begin
    csrf = next(cookie.value for cookie in cookies if cookie.name == settings.CSRF_COOKIE_NAME)
    return SimpleNamespace(client=client, csrf=csrf, handler=handler,
                           first_open_seconds=elapsed, first_open_bytes=len(body))


def post(client, endpoint, csrf, values, *, timeout=120, headers=None):
    query = urllib.request.Request(endpoint, data=urllib.parse.urlencode(values, doseq=True).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded",
                 "Referer": endpoint, "X-CSRFToken": csrf, **(headers or {})})
    begin = time.perf_counter()
    try:
        response = client.open(query, timeout=timeout)
    except urllib.error.HTTPError as error:
        response = error
    stages = []
    with response:
        body = response.read()
        end = time.perf_counter()
        status, result_headers = response.code, dict(response.headers)
        stages.append({"method": "POST", "status": status, "interval": [begin, end],
                       "seconds": end-begin, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
    if status == 303:
        location = urllib.parse.urljoin(endpoint, result_headers["Location"])
        parsed, original = urllib.parse.urlsplit(location), urllib.parse.urlsplit(endpoint)
        assert (parsed.scheme, parsed.netloc) == (original.scheme, original.netloc)
        assert parsed.path.startswith("/private-deliveries/") and not parsed.query
        assert hasattr(client, "private_delivery"), "Proxy feature not active in actual client"
        delivered_query = location
        markers = [value for name, value in (headers or {}).items()
                   if isinstance(name, str) and name.lower() == 'x-capacity-profile']
        if (len(markers) == 1 and isinstance(markers[0], str)
                and re.fullmatch(r'[a-z_]{1,34}', markers[0])):
            # Only an explicitly profiled extra request marks its private GET.
            # No POST authorization/CSRF/Referer headers cross this boundary.
            delivered_query = urllib.request.Request(
                location, headers={'X-Capacity-Profile': markers[0] + '_proxy'}, method='GET')
        delivered_begin = time.perf_counter()
        with client.private_delivery.open(delivered_query, timeout=timeout) as delivered:
            body = delivered.read()  # EOF included, never header timing substituted.
            end = time.perf_counter()
            status, result_headers = delivered.status, dict(delivered.headers)
        stages.append({"method": "GET", "transport": "own-caddy:8080", "status": status,
                       "interval": [delivered_begin, end], "seconds": end-delivered_begin,
                       "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        assert status == 200 and "no-store" in result_headers.get("Cache-Control", "")
    return SimpleNamespace(status=status, headers=result_headers, body=body,
                           seconds=end-begin, interval=[begin, end], stages=stages)
