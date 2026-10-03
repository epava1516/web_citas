import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_browser_revised_listings import moderator_login
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_manager_appeals import manager_rejection  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt
from apps.core.models import ManagerAppeal


@pytest.mark.django_db(transaction=True)
def test_browser_manager_rejection_appeal(live_server, request, settings):
    settings.DEBUG = True
    person, _, _, _, independent, decision = request.getfixturevalue("manager_rejection")
    reviewer = independent.session["_auth_user_id"]
    from apps.core.models import User

    moderator = User.objects.get(pk=reviewer)
    moderator.set_password("Long-moderator-password!847")
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["password", "mfa_secret_encrypted"])
    subject_email = person.subject.email
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            owner = browser.new_page(viewport={"width": 390, "height": 844})
            owner.goto(live_server.url + "/es/account/login/")
            owner.locator("[name=email]").fill(subject_email)
            owner.locator("[name=password]").fill("Long-draft-password!847")
            owner.locator("button[type=submit]").click()
            owner.goto(live_server.url + f"/es/person/{person.pk}/verification/")
            owner.get_by_role("link", name="Reclamar rechazo del gestor").click()
            owner.locator("[name=explanation]").fill("Solicito revisión de mi autorización")
            owner.get_by_role("button", name="Enviar reclamación").click()
            owner.reload()
            expect(
                owner.get_by_text("Solicito revisión de mi autorización", exact=False)
            ).to_be_visible()
            staff = browser.new_page()
            moderator_login(staff, live_server.url, moderator, secret)
            staff.goto(live_server.url + "/es/moderation/manager-appeals/")
            staff.get_by_role("link", name=person.alias).click()
            staff.locator("[name=result]").select_option("approved")
            staff.locator("[name=reason]").fill("Autorización actual revisada independientemente")
            staff.get_by_role("button", name="Resolver reclamación del gestor").click()
            owner.reload()
            expect(
                owner.get_by_text("Autorización actual revisada independientemente", exact=False)
            ).to_be_visible()
            owner.goto(live_server.url + f"/es/person/{person.pk}/verification/")
            expect(owner.get_by_text("Requisitos locales completos", exact=False)).to_be_visible()
        finally:
            browser.close()
    assert ManagerAppeal.objects.get(decision=decision).status == "resolved"
