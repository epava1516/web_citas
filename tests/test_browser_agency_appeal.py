import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_agency_appeals import rejected_agency  # noqa: F401
from test_browser_revised_listings import moderator_login
from test_drafts import scenario  # noqa: F401
from test_organization_review import organization  # noqa: F401

from apps.core.mfa import encrypt
from apps.core.models import AgencyAppeal, User


@pytest.mark.django_db(transaction=True)
def test_mobile_agency_rejection_appeal(live_server, request, settings):
    settings.DEBUG = True
    agency, _, _, independent, decision = request.getfixturevalue("rejected_agency")
    owner = agency.owner
    owner.role = "agency"
    owner.mfa_enabled = True
    moderator = User.objects.get(pk=independent.session["_auth_user_id"])
    secrets = [pyotp.random_base32(), pyotp.random_base32()]
    for user, secret in zip([owner, moderator], secrets, strict=True):
        user.set_password("Long-moderator-password!847")
        user.mfa_secret_encrypted = encrypt(secret)
        user.save()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            moderator_login(page, live_server.url, owner, secrets[0])
            page.goto(live_server.url + f"/es/agency/{agency.pk}/")
            page.get_by_role("link", name="Reclamar rechazo de agencia").click()
            page.locator("[name=explanation]").fill("Solicito una nueva comprobación de agencia")
            page.get_by_role("button", name="Enviar reclamación").click()
            expect(page.get_by_role("button", name="Enviar reclamación")).not_to_be_visible()
            expect(
                page.get_by_text("Solicito una nueva comprobación de agencia", exact=False)
            ).to_be_visible()
            page.reload()
            expect(
                page.get_by_text("Solicito una nueva comprobación de agencia", exact=False)
            ).to_be_visible()
            staff = browser.new_page()
            moderator_login(staff, live_server.url, moderator, secrets[1])
            staff.goto(live_server.url + "/es/moderation/agency-appeals/")
            staff.get_by_role("link", name=agency.name).click()
            staff.locator("[name=result]").select_option("reconsider")
            staff.locator("[name=reason]").fill("Se reabre para comprobar nuevas evidencias")
            staff.get_by_role("button", name="Resolver reclamación de agencia").click()
            expect(
                staff.get_by_role("button", name="Resolver reclamación de agencia")
            ).not_to_be_visible()
            expect(
                staff.get_by_text("Se reabre para comprobar nuevas evidencias", exact=False)
            ).to_be_visible()
            page.reload()
            expect(
                page.get_by_text("Se reabre para comprobar nuevas evidencias", exact=False)
            ).to_be_visible()
            page.goto(live_server.url + f"/es/agency/{agency.pk}/")
            expect(
                page.get_by_text("Comprobación de agencia: pending", exact=False)
            ).to_be_visible()
        finally:
            browser.close()
    assert AgencyAppeal.objects.get(decision=decision).status == "resolved"
    agency.refresh_from_db()
    assert agency.verification_status == "pending" and agency.review_version == 3
