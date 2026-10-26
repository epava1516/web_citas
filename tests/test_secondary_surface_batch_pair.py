"""Explicit paired real Client callbacks; exact Git baseline versus current candidate.

No timings are acceptance assertions. Root applies the preregistered six-segment cost
rule to the recorded pairs, keeping ordinal0 separate from the five subsequent GETs.
"""

import copy
import hashlib
import json
import os
import re
import resource
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import timedelta
from math import ceil
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit
from xml.etree.ElementTree import fromstring

import pytest
from django.conf import settings as django_settings
from django.db import connection
from django.test import Client
from django.urls import URLPattern, URLResolver, get_resolver, resolve, reverse
from django.utils import timezone, translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core import sitemaps
from apps.core.models import Person, User
from apps.listings import favorites
from apps.listings.models import Favorite, Listing, Revision
from apps.listings.moderation import publicly_visible
from apps.listings.seo import absolute, listing_languages
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)
BASELINE_COMMIT = "7107363794b378be3fe71e69998f83d9230888f2"
SOURCES = {
    "favorites": ("apps/listings/favorites.py", "apps.listings",
                  "e4fe5cac54dc2507838457b7fd472e32e4756749b8ed28958e08b1d4234f5429"),
    "sitemaps": ("apps/core/sitemaps.py", "apps.core",
                 "fc4a10139464e364b07aac5cc4e31a60958d17d841a1d4cf7115ba3f4fb9005e"),
}
NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9", "h": "http://www.w3.org/1999/xhtml"}
CSRF_INPUT = re.compile(
    br'<input\b(?=[^>]*\bname="csrfmiddlewaretoken")[^>]*\bvalue="(?P<token>[^"]*)"[^>]*>'
)
SCOPE = (
    "Same persisted cohort/session and real middleware per pair; callback selected in URLPattern only; "
    "fixed Git source hash versus imported candidate source hash; no guard/auth/SQL/clock substitute. "
    "Client.GET plus body wall/processCPU and connection execute_wrapper cursor count/time. "
    "Own/global nested observers are separate, never summed; SQL has no queries_log dependency. "
    "Only CSRF hidden-input values and actual request CSP nonce attributes/directive normalized; "
    "XML exact bytes. Cookie values compare by digest except the CSRF secret; all attributes compare "
    "except that CSRF cookie's rolling Expires. No unrelated cookie values are omitted. "
    "No cold-cache, percentile, browser, worker, provider, CSRF or production claim; no timing assertion."
)


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit owned serial secondary surface pair only")
    assert not os.environ.get("PYTEST_XDIST_WORKER")
    assert connection.vendor == "postgresql" and not settings.PRODUCTION
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    assert sys.platform == "linux", "RSS high-water diagnostic uses Linux KiB units"
    language = translation.get_language()
    request.addfinalizer(lambda: translation.activate(language))


def _sources():
    """Read local immutable Git bytes at runtime; execute their real imports/decorators."""
    root = Path(__file__).resolve().parents[1]
    baseline, hashes = {}, {}
    current = {"favorites": favorites, "sitemaps": sitemaps}
    for name, (path, package, expected) in SOURCES.items():
        result = subprocess.run(["git", "show", f"{BASELINE_COMMIT}:{path}"], cwd=root,
                                capture_output=True, check=True)
        source = result.stdout
        assert hashlib.sha256(source).hexdigest() == expected
        namespace = {"__name__": package + "._n08a2_baseline_" + name,
                     "__package__": package, "__file__": BASELINE_COMMIT + ":" + path}
        exec(compile(source, namespace["__file__"], "exec"), namespace)
        baseline[name] = SimpleNamespace(**namespace)
        candidate_sha = hashlib.sha256(Path(current[name].__file__).read_bytes()).hexdigest()
        assert candidate_sha != expected, "Paired instrument requires the actual proposed candidate"
        hashes[name] = {"baseline": expected, "candidate": candidate_sha}
    assert baseline["sitemaps"].PAGE_SIZE == sitemaps.PAGE_SIZE == 100
    callbacks = {
        "baseline": {"favorites": baseline["favorites"].index,
                     "sitemap_listings": baseline["sitemaps"].listings,
                     "sitemap_index": baseline["sitemaps"].index},
        "candidate": {"favorites": favorites.index, "sitemap_listings": sitemaps.listings,
                      "sitemap_index": sitemaps.index},
    }
    return callbacks, hashes


def _patterns():
    found = {name: [] for name in ["favorites", "sitemap_listings", "sitemap_index"]}
    seen = set()

    def visit(patterns):
        for pattern in patterns:
            if id(pattern) in seen:
                continue
            seen.add(id(pattern))
            if isinstance(pattern, URLResolver):
                visit(pattern.url_patterns)
            elif isinstance(pattern, URLPattern) and pattern.name in found:
                found[pattern.name].append(pattern)

    visit(get_resolver().url_patterns)
    assert all(found.values())
    return found


@contextmanager
def _selected(patterns, callbacks):
    with pytest.MonkeyPatch.context() as patch:
        for name, matches in patterns.items():
            for pattern in matches:
                patch.setattr(pattern, "callback", callbacks[name])
        yield
    # MonkeyPatch restores callbacks even after an exception or failed assertion.


def _snapshot():
    # All persisted scalar fields, including edit/status/version/timestamps, stay local.
    return {model._meta.label: list(model.objects.order_by("pk").values())
            for model in [Favorite, Listing, Revision, Person]}


def _snapshot_sha(snapshot):
    return hashlib.sha256(repr(snapshot).encode()).hexdigest()


def _normalized(response, body):
    headers = {key.lower(): value for key, value in response.items()}
    normalized = body
    counts = {"csrf_hidden_values": 0, "nonce_body_attributes": 0, "nonce_csp_directives": 0}
    if headers.get("content-type", "").startswith("text/html"):
        def mask(match):
            nonlocal counts
            token = match.group("token")
            assert re.fullmatch(br"[A-Za-z0-9]{64}", token), "Unexpected CSRF token shape"
            counts["csrf_hidden_values"] += 1
            start, end = match.span("token")
            return match.group()[:start - match.start()] + b"<csrf>" + match.group()[end - match.start():]

        normalized = CSRF_INPUT.sub(mask, normalized)
    nonce = getattr(response.wsgi_request, "csp_nonce", None)
    if nonce:
        nonce = str(nonce)
        assert nonce and "\"" not in nonce and "'" not in nonce
        for quote in [b'"', b"'"]:
            actual = b"nonce=" + quote + nonce.encode() + quote
            counts["nonce_body_attributes"] += normalized.count(actual)
            normalized = normalized.replace(actual, b"nonce=" + quote + b"<nonce>" + quote)
        actual = "'nonce-" + nonce + "'"
        csp = headers.get("content-security-policy", "")
        counts["nonce_csp_directives"] = csp.count(actual)
        if counts["nonce_csp_directives"]:
            headers["content-security-policy"] = csp.replace(actual, "'nonce-<nonce>'")
    cookies = {}
    for name, morsel in response.cookies.items():
        attributes = dict(morsel.items())
        if name == django_settings.CSRF_COOKIE_NAME:
            value = "<csrf-cookie-secret>"
            if attributes.get("expires"):
                attributes["expires"] = "<rolling-csrf-expiry>"
        else:
            value = hashlib.sha256(morsel.value.encode()).hexdigest()
        cookies[name] = {"value_sha256_or_csrf_marker": value, "attributes": attributes}
    return normalized, headers, cookies, counts


def _get(client, path):
    totals = {"sql_queries": 0, "sql_execute_seconds": 0.0}

    def observe(execute, sql, params, many, context):
        totals["sql_queries"] += 1
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            totals["sql_execute_seconds"] += time.perf_counter() - started

    cpu_started = time.process_time()
    started = time.perf_counter()
    with connection.execute_wrapper(observe):
        response = client.get(path)
        body = response.content
    totals.update(wall_seconds=time.perf_counter() - started,
                  cpu_seconds=time.process_time() - cpu_started, response_bytes=len(body))
    return response, body, totals


def _pair(client, path, *, callbacks, patterns, hashes, rows, state, surface,
          language, check, repetitions=1, category="control", page=1):
    before = _snapshot()
    before_sha = _snapshot_sha(before)
    route = "favorites" if surface == "favorites" else surface
    module = "favorites" if route == "favorites" else "sitemaps"
    for ordinal in range(repetitions):
        order = ["baseline", "candidate"] if ordinal % 2 == 0 else ["candidate", "baseline"]
        compared = {}
        # Preserve the same incoming session/CSRF cookie state for each half-pair.
        incoming_cookies = copy.deepcopy(client.cookies)
        for position, variant in enumerate(order):
            client.cookies = copy.deepcopy(incoming_cookies)
            chosen = callbacks[variant][route]
            with _selected(patterns, callbacks[variant]):
                assert resolve(urlsplit(path).path).func is chosen
                response, body, timing = _get(client, path)
                # Client.resolver_match is lazy: force it before callback restoration.
                assert response.resolver_match.func is chosen
            normalized, headers, cookies, normalization = _normalized(response, body)
            row = {
                "variant": variant, "category": category, "state": state, "surface": surface,
                "language": language, "page": page, "ordinal": ordinal, "order_position": position,
                "status": response.status_code, "route_name": response.resolver_match.view_name,
                "response_language": response.wsgi_request.LANGUAGE_CODE,
                "headers": headers, "cookie_security_attributes": cookies,
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "normalized_sha256": hashlib.sha256(normalized).hexdigest(),
                "normalization": normalization, "observed_function_source_sha256": hashes[module][variant],
                "resolved_callback_verified": response.resolver_match.func is chosen,
                "snapshot_sha256": before_sha, **timing,
            }
            rows.append(row)  # Preserve actual measurements before any oracle can fail.
            assert response.resolver_match.func is chosen
            check(response, body)
            assert _snapshot() == before, "GET changed persisted domain data"
            compared[variant] = (response.status_code, headers, cookies, normalized)
        assert compared["baseline"] == compared["candidate"], "Unapproved response difference"


def _client(user):
    client = Client()
    client.force_login(user)
    session = client.session
    session["account_version"] = user.session_version
    session.save()
    return client


def _favorite_check(user, own, universe, visible_ids, *, hidden=None, foreign=None):
    ordered = sorted(own, key=lambda item: (item.created_at, item.pk), reverse=True)
    expected = ordered[:24]
    expected_ids = [item.pk for item in expected]
    expected_visible = visible_ids & {item.listing_id for item in expected}
    listing_by_id = {listing.pk: listing for listing in universe}
    language = translation.get_language()
    links = {listing.pk: f'href="{reverse("listing_detail", args=[listing.pk])}"'.encode()
             for listing in universe}
    actions = {favorite.pk: f'action="{reverse("favorite_remove", args=[favorite.pk])}"'.encode()
               for favorite in own + ([foreign] if foreign is not None else [])}

    def check(response, body):
        assert response.status_code == 200 and response.resolver_match.view_name == "favorites"
        assert response.wsgi_request.LANGUAGE_CODE == response["Content-Language"] == language
        assert response["Cache-Control"] == "private, no-store"
        page = response.context["page"]
        entries = list(response.context["entries"])
        assert page.number == 1 and page.paginator.per_page == 24
        assert page.paginator.count == len(own) and page.paginator.num_pages == max(1, ceil(len(own) / 24))
        assert [entry["favorite"].pk for entry in entries] == expected_ids
        assert [item.pk for item in list(page.object_list)] == expected_ids
        assert {entry["favorite"].listing_id for entry in entries if entry["visible"]} == expected_visible
        for entry in entries:
            favorite = entry["favorite"]
            assert favorite.user_id == user.pk
            assert favorite.listing.pk == listing_by_id[favorite.listing_id].pk
            if entry["visible"]:
                revision = favorite.listing.approved_revision
                assert revision.pk == listing_by_id[favorite.listing_id].approved_revision_id
                assert revision.listing_id == favorite.listing_id
                assert revision.title.encode() in body
        for identifier, link in links.items():
            assert (link in body) == (identifier in expected_visible)
            if identifier not in expected_visible:
                assert str(identifier).encode() not in body
        for identifier, action in actions.items():
            assert (action in body) == (identifier in expected_ids)
        invisible_count = len(expected) - len(expected_visible)
        placeholder = b"Listing unavailable" if language == "en" else b"Anuncio no disponible"
        assert body.count(placeholder) == invisible_count
        if hidden is not None:
            assert str(hidden.pk).encode() not in body
            visible_titles = {listing_by_id[identifier].approved_revision.title for identifier in expected_visible}
            if hidden.approved_revision and hidden.approved_revision.title not in visible_titles:
                assert hidden.approved_revision.title.encode() not in body
        if foreign is not None:
            assert str(foreign.listing_id).encode() not in body

    return check


def _xml_check(selected, versions, hidden_id=None):
    expected = []
    for listing in selected:
        if listing.pk == hidden_id:
            continue
        alternatives = [{"rel": "alternate", "hreflang": language, "href": address}
                        for language, address in versions[listing.pk]]
        expected.extend((address, alternatives) for _, address in versions[listing.pk])

    def check(response, body):
        assert response.status_code == 200 and response.resolver_match.view_name == "sitemap_listings"
        assert response["Cache-Control"] == "no-store" and response["X-Robots-Tag"] == "noindex, nofollow"
        assert response["Content-Type"] == "application/xml"
        root = fromstring(body)
        assert root.tag == f"{{{NS['s']}}}urlset"
        actual = []
        for node in root:
            assert node.tag == f"{{{NS['s']}}}url"
            location = node.find("s:loc", NS)
            assert location is not None and not location.attrib
            alternate_nodes = node.findall("h:link", NS)
            assert len(list(node)) == 1 + len(alternate_nodes)
            actual.append((location.text, [link.attrib for link in alternate_nodes]))
        assert actual == expected
        assert all("?" not in address for address, _ in actual)
        if hidden_id is not None:
            assert str(hidden_id).encode() not in body

    return check


def _index_check(settings, count):
    expected = [settings.PUBLIC_ORIGIN + reverse("sitemap_directory")] + [
        settings.PUBLIC_ORIGIN + reverse("sitemap_listings", args=[page])
        for page in range(1, ceil(count / 100) + 1)
    ]

    def check(response, body):
        assert response.status_code == 200 and response.resolver_match.view_name == "sitemap_index"
        assert response["Cache-Control"] == "no-store" and response["X-Robots-Tag"] == "noindex, nofollow"
        root = fromstring(body)
        assert root.tag == f"{{{NS['s']}}}sitemapindex"
        assert [node.tag for node in root] == [f"{{{NS['s']}}}sitemap"] * len(expected)
        assert all(len(list(node)) == 1 for node in root)
        assert [node.text for node in root.findall("s:sitemap/s:loc", NS)] == expected

    return check


def _status_check(status):
    def check(response, body):
        assert response.status_code == status
        if status == 302:
            assert "login" in response.url
        assert b"N08A2_PRIVATE_QUERY" not in body
    return check


def _set_candidates(listings, count):
    Listing.objects.filter(pk__in=[listing.pk for listing in listings]).update(status="paused")
    Listing.objects.filter(pk__in=[listing.pk for listing in listings[:count]]).update(status="published")


def _own_favorites(user, listings, count):
    Favorite.objects.filter(user=user).delete()
    own = Favorite.objects.bulk_create([Favorite(user=user, listing=listing) for listing in listings[:count]])
    stamp = timezone.now()
    for ordinal, favorite in enumerate(own):
        favorite.created_at = stamp + timedelta(seconds=ordinal)
    if own:
        Favorite.objects.bulk_update(own, ["created_at"])
    return own


@contextmanager
def _report(record_property, name, rows, metadata):
    try:
        yield
    finally:
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
        record_property(name, json.dumps({
            "rows": rows, "scope": SCOPE, "metadata": metadata,
            "process_high_water_rss_bytes": rss,
            "memory_scope": "Linux process lifetime high-water; not per-version memory",
            "memory_diagnostic_limit_bytes": 1024 ** 3,
        }, sort_keys=True))
        assert rss <= 1024 ** 3, "Process high-water exceeds preregistered diagnostic limit"


def test_secondary_surface_batch_pair(request, settings, record_property):
    _guard(request, settings)
    callbacks, hashes = _sources()
    patterns = _patterns()
    rows = []
    metadata = {"baseline_commit": BASELINE_COMMIT, "source_sha256": hashes,
                "planned_target_gets": 72, "planned_control_gets": 42,
                "planned_total_gets": 114, "populate_calls": 1,
                "favorite_page_size": 24, "sitemap_page_size": 100,
                "target_segments": 6, "target_repetitions_per_variant_segment": 6,
                "preparation": "native directory, eager fixtures and populate101 shared synthetic media",
                "readonly_models": ["Favorite", "Listing", "Revision", "Person"]}
    with _report(record_property, "secondary_batch_pair", rows, metadata):
        public = request.getfixturevalue("directory")
        population = populate(101)
        assert population["published"] == 101 and population["shared_synthetic_photo_fixture"]
        settings.PUBLIC_ORIGIN = "https://paired-secondary.example.invalid"
        listings = list(Listing.objects.filter(status="published")
                        .select_related("approved_revision", "person").order_by("pk"))
        assert len(listings) == 101 and not Favorite.objects.exists()
        user = User.objects.get(username="fixture-v1-visitor")
        other = User.objects.get(username="fixture-v1-individual")
        client, other_client = _client(user), _client(other)
        foreign = Favorite.objects.create(user=other, listing=listings[-1])
        versions = {listing.pk: [(language, absolute("listing_detail", language, args=[listing.pk]))
                                for language in listing_languages(listing.approved_revision)]
                    for listing in listings}
        common = {"callbacks": callbacks, "patterns": patterns, "hashes": hashes, "rows": rows}
        for count in [0, 1, 10]:
            _set_candidates(listings, count)
            own = _own_favorites(user, listings, count)
            for language in ["es", "en"]:
                translation.activate(language)
                check = _favorite_check(user, own, listings, {listing.pk for listing in listings[:count]}, foreign=foreign)
                _pair(client, reverse("favorites"), **common, state=f"small_{count}",
                      surface="favorites", language=language, check=check)
            translation.activate("es")
            check = _xml_check(listings[:count], versions) if count else _status_check(404)
            _pair(public, reverse("sitemap_listings", args=[1]), **common,
                  state=f"small_{count}", surface="sitemap_listings", language="neutral", check=check)
        _set_candidates(listings, 100)
        own = _own_favorites(user, listings, 100)
        hidden = next(listing for listing in listings if listing.pk == own[-1].listing_id)

        def native_101_controls(state):
            _set_candidates(listings, 101)
            translation.activate("es")
            _pair(public, reverse("sitemap_index"), **common, state=state, surface="sitemap_index",
                  language="neutral", check=_index_check(settings, 101), page=0)
            _pair(public, reverse("sitemap_listings", args=[2]), **common, state=state,
                  surface="sitemap_listings", language="neutral", check=_xml_check(listings[100:], versions), page=2)
            _set_candidates(listings, 100)

        native_101_controls("normal_101")
        for state in ["normal", "one_revoked"]:
            if state == "one_revoked":
                person = Person.objects.get(pk=hidden.person_id)
                person.consent_revoked_at = timezone.now()
                person.save(update_fields=["consent_revoked_at"])
                assert Favorite.objects.filter(pk=own[-1].pk, user=user, listing=hidden).exists()
                assert Listing.objects.filter(status="published").count() == 100
            visible = {listing.pk for listing in listings[:100]
                       if state == "normal" or listing.pk != hidden.pk}
            for language in ["es", "en"]:
                translation.activate(language)
                check = _favorite_check(user, own, listings, visible,
                                        hidden=hidden if state == "one_revoked" else None, foreign=foreign)
                _pair(client, reverse("favorites"), **common, state=state, surface="favorites",
                      language=language, check=check, repetitions=6, category="target")
            translation.activate("es")
            _pair(public, reverse("sitemap_listings", args=[1]), **common, state=state,
                  surface="sitemap_listings", language="neutral", repetitions=6, category="target",
                  check=_xml_check(listings[:100], versions, hidden.pk if state == "one_revoked" else None))
        native_101_controls("one_revoked_101")
        for language in ["es", "en"]:
            translation.activate(language)
            _pair(Client(), reverse("favorites"), **common, state="anonymous", surface="favorites",
                  language=language, check=_status_check(302))
            _pair(other_client, reverse("favorites"), **common, state="foreign_actor_placeholder",
                  surface="favorites", language=language,
                  check=_favorite_check(other, [foreign], listings, set(), hidden=listings[-1]))
        translation.activate("es")
        for label, path in [
            ("index_query", reverse("sitemap_index") + "?q=N08A2_PRIVATE_QUERY"),
            ("listings_query", reverse("sitemap_listings", args=[1]) + "?q=N08A2_PRIVATE_QUERY"),
            ("page_zero", reverse("sitemap_listings", args=[0])),
            ("page_out_of_range", reverse("sitemap_listings", args=[3])),
        ]:
            surface = "sitemap_index" if label == "index_query" else "sitemap_listings"
            _pair(public, path, **common, state=label, surface=surface, language="neutral", check=_status_check(404))
        assert sum(row["category"] == "target" for row in rows) == 72
        assert sum(row["category"] == "control" for row in rows) == 42
        assert len(rows) == 114
        metadata["readonly_snapshots_verified"] = True


@pytest.mark.parametrize("language", ["es", "en"])
def test_secondary_surface_null_and_foreign_revision_pair(request, settings, record_property, language):
    _guard(request, settings)
    callbacks, hashes = _sources()
    patterns = _patterns()
    rows = []
    metadata = {"baseline_commit": BASELINE_COMMIT, "source_sha256": hashes,
                "language": language, "planned_gets": 2, "populate_calls": 0,
                "preparation": "native directory plus two explicit invalid synthetic listing pointers",
                "readonly_models": ["Favorite", "Listing", "Revision", "Person"]}
    with _report(record_property, "secondary_batch_pair_negative", rows, metadata):
        request.getfixturevalue("directory")
        owner = Listing.objects.select_related("approved_revision", "person").get(
            person__individual__username="fixture-v1-individual")
        bad = []
        for label in ["null", "foreign"]:
            subject = User.objects.create_user(username=f"n08a2-{label}", email=f"n08a2-{label}@example.invalid")
            person = Person.objects.create(individual=subject, subject=subject, alias="Synthetic invalid pointer")
            bad.append(Listing.objects.create(person=person, status="published", published_at=timezone.now(),
                                              expires_at=timezone.now() + timedelta(days=30),
                                              approved_revision=owner.approved_revision if label == "foreign" else None))
        assert not publicly_visible(bad[0]) and not publicly_visible(bad[1]) and publicly_visible(owner)
        user = User.objects.get(username="fixture-v1-visitor")
        assert not Favorite.objects.filter(user=user).exists()
        own = _own_favorites(user, [*bad, owner], 3)
        translation.activate(language)
        _pair(_client(user), reverse("favorites"), callbacks=callbacks, patterns=patterns, hashes=hashes,
              rows=rows, state="null_and_foreign_revision", surface="favorites", language=language,
              check=_favorite_check(user, own, [*bad, owner], {owner.pk}))
        assert len(rows) == 2
        assert all(row["normalization"]["csrf_hidden_values"] == 3 for row in rows)
        metadata["readonly_snapshots_verified"] = True
