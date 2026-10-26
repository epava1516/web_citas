"""Explicit finite Client references for secondary surfaces; synthetic preparation only."""

import json
import os
import time
from datetime import timedelta
from math import ceil
from pathlib import Path
from xml.etree.ElementTree import fromstring

import pytest
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone, translation
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import LegalDocument, Person, User
from apps.listings.models import Favorite, Listing, Revision
from apps.listings.seo import absolute, listing_languages
from scripts.synthetic_load_dataset import populate

pytestmark = pytest.mark.django_db(transaction=True)
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"
NS = {"s": SITEMAP_NS, "h": XHTML_NS}
SCOPE = (
    "Finite synthetic Django Client.GET reference: first plus5 subsequent requests per state/page; "
    "wall/processCPU and connection CaptureQueriesContext SQL/count; rendered body materialized; "
    "preparation/oracles outside clocks. Root global request observer is separate, never summed. "
    "No budget, gain, p95, browser, worker, provider, CSRF or production/legal compliance claim."
)


def _guard(request, settings):
    explicit = any(Path(str(arg).split("::")[0]).resolve() == Path(__file__).resolve()
                   for arg in request.config.args)
    if not explicit:
        pytest.skip("Explicit finite secondary surface diagnostic only")
    assert not os.environ.get("PYTEST_XDIST_WORKER"), "Reference requires serial execution"
    assert connection.vendor == "postgresql" and not settings.PRODUCTION
    assert connection.settings_dict["NAME"].startswith("test_promotion_gate_")
    previous_language = translation.get_language()
    request.addfinalizer(lambda: translation.activate(previous_language))


def _six_gets(client, path, rows, *, surface, state, language, page, check):
    for ordinal in range(6):
        with CaptureQueriesContext(connection) as queries:
            cpu_started = time.process_time()
            started = time.perf_counter()
            response = client.get(path)
            body = response.content
            wall = time.perf_counter() - started
            cpu = time.process_time() - cpu_started
        # Keep all queryset/context/XML/link assertions out of the timed interval.
        check(response, body)
        rows.append({
            "surface": surface, "state": state, "language": language, "page": page,
            "ordinal": ordinal, "wall_seconds": wall, "cpu_seconds": cpu,
            "sql_queries": len(queries),
            "sql_execute_seconds": sum(float(query["time"]) for query in queries),
            "response_bytes": len(body), "status": response.status_code,
            "route_name": response.resolver_match.view_name,
            "observed_cache_control": response.get("Cache-Control"),
            "observed_content_language": response.get("Content-Language"),
            "response_language": response.wsgi_request.LANGUAGE_CODE,
        })


def _language(response, language):
    assert response.wsgi_request.LANGUAGE_CODE == language
    assert response["Content-Language"] == language


def _record(record_property, rows, setup, counts):
    record_property("secondary_surface_samples", json.dumps({
        "rows": rows, "scope": SCOPE, "setup_descriptor": setup, "population_counts": counts,
    }, sort_keys=True))


def _favorite_snapshot():
    return list(Favorite.objects.order_by("pk").values_list("pk", "user_id", "listing_id", "created_at"))


def test_favorites_secondary_surface_reference(request, settings, record_property):
    _guard(request, settings)
    request.getfixturevalue("directory")
    population = populate(101)
    assert population["published"] == 101 and population["shared_synthetic_photo_fixture"]
    listings = list(Listing.objects.filter(status="published")
                    .select_related("approved_revision", "person").order_by("pk"))
    assert len(listings) == 101 and not Favorite.objects.exists()
    user = User.objects.get(username="fixture-v1-visitor")
    other = User.objects.get(username="fixture-v1-individual")
    client = Client()
    client.force_login(user)
    foreign_listing = listings[-1]
    foreign = Favorite.objects.create(user=other, listing=foreign_listing)
    own, rows = [], []
    hidden = None
    stamp = timezone.now()

    def observe(size, state):
        # The oracle comes from the records created here, not the view queryset.
        ordered = sorted(own, key=lambda item: (item.created_at, item.pk), reverse=True)
        snapshot = _favorite_snapshot()
        for language in ["es", "en"]:
            translation.activate(language)  # Fixture /es/ requests can replace the active language.
            route = reverse("favorites")
            detail_links = {
                listing.pk: f'href="{reverse("listing_detail", args=[listing.pk])}"'.encode()
                for listing in listings
            }
            remove_actions = {
                favorite.pk: f'action="{reverse("favorite_remove", args=[favorite.pk])}"'.encode()
                for favorite in [*own, foreign]
            }
            for page_number in range(1, max(1, ceil(size / 24)) + 1):
                expected = ordered[(page_number - 1) * 24:page_number * 24]
                expected_ids = [item.pk for item in expected]
                visible_ids = {item.listing_id for item in expected
                               if hidden is None or item.listing_id != hidden.pk}

                def check(response, body):
                    assert response.status_code == 200
                    assert response.resolver_match.view_name == "favorites"
                    _language(response, language)
                    assert response["Cache-Control"] == "private, no-store"
                    page = response.context["page"]
                    entries = list(response.context["entries"])
                    assert page.number == page_number and page.paginator.per_page == 24
                    assert page.paginator.count == size
                    assert page.paginator.num_pages == max(1, ceil(size / 24))
                    assert [entry["favorite"].pk for entry in entries] == expected_ids
                    assert [item.pk for item in list(page.object_list)] == expected_ids
                    assert all(entry["favorite"].user_id == user.pk for entry in entries)
                    assert {entry["favorite"].listing_id for entry in entries if entry["visible"]} == visible_ids
                    for listing in listings:
                        assert (detail_links[listing.pk] in body) == (listing.pk in visible_ids)
                    for favorite in [*own, foreign]:
                        assert (remove_actions[favorite.pk] in body) == (favorite.pk in expected_ids)
                    if hidden is not None:
                        for private in [hidden.approved_revision.title,
                                        hidden.approved_revision.phone, str(hidden.pk)]:
                            assert private.encode() not in body
                    assert foreign_listing.approved_revision.title.encode() not in body

                _six_gets(client, route + f"?page={page_number}", rows, surface="favorites",
                          state=state, language=language, page=page_number, check=check)
            assert Client().get(route).status_code == 302
        assert _favorite_snapshot() == snapshot

    for size in [0, 1, 10, 100]:
        added = Favorite.objects.bulk_create([
            Favorite(user=user, listing=listing) for listing in listings[len(own):size]
        ])
        for index, favorite in enumerate(added, start=len(own)):
            favorite.created_at = stamp + timedelta(seconds=index)
        if added:
            Favorite.objects.bulk_update(added, ["created_at"])
        own.extend(added)
        observe(size, f"own_{size}")
    first = max(own, key=lambda item: (item.created_at, item.pk))
    hidden = next(listing for listing in listings if listing.pk == first.listing_id)
    person = Person.objects.get(pk=hidden.person_id)
    person.consent_revoked_at = timezone.now()
    person.save(update_fields=["consent_revoked_at"])  # Native invalidation/signals retained.
    assert Favorite.objects.filter(pk=first.pk, user=user, listing=hidden).exists()
    observe(100, "own_100_one_revoked")
    _record(record_property, rows, {
        "directory_fixture_calls": 1, "populate_calls": 1,
        "shared_synthetic_photo_fixture": True, "preparation": "native seed plus bulk synthetic clones/favorites; eager fixtures",
        "favorite_get_snapshot_unchanged": True, "native_page_size": 24,
    }, {"published_pre_revocation": 101, "own_favorite_cohorts": [0, 1, 10, 100],
        "foreign_favorites": 1, "retained_unavailable_favorites": 1})


def _xml_header(response, root_tag):
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert response["Content-Type"] == "application/xml"
    root = fromstring(response.content)
    assert root.tag == f"{{{SITEMAP_NS}}}{root_tag}"
    return root


def _assert_urlset(response, expected):
    root = _xml_header(response, "urlset")
    nodes = list(root)
    assert [node.tag for node in nodes] == [f"{{{SITEMAP_NS}}}url"] * len(expected)
    actual = []
    for node in nodes:
        location = node.find("s:loc", NS)
        assert location is not None and not location.attrib
        alternates = node.findall("h:link", NS)
        assert len(list(node)) == 1 + len(alternates)
        assert all(link.attrib.get("rel") == "alternate" for link in alternates)
        actual.append((location.text, [link.attrib for link in alternates]))
    assert actual == expected
    assert all("?" not in location for location, _ in actual)


def _versions_oracle(versions):
    alternates = [{"rel": "alternate", "hreflang": language, "href": address}
                  for language, address in versions]
    return [(address, alternates) for _, address in versions]


def test_sitemap_secondary_surface_reference(request, settings, record_property):
    _guard(request, settings)
    client = request.getfixturevalue("directory")
    population = populate(101)
    assert population["published"] == 101 and population["shared_synthetic_photo_fixture"]
    settings.PUBLIC_ORIGIN = "https://secondary-reference.example.invalid"
    listings = list(Listing.objects.filter(status="published")
                    .select_related("approved_revision", "person").order_by("pk"))
    assert len(listings) == 101
    # Deliberate private draft lure, never a sitemap source.
    Revision.objects.create(listing=listings[0], manager_version=listings[0].person.manager_version,
                            title="N08A PRIVATE DRAFT TITLE", description="N08A PRIVATE DESCRIPTION")
    versions = {
        listing.pk: [(language, absolute("listing_detail", language, args=[listing.pk]))
                     for language in listing_languages(listing.approved_revision)]
        for listing in listings
    }
    translation.activate("es")
    rows = []
    directory_path = reverse("sitemap_directory")
    directory_expected = _versions_oracle([(language, absolute("home", language))
                                          for language in ["es", "en"]])

    def check_directory(response, body):
        assert response.resolver_match.view_name == "sitemap_directory"
        _assert_urlset(response, directory_expected)

    _six_gets(client, directory_path, rows, surface="sitemap_directory", state="directory",
              language="neutral", page=0, check=check_directory)

    def observe(selected, state, hidden_id=None):
        candidate_pages = ceil(len(selected) / 100)
        index_expected = [settings.PUBLIC_ORIGIN + directory_path] + [
            settings.PUBLIC_ORIGIN + reverse("sitemap_listings", args=[page])
            for page in range(1, candidate_pages + 1)
        ]

        def check_index(response, body):
            assert response.resolver_match.view_name == "sitemap_index"
            root = _xml_header(response, "sitemapindex")
            assert [node.tag for node in root] == [f"{{{SITEMAP_NS}}}sitemap"] * len(index_expected)
            assert [node.text for node in root.findall("s:sitemap/s:loc", NS)] == index_expected
            assert all(len(list(node)) == 1 for node in root)

        _six_gets(client, reverse("sitemap_index"), rows, surface="sitemap_index", state=state,
                  language="neutral", page=0, check=check_index)
        for page_number in range(1, candidate_pages + 1):
            expected = [row
                        for listing in selected[(page_number - 1) * 100:page_number * 100]
                        if listing.pk != hidden_id
                        for row in _versions_oracle(versions[listing.pk])]

            def check_listing(response, body):
                assert response.resolver_match.view_name == "sitemap_listings"
                _assert_urlset(response, expected)
                assert b"N08A PRIVATE" not in body
                if hidden_id is not None:
                    assert str(hidden_id).encode() not in body

            _six_gets(client, reverse("sitemap_listings", args=[page_number]), rows,
                      surface="sitemap_listings", state=state, language="neutral",
                      page=page_number, check=check_listing)
        if not selected:
            assert client.get(reverse("sitemap_listings", args=[1])).status_code == 404

    for count in [0, 1, 10, 100, 101]:
        # Fixture cohort changes use normal ORM writes and actual database invalidation.
        Listing.objects.filter(pk__in=[listing.pk for listing in listings]).update(status="paused")
        Listing.objects.filter(pk__in=[listing.pk for listing in listings[:count]]).update(status="published")
        observe(listings[:count], f"candidates_{count}")
    hidden = listings[0]
    person = Person.objects.get(pk=hidden.person_id)
    person.consent_revoked_at = timezone.now()
    person.save(update_fields=["consent_revoked_at"])
    hidden.refresh_from_db()
    assert hidden.status == "published" and hidden.approved_revision.status == "approved"
    assert Listing.objects.filter(status="published").count() == 101
    observe(listings, "candidates_101_one_revoked", hidden.pk)
    assert client.get(absolute("listing_detail", "es", args=[hidden.pk])).status_code == 404
    for path in [reverse("sitemap_index"), directory_path,
                 reverse("sitemap_listings", args=[1]), reverse("sitemap_listings", args=[2])]:
        denied = client.get(path, {"q": "N08A_PRIVATE_QUERY_MARKER"})
        assert denied.status_code == 404 and b"N08A_PRIVATE_QUERY_MARKER" not in denied.content
    assert client.get(reverse("sitemap_listings", args=[0])).status_code == 404
    assert client.get(reverse("sitemap_listings", args=[3])).status_code == 404
    _record(record_property, rows, {
        "directory_fixture_calls": 1, "populate_calls": 1,
        "shared_synthetic_photo_fixture": True, "preparation": "native seed plus bulk synthetic clones; eager fixtures",
        "native_page_size": 100, "directory_repetitions": 6,
        "candidate_membership_oracle": "explicit fixture cohort IDs, ordered by UUID; visibility revoked through Person.save",
    }, {"candidate_cohorts": [0, 1, 10, 100, 101], "candidate_count_after_revocation": 101,
        "unavailable_candidates": 1, "private_draft_lures": 1})


def test_legal_secondary_surface_reference(request, settings, record_property):
    _guard(request, settings)
    request.getfixturevalue("photo_environment")  # Eager native signal callbacks; no seed or providers.
    assert not LegalDocument.objects.exists(), "Legal reference needs an empty transactional database"
    stamp = timezone.now()
    documents = {}
    for language in ["es", "en"]:
        documents[language] = LegalDocument.objects.bulk_create([
            LegalDocument(slug=f"n08a-{language}-{index:03d}", version="synthetic-v1",
                          language=language, title=f"Synthetic document {language} {index:03d}",
                          body=f"Synthetic reference prose {language} {index:03d}.",
                          published_at=stamp, active=False)
            for index in range(100)
        ])
    inactive = LegalDocument.objects.bulk_create([
        LegalDocument(slug=f"n08a-inactive-{language}", version="synthetic-inactive",
                      language=language, title=f"Inactive lure {language}", body="Inactive synthetic prose.",
                      published_at=stamp, active=False) for language in ["es", "en"]
    ])
    client, rows = Client(), []
    for count in [0, 1, 10, 100]:
        for language in ["es", "en"]:
            LegalDocument.objects.filter(pk__in=[document.pk for document in documents[language][:count]]).update(active=True)
        snapshot = list(LegalDocument.objects.order_by("pk").values())
        for language in ["es", "en"]:
            translation.activate(language)
            expected = documents[language][:count]
            expected_ids = [document.pk for document in expected]
            all_documents = documents["es"] + documents["en"] + inactive
            links = {document.pk: f'href="{reverse("legal_document", args=[document.slug])}"'.encode()
                     for document in all_documents}

            def check_index(response, body):
                assert response.status_code == 200 and response.resolver_match.view_name == "legal_index"
                _language(response, language)
                shown = list(response.context["documents"])
                assert [document.pk for document in shown] == expected_ids
                assert [document.slug for document in shown] == sorted(document.slug for document in expected)
                for document in all_documents:
                    assert (links[document.pk] in body) == (document.pk in expected_ids)
                for document in expected:
                    assert document.title.encode() in body and document.version.encode() in body

            _six_gets(client, reverse("legal_index"), rows, surface="legal_index",
                      state=f"active_per_language_{count}", language=language, page=0, check=check_index)
            if count == 100:
                document = expected[0]

                def check_document(response, body):
                    assert response.status_code == 200 and response.resolver_match.view_name == "legal_document"
                    _language(response, language)
                    actual = response.context["document"]
                    assert actual.pk == document.pk and actual.language == language and actual.active
                    for text in [document.body, document.version, document.title]:
                        assert text.encode() in body

                _six_gets(client, reverse("legal_document", args=[document.slug]), rows,
                          surface="legal_document", state="active_per_language_100", language=language,
                          page=0, check=check_document)
                other_language = "en" if language == "es" else "es"
                for slug in [f"n08a-inactive-{language}", documents[other_language][0].slug]:
                    assert client.get(reverse("legal_document", args=[slug])).status_code == 404
        assert list(LegalDocument.objects.order_by("pk").values()) == snapshot
    _record(record_property, rows, {
        "legal_GET_snapshot_unchanged": True,
        "directory_fixture_calls": 0, "populate_calls": 0,
        "preparation": "own synthetic legal rows only; no bootstrap, legal seed or current-content claim",
        "legal_scope": "index selection and detail rendering; not legal correctness or compliance",
    }, {"active_cohorts_per_language": [0, 1, 10, 100], "document_rows": 202,
        "inactive_lures": 2, "languages": 2})
