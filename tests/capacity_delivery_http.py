"""Actual TCP/CSRF clients for the owned capacity flow; no forwarded-IP override."""

import http.client
import http.cookiejar
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
    handlers = [urllib.request.HTTPCookieProcessor(cookies)]
    if handler:
        handlers.append(handler)
    client = urllib.request.build_opener(*handlers)
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
    with response:
        body = response.read()
        end = time.perf_counter()
        return SimpleNamespace(status=response.code, headers=dict(response.headers), body=body,
                               seconds=end - begin, interval=[begin, end])
