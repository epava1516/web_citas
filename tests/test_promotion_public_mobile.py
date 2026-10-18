"""Anonymous mobile visitors see explicit synthetic sponsorship, subject to filters."""

import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_promotion_exposure import purchased

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_public_mobile_sponsorship_is_visible_and_respects_search(
    request, settings, live_server, language
):
    settings.DEBUG = True  # Serve local static assets, as in the existing browser gates.
    _, listing, _ = purchased(request, settings)
    caption = "Sponsored (simulation)" if language == "en" else "Patrocinado (simulación)"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            response = page.goto(live_server.url + f"/{language}/")
            assert response.status == 200
            card = page.locator(
                f'article.listing-card:has(a[href="/{language}/listing/{listing.pk}/"])'
            )
            expect(card.locator(".sponsored")).to_be_visible()
            expect(card.locator(".sponsored")).to_contain_text(caption)
            expect(page.locator(".sponsored")).to_have_count(1)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            response = page.goto(
                live_server.url + f"/{language}/?q=unmatchedpromotionquery8293"
            )
            assert response.status == 200
            expect(page.locator(".sponsored")).to_have_count(0)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
