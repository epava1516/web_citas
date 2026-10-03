import os
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_match_review import conflict  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.mfa import encrypt


def moderator_login(page, origin, moderator, secret):
    page.goto(origin + "/es/account/login/")
    page.locator("[name=email]").fill(moderator.email)
    page.locator("[name=password]").fill("Long-moderator-password!847")
    page.locator("button[type=submit]").click()
    page.goto(origin + "/es/moderation/listings/")
    page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
    page.locator("button[type=submit]").click()


@pytest.mark.django_db(transaction=True)
def test_mobile_edit_keeps_public_snapshot_until_review(live_server, request, settings):
    settings.DEBUG = True
    person, _, original, moderator, _ = request.getfixturevalue("published")
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
            page.locator("[name=email]").fill(person.individual.email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/es/draft/{original.pk}/status/")
            page.get_by_role("button", name="Crear o retomar borrador revisado").click()
            page.locator("[name=title]").fill("Versión móvil actualizada")
            page.get_by_role("button", name="Guardar y continuar").click()
            page.locator("[name=contact_exposure_accepted]").check()
            page.locator("[name=accept_publishing]").check()
            page.get_by_role("button", name="Guardar y continuar").click()
            page.get_by_role("link", name="Revisar borrador").click()
            page.locator("[name=declaration]").check()
            page.get_by_role("button", name="Enviar a revisión").click()
            assert page.url.endswith("/status/")
            revision_id = page.url.split("/draft/", 1)[1].split("/", 1)[0]
            guest = browser.new_page()
            guest.goto(live_server.url + f"/es/listing/{original.listing_id}/")
            expect(guest.get_by_role("heading", name=original.title)).to_be_visible()
            reviewer_page = browser.new_page()
            moderator_login(reviewer_page, live_server.url, moderator, secret)
            reviewer_page.goto(live_server.url + f"/es/moderation/listings/{revision_id}/")
            reviewer_page.locator("[name=outcome]").select_option("approved")
            reviewer_page.locator("[name=reason]").fill("Cambios sintéticos revisados")
            reviewer_page.get_by_role("button", name="Registrar decisión").click()
            guest.reload()
            expect(guest.get_by_role("heading", name="Versión móvil actualizada")).to_be_visible()
        finally:
            browser.close()


@pytest.mark.django_db(transaction=True)
def test_browser_match_resolution_and_pending_approval(live_server, request, settings):
    settings.DEBUG = True
    _, revision, match, moderator, _, _, _ = request.getfixturevalue("conflict")
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["mfa_secret_encrypted"])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page()
            moderator_login(page, live_server.url, moderator, secret)
            page.goto(live_server.url + "/es/moderation/matches/")
            page.get_by_role("link", name=f"{match.pk} · sha256", exact=True).click()
            expect(page.get_by_role("img", name="Primera foto de revisión")).to_be_visible()
            expect(page.get_by_role("img", name="Segunda foto de revisión")).to_be_visible()
            page.locator("[name=outcome]").select_option("distinct_people")
            page.locator("[name=reason]").fill(
                "Autorizaciones sintéticas directas de ambas personas revisadas"
            )
            page.locator("[name=evidence_reference]").fill("synthetic-browser-review")
            page.get_by_role("button", name="Registrar resolución").click()
            page.reload()
            expect(
                page.get_by_text("Autorizaciones sintéticas directas de ambas personas revisadas")
            ).to_be_visible()
            page.goto(live_server.url + f"/es/moderation/listings/{revision.pk}/")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill("Anuncio sintético válido")
            page.get_by_role("button", name="Registrar decisión").click()
            guest = browser.new_page()
            guest.goto(live_server.url + f"/es/listing/{revision.listing_id}/")
            expect(guest.get_by_role("heading", name=revision.title)).to_be_visible()
        finally:
            browser.close()
