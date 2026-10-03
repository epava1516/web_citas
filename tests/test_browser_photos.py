import os
import shutil

import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_photos import raw_image

from apps.listings.models import Listing, Revision


@pytest.mark.django_db(transaction=True)
def test_browser_photo_upload_preview_remove(live_server, request, settings, tmp_path):
    user, person, _ = request.getfixturevalue("scenario")
    settings.MEDIA_ROOT = tmp_path / "private"
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    revision = Revision.objects.create(
        listing=Listing.objects.create(person=person), manager_version=1
    )
    file = tmp_path / "synthetic.jpg"
    file.write_bytes(raw_image(34))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 390, "height": 844})
        try:
            page.goto(live_server.url + "/es/account/login/")
            page.locator("[name=email]").fill(user.email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/es/draft/{revision.pk}/3/")
            page.locator("[name=image]").set_input_files(str(file))
            page.get_by_role("button", name="Subir foto", exact=True).click()
            expect(page.locator("img")).to_be_visible()
            assert page.locator("img").evaluate("(img) => img.complete && img.naturalWidth > 0")
            page.reload()
            expect(page.locator("img")).to_be_visible()
            page.get_by_role("button", name="Eliminar foto").click()
            expect(page.locator("img")).to_have_count(0)
        finally:
            browser.close()
    assert revision.photos.filter(removed_at__isnull=True).count() == 0
