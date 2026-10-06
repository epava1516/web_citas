import shutil
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
from xml.etree.ElementTree import fromstring

import pytest
from django.db import connections
from django.utils import timezone
from playwright.sync_api import sync_playwright
from test_discovery import directory, photo_environment  # noqa: F401

from apps.core import sitemaps
from apps.core.models import Person
from apps.listings.models import Listing, Revision

pytestmark = pytest.mark.django_db(transaction=True)
NS = {"s": sitemaps.NS, "h": sitemaps.XHTML}


@pytest.fixture
def public_client(request):
    return request.getfixturevalue("directory")


def documents(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    return [
        urlsplit(node.text).path
        for node in fromstring(response.content).findall("s:sitemap/s:loc", NS)
    ]


def urls(client):
    rows = []
    for path in documents(client):
        response = client.get(path)
        assert response.status_code == 200
        rows.extend(fromstring(response.content).findall("s:url", NS))
    return rows


def test_robots_policy_branches_and_empty_sitemap(client, settings):
    settings.PUBLIC_ORIGIN = "https://seo.example.invalid"
    dev = client.get("/robots.txt")
    assert dev.status_code == 200 and "Disallow: /\n" in dev.content.decode()
    assert "noindex" in dev["X-Robots-Tag"]
    assert documents(client) == ["/sitemaps/directory.xml"]
    assert client.get("/sitemaps/listings/1.xml").status_code == 404
    assert client.get("/sitemap.xml", {"q": "private-query"}).status_code == 404
    assert client.post("/robots.txt").status_code == 405
    # Policy branch only; no production identity/provider verification with fixtures.
    settings.PRODUCTION = True
    text = client.get("/robots.txt").content.decode()
    assert "Disallow: /es/account/" in text and "Disallow: /en/moderation/" in text
    assert "Sitemap: https://seo.example.invalid/sitemap.xml" in text
    assert "Disallow: /\n" not in text


def test_sitemap_languages_privacy_page_boundaries_and_withdrawal(
    public_client, settings, monkeypatch
):
    settings.PUBLIC_ORIGIN = "https://seo.example.invalid"
    monkeypatch.setattr(sitemaps, "PAGE_SIZE", 1)
    listing = Person.objects.get(individual__username="fixture-v1-individual").listing
    revision = listing.approved_revision
    revision.content_language = "es"
    revision.description_alternative = ""
    revision.save(update_fields=["content_language", "description_alternative"])
    Revision.objects.create(
        listing=listing,
        manager_version=listing.person.manager_version,
        title="PRIVATE PENDING",
        description="PRIVATE DESCRIPTION",
    )
    paths = documents(public_client)
    assert len(paths) == 3  # Directory plus two candidate pages; bounded before visibility.
    rows = urls(public_client)
    locations = [row.find("s:loc", NS).text for row in rows]
    own = f"https://seo.example.invalid/es/listing/{listing.pk}/"
    assert own in locations and own.replace("/es/", "/en/") not in locations
    assert all(
        location.startswith("https://seo.example.invalid/") and "?" not in location
        for location in locations
    )
    response = public_client.get(paths[-1])
    assert response["Cache-Control"] == "no-store" and "noindex" in response["X-Robots-Tag"]
    assert b"PRIVATE" not in response.content and b"@" not in response.content
    assert public_client.get("/sitemaps/listings/0.xml").status_code == 404
    assert public_client.get("/sitemaps/listings/999999999.xml").status_code == 404
    revision.description_alternative = "Real alternative English text for this synthetic profile."
    revision.save(update_fields=["description_alternative"])
    rows = urls(public_client)
    own_rows = [r for r in rows if str(listing.pk) in r.find("s:loc", NS).text]
    assert len(own_rows) == 2
    assert all(
        {x.attrib["hreflang"] for x in r.findall("h:link", NS)} == {"es", "en"} for r in own_rows
    )
    listing.person.consent_revoked_at = timezone.now()
    listing.person.save(update_fields=["consent_revoked_at"])
    assert all(str(listing.pk) not in r.find("s:loc", NS).text for r in urls(public_client))
    Listing.objects.update(status="paused")
    assert documents(public_client) == ["/sitemaps/directory.xml"]


def test_browser_follows_sitemap_to_public_page_and_observes_retirement(
    live_server, public_client, settings
):
    settings.PUBLIC_ORIGIN = live_server.url
    listing = Person.objects.get(individual__username="fixture-v1-individual").listing
    revision = listing.approved_revision
    revision.content_language = "es"
    revision.description_alternative = ""
    revision.save(update_fields=["content_language", "description_alternative"])
    location = f"{live_server.url}/es/listing/{listing.pk}/"

    def retire():
        try:
            Listing.objects.filter(pk=listing.pk).update(status="paused")
        finally:
            connections.close_all()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            assert page.goto(live_server.url + "/sitemap.xml").status == 200
            response = page.request.get(live_server.url + "/sitemaps/listings/1.xml")
            assert location in [
                n.text for n in fromstring(response.body()).findall("s:url/s:loc", NS)
            ]
            assert page.goto(location).status == 200
            assert page.locator("link[rel=canonical]").get_attribute("href") == location
            with ThreadPoolExecutor(max_workers=1) as pool:
                pool.submit(retire).result(timeout=10)
            fresh = page.request.get(live_server.url + "/sitemaps/listings/1.xml")
            assert location not in fresh.text()
            assert page.goto(location).status == 404
        finally:
            browser.close()
