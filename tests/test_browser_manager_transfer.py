import os
import shutil

import pyotp
import pytest
from django.core import mail
from playwright.sync_api import expect, sync_playwright
from test_browser_revised_listings import moderator_login
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt
from apps.core.models import Agency, ManagerReview, User
from apps.core.verification_services import publication_ready


@pytest.mark.django_db(transaction=True)
def test_mobile_agency_transfer_to_self_and_human_review(live_server, request, settings):
    settings.DEBUG = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    person, _, revision, moderator, _ = request.getfixturevalue("pending")
    subject_email = person.subject.email
    old_owner = User.objects.create_user(
        username="old-browser-agency",
        email="old-browser-agency@example.invalid",
        role="agency",
        mfa_enabled=True,
    )
    agency = Agency.objects.create(owner=old_owner, name="Agencia previa sintética")
    person.individual = None
    person.agency = agency
    person.save(update_fields=["individual", "agency"])
    person.representationaction_set.filter(action="grant").update(
        manager_kind="agency", manager_id=str(agency.pk)
    )
    claim = person.phone_claim
    claim.individual = None
    claim.agency = agency
    claim.save(update_fields=["individual", "agency"])
    old_photo_id = revision.photos.get().pk
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["mfa_secret_encrypted"])
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
            page.goto(live_server.url + f"/es/person/{person.pk}/verification/")
            page.get_by_role("link", name="Cambiar gestor").click()
            expect(page.locator("[name=manager_version]")).to_have_value("1")
            page.locator("[name=confirm]").check()
            page.locator("button[type=submit]").click()
            expect(page.get_by_text("Publicación bloqueada", exact=False)).to_be_visible()
            assert (
                page.request.get(live_server.url + f"/es/photos/{old_photo_id}/private/").status
                == 404
            )
            page.get_by_role("link", name="Autorizar publicación").click()
            page.locator("[name=authorize]").check()
            page.locator("button[type=submit]").click()
            page.get_by_role("link", name="Simulador de edad").click()
            page.locator("[name=outcome]").select_option("passed")
            page.locator("button[type=submit]").click()
            page.get_by_role("link", name="Comprobar teléfono").click()
            page.locator("[name=phone]").fill("600888444")
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(mail.outbox[-1].body)
            page.locator("button[type=submit]").click()
            expect(page.get_by_text("Publicación bloqueada", exact=False)).to_be_visible()
            staff = browser.new_page()
            moderator_login(staff, live_server.url, moderator, secret)
            staff.goto(live_server.url + "/es/moderation/managers/")
            staff.get_by_role("link", name=person.alias).click()
            staff.locator("[name=outcome]").select_option("approved")
            staff.locator("[name=reason]").fill("Transferencia sintética autorizada por su titular")
            staff.get_by_role("button", name="Registrar revisión del gestor").click()
            staff.reload()
            expect(
                staff.get_by_text("Transferencia sintética autorizada por su titular")
            ).to_be_visible()
            page.reload()
            expect(page.get_by_text("Requisitos locales completos", exact=False)).to_be_visible()
        finally:
            browser.close()
    person.refresh_from_db()
    assert person.agency_id is None and person.manager_version == 2 and publication_ready(person)
    assert ManagerReview.objects.get().manager_version == 2
