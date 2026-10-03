import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_organization_review import organization  # noqa: F401

from apps.core.mfa import encrypt


@pytest.mark.django_db(transaction=True)
def test_browser_moderator_mfa_and_organization_decision(live_server, request, settings):
    settings.DEBUG = True
    agency, moderator, _ = request.getfixturevalue("organization")
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
            page.goto(live_server.url + "/es/moderation/organizations/")
            expect(
                page.get_by_role("heading", name="Autenticación de dos factores")
            ).to_be_visible()
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + "/es/moderation/organizations/")
            page.get_by_role("link", name=agency.name).click()
            page.locator("[name=outcome]").select_option("passed")
            page.locator("[name=reason]").fill("Organización sintética revisada en pruebas")
            page.locator("[name=evidence_reference]").fill("synthetic-browser-reference")
            page.get_by_role("button", name="Registrar decisión").click()
            page.reload()
            expect(page.get_by_text("Organización sintética revisada en pruebas")).to_be_visible()
            expect(page.get_by_text("Comprobación de agencia: passed")).to_be_visible()
            expect(page.get_by_role("button", name="Registrar decisión")).to_have_count(0)
        finally:
            browser.close()
