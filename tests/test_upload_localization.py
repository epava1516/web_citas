"""Finite browser rejects; no benchmark workload or changes to photo ingestion."""

import shutil

import pytest
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import RateWindow
from apps.listings.models import Revision
from apps.mediafiles.models import Blob, Photo, UploadAttempt

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_upload_missing_and_rate_localized_without_effects(
    request,
    settings,
    photo_environment,  # noqa: F811
    live_server,
    language,
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    _, person, client = request.getfixturevalue("scenario")
    assert client.post(f"/{language}/person/{person.pk}/listing/start/").status_code == 302
    revision = Revision.objects.get()
    before = revision.edit_version
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            draft = live_server.url + f"/{language}/draft/{revision.pk}/3/"
            page.goto(draft)
            form = page.locator("form", has=page.locator("input[type=file]"))
            form.evaluate("e=>e.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                form.locator("button[type=submit]").click()
            assert response.value.status == 400
            expect(page.locator("body")).to_have_text(
                "File required" if language == "en" else "Archivo requerido"
            )
            window = db_sync(lambda: RateWindow.objects.get())
            assert window.attempts == 1
            db_sync(lambda: RateWindow.objects.filter(pk=window.pk).update(attempts=30))
            page.goto(draft)
            form = page.locator("form", has=page.locator("input[type=file]"))
            form.evaluate("e=>e.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as response:
                form.locator("button[type=submit]").click()
            assert response.value.status == 429
            expect(page.locator("body")).to_have_text(
                "Too many uploads" if language == "en" else "Demasiadas subidas"
            )
            assert db_sync(lambda: RateWindow.objects.get(pk=window.pk).attempts) == 31
        finally:
            browser.close()
    revision.refresh_from_db()
    assert revision.edit_version == before and revision.status == "draft"
    assert Photo.objects.count() == Blob.objects.count() == UploadAttempt.objects.count() == 0
