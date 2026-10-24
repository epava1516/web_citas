import os
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory, multipage_directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401


@pytest.mark.django_db(transaction=True)
def test_mobile_search_service_modes_language_and_public_card(live_server, request, settings):
    settings.DEBUG = True
    request.getfixturevalue("directory")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/es/")
            page.locator("[name=q]").fill("photography")
            for name in ["category", "service", "services_mode", "reception", "travel"]:
                expect(page.locator(f'[name="{name}"]')).to_have_count(0)
            page.locator("[name=language]").select_option(["en", "fr"])
            page.locator("[name=day]").select_option(["1"])
            page.get_by_role("button", name="Buscar", exact=True).click()
            expect(page.get_by_text("2 resultados", exact=True)).to_be_visible()
            page.reload()
            expect(page.locator("[name=q]")).to_have_value("photography")
            expect(page.locator("[name=language]")).to_have_values(["en", "fr"])
            expect(page.locator("[name=day]")).to_have_values(["1"])
            page.locator("[name=day]").select_option(["2"])
            page.get_by_role("button", name="Buscar", exact=True).click()
            expect(page.get_by_text("0 resultados", exact=True)).to_be_visible()
            page.goto(live_server.url + "/en/?q=photography&language=en&language=fr&day=1")
            expect(page.get_by_text("2 results", exact=True)).to_be_visible()
            expect(page.locator('[name=language] option[value="en"]')).to_have_count(1)
            assert "Synthetic profile" in page.content()
            page.locator("[name=checked]").select_option("age")
            page.get_by_role("button", name="Search", exact=True).click()
            expect(page.get_by_text("0 results", exact=True)).to_be_visible()
            page.reload()
            expect(page.locator("[name=checked]")).to_have_values(["age"])
            page.locator("[name=checked]").select_option([])
            page.get_by_role("button", name="Search", exact=True).click()
            expect(page.get_by_text("2 results", exact=True)).to_be_visible()
            link = page.locator("article.card h2 a").first
            title = link.inner_text()
            link.click()
            expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="Rates", exact=True)).to_have_count(0)
            expect(page.get_by_role("cell", name="Consult", exact=True)).to_have_count(0)
            expect(page.get_by_text("Age: simulated", exact=True)).to_be_visible()
            expect(page.get_by_text("Contact: simulated", exact=True)).to_be_visible()
            expect(page.get_by_text("Spanish, English", exact=False)).to_be_visible()
            page.reload()
            expect(page.get_by_text("Age: simulated", exact=True)).to_be_visible()
            image = page.get_by_role("img", name=title, exact=True)
            expect(image).to_be_visible()
            assert image.evaluate("img => img.complete && img.naturalWidth > 0")
        finally:
            browser.close()


@pytest.mark.django_db(transaction=True)
def test_mobile_geo_dependencies_clear_children_and_preserve_url(live_server, request, settings):
    from apps.catalog.models import Municipality, PostalCode

    settings.DEBUG = True
    request.getfixturevalue("directory")
    north = Municipality.objects.select_related("province").get(code="demo-north")
    south = Municipality.objects.select_related("province").get(code="demo-south")
    north_region, south_region = str(north.province.region_id), str(south.province.region_id)
    north_city, south_city = str(north.pk), str(south.pk)
    postal = str(PostalCode.objects.get(code="29001").pk)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/")
            page.locator("[name=region]").select_option(south_region)
            expect(page.locator(f'[name=city] option[value="{north_city}"]')).to_have_count(0)
            page.locator("[name=city]").select_option(south_city)
            page.locator("[name=postal_code]").select_option(postal)
            page.get_by_role("button", name="Search", exact=True).click()
            expect(page.get_by_text("0 results", exact=True)).to_be_visible()
            page.reload()
            expect(page.locator("[name=city]")).to_have_values([south_city])
            expect(page.locator("[name=postal_code]")).to_have_values([postal])
            page.locator("[name=region]").select_option(north_region)
            expect(page.locator("[name=city]")).to_have_values([])
            expect(page.locator("[name=postal_code]")).to_have_values([])
            page.locator("[name=region]").select_option([])
            expect(page.locator(f'[name=city] option[value="{south_city}"]')).to_have_count(1)
            page.get_by_role("button", name="Search", exact=True).click()
            expect(page.get_by_text("2 results", exact=True)).to_be_visible()
        finally:
            browser.close()


@pytest.mark.django_db(transaction=True)
def test_mobile_positive_pagination_preserves_filters_and_reload(live_server, request, settings):
    settings.DEBUG = True
    request.getfixturevalue("multipage_directory")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/?q=pagination&channel=phone")
            expect(page.get_by_text("25 results", exact=True)).to_be_visible()
            expect(page.locator("article.card")).to_have_count(24)
            first_links = page.locator("article.card h2 a").evaluate_all(
                "links => links.map(link => link.href)"
            )
            page.get_by_role("link", name="Next", exact=True).click()
            expect(page.locator("article.card")).to_have_count(1)
            assert (
                "page=2" in page.url and "q=pagination" in page.url and "channel=phone" in page.url
            )
            assert page.locator("article.card h2 a").get_attribute("href") not in [
                url.removeprefix(live_server.url) for url in first_links
            ]
            page.reload()
            expect(page.locator("[name=q]")).to_have_value("pagination")
            expect(page.locator("[name=channel]")).to_have_values(["phone"])
            expect(page.locator("article.card")).to_have_count(1)
            page.get_by_role("link", name="Previous", exact=True).click()
            expect(page.locator("article.card")).to_have_count(24)
            assert (
                page.locator("article.card h2 a").evaluate_all(
                    "links => links.map(link => link.href)"
                )
                == first_links
            )
        finally:
            browser.close()
