"""Pending portability assessments can be saved through real mobile sessions ES/EN."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilityAssessment

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_pending_portability_assessment(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    original = (case.version, case.status, case.scope_status)
    reason = "PRIVATE_SYNTHETIC_MOBILE_PORTABILITY"
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.get_by_role(
                "link",
                name="Assess portability datasets"
                if english
                else "Evaluar conjuntos de portabilidad",
                exact=True,
            ).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Assess portability datasets"
                    if english
                    else "Evaluar conjuntos de portabilidad",
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_text(
                    "Private favorites" if english else "Favoritos privados", exact=True
                )
            ).to_be_visible()
            assert page.locator("fieldset").count() == 9
            page.locator("[name=reason]").fill(reason)
            page.get_by_role(
                "button",
                name="Save assessment draft" if english else "Guardar borrador de evaluación",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Assessment draft saved" if english else "Borrador de evaluación guardado"
            )
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/")
            assert reason not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    row = RightsPortabilityAssessment.objects.get()
    assert all(item["status"] == "pending" for item in unseal(row.encrypted_assessment).values())
    case.refresh_from_db()
    assert (case.version, case.status, case.scope_status) == original
