import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_appeals import rejected  # noqa: F401
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt


@pytest.mark.django_db(transaction=True)
def test_browser_appeal_and_independent_mfa_review(live_server, request, settings):
    settings.DEBUG = True
    person, _, revision, _, review_user, _ = request.getfixturevalue("rejected")
    secret = pyotp.random_base32()
    review_user.mfa_secret_encrypted = encrypt(secret)
    review_user.save(update_fields=["mfa_secret_encrypted"])
    owner_email = person.individual.email
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            owner_page = browser.new_page(viewport={"width": 390, "height": 844})
            owner_page.goto(live_server.url + "/es/account/login/")
            owner_page.locator("[name=email]").fill(owner_email)
            owner_page.locator("[name=password]").fill("Long-draft-password!847")
            owner_page.locator("button[type=submit]").click()
            owner_page.goto(live_server.url + f"/es/draft/{revision.pk}/status/")
            owner_page.get_by_role("link", name="Solicitar revisión", exact=True).click()
            owner_page.locator("[name=explanation]").fill(
                "Solicito comprobar nuevamente el contenido sintético"
            )
            owner_page.get_by_role("button", name="Enviar reclamación").click()
            owner_page.reload()
            expect(
                owner_page.get_by_text("Solicito comprobar nuevamente el contenido sintético")
            ).to_be_visible()
            staff = browser.new_page()
            staff.goto(live_server.url + "/es/account/login/")
            staff.locator("[name=email]").fill(review_user.email)
            staff.locator("[name=password]").fill("Long-appeal-password!847")
            staff.locator("button[type=submit]").click()
            staff.goto(live_server.url + "/es/moderation/appeals/")
            staff.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            staff.locator("button[type=submit]").click()
            staff.goto(live_server.url + "/es/moderation/appeals/")
            staff.get_by_role("link", name=revision.title).click()
            staff.get_by_role("link", name="Inspeccionar revisión completa y fotografías").click()
            expect(staff.get_by_role("img", name="Foto privada para revisión")).to_be_visible()
            staff.go_back()
            staff.locator("[name=result]").select_option("reconsider")
            staff.locator("[name=reason]").fill("Nueva revisión humana solicitada")
            staff.get_by_role("button", name="Resolver reclamación").click()
            owner_page.reload()
            expect(owner_page.get_by_text("Nueva revisión humana solicitada")).to_be_visible()
        finally:
            browser.close()
