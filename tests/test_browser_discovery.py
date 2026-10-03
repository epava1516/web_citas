import os
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
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
            page.locator("[name=service]").select_option(
                label=["Fotografía", "Eventos de modelaje"]
            )
            page.locator("[name=services_mode]").select_option("any")
            page.get_by_role("button", name="Buscar", exact=True).click()
            expect(page.get_by_text("2 resultados", exact=True)).to_be_visible()
            page.reload()
            expect(page.locator("[name=q]")).to_have_value("photography")
            page.locator("[name=services_mode]").select_option("all")
            page.get_by_role("button", name="Buscar", exact=True).click()
            expect(page.get_by_text("0 resultados", exact=True)).to_be_visible()
            page.goto(live_server.url + "/en/?q=photography")
            expect(page.get_by_text("2 results", exact=True)).to_be_visible()
            expect(page.get_by_role("option", name="Photography", exact=True)).to_have_count(1)
            assert "Synthetic profile" in page.content()
            link = page.locator("article.card h2 a").first
            title = link.inner_text()
            link.click()
            expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
            expect(page.get_by_role("heading", name="Rates", exact=True)).to_be_visible()
            expect(page.get_by_role("cell", name="Consult", exact=True)).to_be_visible()
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
