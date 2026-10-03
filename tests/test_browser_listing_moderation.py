import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt


@pytest.mark.django_db(transaction=True)
def test_browser_listing_review_and_public_version(live_server, request, settings):
    settings.DEBUG = True
    _, _, revision, moderator, _ = request.getfixturevalue("pending")
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["mfa_secret_encrypted"])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(live_server.url + "/es/account/login/")
            page.locator("[name=email]").fill(moderator.email)
            page.locator("[name=password]").fill("Long-moderator-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + "/es/moderation/listings/")
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + "/es/moderation/listings/")
            page.get_by_role("link", name=revision.title).click()
            image = page.get_by_role("img", name="Foto privada para revisión")
            expect(image).to_be_visible()
            assert image.evaluate("img => img.complete && img.naturalWidth > 0")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill("Publicación sintética revisada por moderador")
            page.get_by_role("button", name="Registrar decisión").click()
            page.reload()
            expect(page.get_by_text("Publicación sintética revisada por moderador")).to_be_visible()
            guest = browser.new_page(viewport={"width": 390, "height": 844})
            guest.goto(live_server.url + f"/es/listing/{revision.listing_id}/")
            expect(guest.get_by_role("heading", name=revision.title)).to_be_visible()
            expect(guest.get_by_role("img", name=revision.title)).to_be_visible()
        finally:
            browser.close()
