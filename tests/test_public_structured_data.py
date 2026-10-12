"""Public JSON-LD mirrors approved content and stays inert under the existing CSP."""

import json
import shutil
from html.parser import HTMLParser

import pytest
from django.templatetags.static import static
from django.utils import timezone
from playwright.sync_api import sync_playwright
from test_discovery import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Revision

pytestmark = pytest.mark.django_db(transaction=True)


class Documents(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.documents = []
        self.active = None
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type") == "application/ld+json":
            self.active = ""

    def handle_data(self, data):
        if self.active is not None:
            self.active += data

    def handle_endtag(self, tag):
        if tag == "script" and self.active is not None:
            self.documents.append(json.loads(self.active))
            self.active = None


@pytest.fixture
def pub_client(request):
    return request.getfixturevalue("directory")


def listing():
    return Person.objects.get(individual__username="fixture-v1-individual").listing


@pytest.mark.parametrize("language", ["es", "en"])
def test_public_jsonld_uses_approved_canonical_language_and_public_alias(pub_client, settings, language):
    settings.PUBLIC_ORIGIN = "https://structured.example.invalid"
    item = listing()
    item.person.alias = '</script><script>window.SEO_PWNED=true</script>& synthetic'
    item.person.save(update_fields=["alias"])
    Revision.objects.create(
        listing=item, manager_version=item.person.manager_version,
        title="PRIVATE PENDING MARKUP", description="PRIVATE PENDING DESCRIPTION",
    )
    response = pub_client.get(f"/{language}/listing/{item.pk}/", {"tracking": "PRIVATE QUERY"})
    assert response.status_code == 200
    documents = Documents(response.content.decode()).documents
    assert len(documents) == 1
    data = documents[0]
    assert set(data) == {"@context", "@type", "url", "name", "description", "inLanguage", "about"}
    assert data["@context"] == "https://schema.org" and data["@type"] == "WebPage"
    assert data["inLanguage"] == language
    assert data["url"] == f"https://structured.example.invalid/{language}/listing/{item.pk}/"
    assert data["name"] == response.context["seo"]["title"]
    assert data["description"] == response.context["seo"]["description"]
    assert data["about"] == {"@type": "Person", "name": item.person.alias}
    assert "PRIVATE" not in json.dumps(data)
    assert item.approved_revision.phone not in json.dumps(data)
    assert 'script-src \'self\'' in response["Content-Security-Policy"]
    assert "unsafe-inline" not in response["Content-Security-Policy"]
    assert b"\\u003C/script\\u003E" in response.content


def test_untranslated_fallback_catalog_and_private_routes_do_not_emit_jsonld(pub_client):
    item = listing()
    revision = item.approved_revision
    revision.content_language = "es"
    revision.description_alternative = ""
    revision.save(update_fields=["content_language", "description_alternative"])
    for path in [f"/en/listing/{item.pk}/", "/es/", "/es/?q=private", "/es/account/login/"]:
        response = pub_client.get(path)
        assert response.status_code == 200
        assert not Documents(response.content.decode()).documents
    assert len(Documents(pub_client.get(f"/es/listing/{item.pk}/").content.decode()).documents) == 1


@pytest.mark.parametrize("change", ["paused", "expired", "consent"])
def test_hidden_listing_does_not_publish_jsonld(pub_client, change):
    item = listing()
    if change == "paused":
        item.status = "paused"
        item.save(update_fields=["status"])
    elif change == "expired":
        item.expires_at = timezone.now()
        item.save(update_fields=["expires_at"])
    else:
        item.person.consent_revoked_at = timezone.now()
        item.person.save(update_fields=["consent_revoked_at"])
    response = pub_client.get(f"/es/listing/{item.pk}/")
    assert response.status_code == 404 and not Documents(response.content.decode()).documents


@pytest.mark.parametrize("language", ["es", "en"])
def test_browser_jsonld_remains_inert_and_readable_under_csp(live_server, pub_client, language):
    item = listing()
    alias = '</script><script>window.SEO_PWNED=true</script>& synthetic'
    item.person.alias = alias
    item.person.save(update_fields=["alias"])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.add_init_script("window.cspViolations=[]; document.addEventListener('securitypolicyviolation', e => window.cspViolations.push(e.effectiveDirective));")
            response = page.goto(live_server.url + f"/{language}/listing/{item.pk}/")
            assert response.status == 200
            assert page.locator('script[type="application/ld+json"]').count() == 1
            data = json.loads(page.locator('script[type="application/ld+json"]').text_content())
            assert data["about"]["name"] == alias and data["inLanguage"] == language
            assert page.evaluate("window.SEO_PWNED === undefined")
            assert page.evaluate("window.cspViolations") == []
            executable = page.locator('script:not([type="application/ld+json"])')
            # The base template includes the local form error accessibility helper.
            # Permit precisely that asset; injected inline or extra scripts fail.
            assert executable.count() == 1
            assert executable.get_attribute("src") == static("form-errors.js")
            assert executable.get_attribute("defer") is not None
            assert executable.text_content().strip() == ""
        finally:
            browser.close()
