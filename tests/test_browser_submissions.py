import os
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401


@pytest.mark.django_db(transaction=True)
def test_mobile_submission_declaration_and_pending_reload(live_server, request, settings):
    settings.DEBUG = True
    user, _, _, revision = request.getfixturevalue("prepared")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/es/account/login/")
            page.locator("[name=email]").fill(user.email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/es/draft/{revision.pk}/4/")
            page.locator("[name=declaration]").check()
            page.get_by_role("button", name="Enviar a revisión").click()
            expect(page.get_by_text("Pendiente de revisión humana.", exact=False)).to_be_visible()
            page.reload()
            expect(page.get_by_text("Todavía no se ha publicado.", exact=False)).to_be_visible()
        finally:
            browser.close()
