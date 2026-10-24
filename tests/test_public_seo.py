"""Metadata from public approved content; private and filtered pages stay unindexed."""

import shutil
from html.parser import HTMLParser

import pytest
from django.template.loader import render_to_string
from playwright.sync_api import sync_playwright
from test_discovery import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def pub_client(request):
    return request.getfixturevalue("directory")


class Head(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.links = []
        self.language = None
        self.meta = {}
        self.title = ""
        self.in_title = False
        self.in_head = False
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "html":
            self.language = data.get("lang")
        if tag == "head":
            self.in_head = True
        if not self.in_head:
            return
        if tag == "title":
            self.in_title = True
        if tag == "link":
            self.links.append(data)
        if tag == "meta" and "name" in data:
            self.meta[data["name"]] = data.get("content", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "head":
            self.in_head = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def canonical(head):
    return [link["href"] for link in head.links if link.get("rel") == "canonical"]


@pytest.mark.parametrize("language", ["es", "en"])
def test_public_metadata_localization_filters_privacy_and_origin(pub_client, settings, language):
    settings.PUBLIC_ORIGIN = "https://seo.example.invalid"
    clean = pub_client.get(f"/{language}/")
    head = Head(clean.content.decode())
    assert head.language == language
    assert canonical(head) == [f"https://seo.example.invalid/{language}/"]
    assert {link["hreflang"] for link in head.links if link.get("rel") == "alternate"} == {
        "es",
        "en",
    }
    assert {
        link["hreflang"]: link["href"] for link in head.links if link.get("rel") == "alternate"
    } == {lang: f"https://seo.example.invalid/{lang}/" for lang in ["es", "en"]}
    assert head.meta["robots"] == "noindex,nofollow"  # Development remains private.
    assert ("Find romantic dating profiles" if language == "en" else "Encuentra perfiles para citas románticas") in head.title
    for query in [
        {"q": "private-contact@example.invalid"},
        {"unknown": "tracking-only"},
        {"page": "-1"},
    ]:
        response = pub_client.get(f"/{language}/", query)
        meta = Head(response.content.decode())
        assert not canonical(meta) and "noindex" in meta.meta["robots"]
        assert "private-contact@example.invalid" not in meta.title + meta.meta["description"]
    private = Head(pub_client.get(f"/{language}/account/login/").content.decode())
    assert private.language == language
    assert not canonical(private) and private.meta["robots"] == "noindex,nofollow"
    assert private.meta["description"] == (
        "Personal profiles of adults seeking romantic dates in Spain."
        if language == "en"
        else "Perfiles personales de personas adultas que buscan citas románticas en España."
    )
    # Explicit template branch verification; not production verification of fixtures.
    rendered = Head(
        render_to_string(
            "base.html",
            {"seo": clean.context["seo"], "development": False},
            request=clean.wsgi_request,
        )
    )
    assert "robots" not in rendered.meta


def test_only_available_listing_languages_are_indexable_and_pending_content_excluded(
    pub_client, settings
):
    settings.PUBLIC_ORIGIN = "https://seo.example.invalid"
    listing = Person.objects.get(individual__username="fixture-v1-individual").listing
    revision = listing.approved_revision
    revision.content_language = "es"
    revision.description_alternative = ""
    revision.save(update_fields=["content_language", "description_alternative"])
    Revision.objects.create(
        listing=listing,
        manager_version=listing.person.manager_version,
        title="PRIVATE PENDING SEO TITLE",
        description="PRIVATE PENDING SEO DESCRIPTION",
    )
    response = pub_client.get(f"/en/listing/{listing.pk}/")
    assert response.status_code == 200
    head = Head(response.content.decode())
    assert head.language == "en"
    assert canonical(head) == [f"https://seo.example.invalid/es/listing/{listing.pk}/"]
    assert [x["hreflang"] for x in head.links if x.get("rel") == "alternate"] == ["es"]
    assert "PRIVATE PENDING" not in head.title + head.meta["description"]
    rendered = Head(
        render_to_string(
            "base.html",
            {"seo": response.context["seo"], "development": False},
            request=response.wsgi_request,
        )
    )
    assert rendered.meta["robots"] == "noindex,follow"
    revision.description_alternative = (
        "English public translated description available for this synthetic profile."
    )
    revision.save(update_fields=["description_alternative"])
    translated = pub_client.get(f"/en/listing/{listing.pk}/")
    head = Head(translated.content.decode())
    assert canonical(head) == [f"https://seo.example.invalid/en/listing/{listing.pk}/"]
    assert head.meta["description"] == revision.description_alternative
    assert len([x for x in head.links if x.get("rel") == "alternate"]) == 2
    listing.status = "paused"
    listing.save(update_fields=["status"])
    hidden = pub_client.get(f"/en/listing/{listing.pk}/")
    assert hidden.status_code == 404 and not canonical(Head(hidden.content.decode()))


def test_browser_metadata_navigation_and_retirement(live_server, pub_client, settings):
    settings.PUBLIC_ORIGIN = "https://seo.example.invalid"
    listing = Person.objects.get(individual__username="fixture-v1-individual").listing
    title = listing.approved_revision.title
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/")
            assert "Find romantic dating profiles" in page.title()
            assert page.locator("html").get_attribute("lang") == "en"
            assert (
                page.locator("link[rel=canonical]").get_attribute("href")
                == "https://seo.example.invalid/en/"
            )
            page.goto(live_server.url + f"/es/listing/{listing.pk}/")
            assert title in page.title()
            assert page.locator("html").get_attribute("lang") == "es"
            assert page.locator("meta[name=robots]").get_attribute("content") == "noindex,nofollow"
            from concurrent.futures import ThreadPoolExecutor

            from django.db import connections

            from apps.listings.models import Listing

            def retire():
                try:
                    Listing.objects.filter(pk=listing.pk).update(status="paused")
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(retire).result(timeout=10)
            assert page.reload().status == 404
            assert page.locator("link[rel=canonical]").count() == 0
        finally:
            browser.close()
