import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_browser_revised_listings import moderator_login
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_match_review import conflict  # noqa: F401
from test_photo_appeals import independent_reviewer
from test_photo_restrictions import restricted  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt
from apps.mediafiles.models import PhotoAppeal


@pytest.mark.django_db(transaction=True)
def test_mobile_photo_appeal_submission_and_independent_reopening(live_server, request, settings):
    settings.DEBUG = True
    values, notices = request.getfixturevalue("restricted")
    original, _, _, original_moderator, _, _, _ = values
    moderator, _ = independent_reviewer(original_moderator)
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["mfa_secret_encrypted"])
    subject_email = original.listing.person.subject.email
    alias = original.listing.person.alias
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/es/account/login/")
            page.locator("[name=email]").fill(subject_email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/es/person/photo-restrictions/{notices[0].pk}/")
            page.locator("[name=explanation]").fill("Revisen mi autorización sobre la foto")
            page.get_by_role("button", name="Enviar reclamación").click()
            expect(
                page.get_by_text("Revisen mi autorización sobre la foto", exact=False)
            ).to_be_visible()
            page.reload()
            staff = browser.new_page()
            moderator_login(staff, live_server.url, moderator, secret)
            staff.goto(live_server.url + "/es/moderation/photo-appeals/")
            staff.get_by_role("link", name=alias).click()
            staff.get_by_role("link", name="Inspeccionar evidencia privada").click()
            expect(staff.get_by_role("img", name="Segunda foto de revisión")).to_be_visible()
            staff.go_back()
            staff.locator("[name=result]").select_option("reconsider")
            staff.locator("[name=reason]").fill("Nueva revisión humana de autorización de foto")
            staff.get_by_role("button", name="Resolver reclamación de foto").click()
            expect(
                staff.get_by_text("Nueva revisión humana de autorización de foto", exact=False)
            ).to_be_visible()
            page.reload()
            expect(
                page.get_by_text("Pendiente de nueva revisión humana", exact=False)
            ).to_be_visible()
            assert "second-subject@example.invalid" not in page.content()
            assert (
                page.request.get(
                    live_server.url + f"/es/person/photo-restrictions/{notices[1].pk}/"
                ).status
                == 404
            )
        finally:
            browser.close()
    assert PhotoAppeal.objects.get().status == "resolved"
