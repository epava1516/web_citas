"""Account-only SSR copy and anonymous download on mobile in both languages."""

import json
import shutil
from pathlib import Path

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.models import RightsExportDownload

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_account_copy_login_audit_generate_and_download(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, subject, _, receipt = prepared_account(request, settings, monkeypatch)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
    submit = "Record copy action" if english else "Registrar acción de copia"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(moderator["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(moderator["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/export/")
            expect(
                page.get_by_role(
                    "heading",
                    name="Prepare private account copy"
                    if english
                    else "Preparar copia privada de cuenta",
                    exact=True,
                )
            ).to_be_visible()
            assert (
                page.locator("[name=copy]").input_value() == ""
                and subject.email not in page.content()
            )
            page.locator("[name=operation]").select_option("preview")
            page.locator("[name=purpose]").fill("Read own account copy before reviewed release")
            page.get_by_role("button", name=submit, exact=True).click()
            expect(page.locator("[name=copy]")).not_to_have_value("")
            copied_source = json.loads(page.locator("[name=copy]").input_value())
            assert copied_source["subject_account"]["email"] == subject.email
            page.locator("[name=reason]").fill("Release reviewed synthetic own account copy")
            page.get_by_role("button", name=submit, exact=True).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Private rights inspection" if english else "Consulta privada de derechos",
                    exact=True,
                )
            ).to_be_visible()
            page.reload()
            assert subject.email not in page.content()
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt.replace("/en/", f"/{language}/", 1))
            with anonymous.expect_download() as item:
                anonymous.get_by_role(
                    "button",
                    name="Download private copy" if english else "Descargar copia privada",
                    exact=True,
                ).click()
            copied = json.loads(Path(item.value.path()).read_text())
            assert copied["schema"] == "subject-account-copy-v1" and copied["partial"] is True
            assert copied["subject_account"]["email"] == subject.email
            assert copied["profile"] is None and copied["revisions"] == []
            anonymous.reload()
            assert subject.email not in anonymous.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert anonymous.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert RightsExportDownload.objects.filter(export__account_subject=subject).count() == 1
