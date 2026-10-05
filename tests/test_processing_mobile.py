"""Selected-purpose preparation through real mobile forms in both languages."""

import json
import shutil
from datetime import timedelta

import pyotp
import pytest
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.models import ProcessingPurposePlan

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_processing_preparation(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, _, _, _ = prepared_account(request, settings, monkeypatch, "object")
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
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
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Read latest request before preparing purpose-specific decisions"
            )
            page.locator("button[type=submit]").first.click()
            path = live_server.url + f"/{language}/moderation/rights/{case.pk}/processing/"
            page.goto(path)
            assert "core.User" not in page.content()
            reason = "Synthetic independent purpose preparation requires further review"
            page.locator("[name=reason]").fill(reason)
            button = "Record purpose action" if english else "Registrar acción por finalidad"
            page.get_by_role("button", name=button, exact=True).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Selected purposes" if english else "Finalidades seleccionadas",
                    exact=True,
                )
            ).to_be_visible()
            values = json.loads(page.locator("[name=decisions]").input_value())
            for item in values:
                item.update(
                    basis=reason,
                    reason=reason,
                    scope=reason,
                    review_on=(timezone.localdate() + timedelta(days=7)).isoformat(),
                )
            page.locator("[name=decisions]").fill(json.dumps(values))
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Preparation recorded; processing unchanged"
                if english
                else "Preparación registrada; tratamiento intacto"
            )
            page.reload()
            assert reason not in page.content() and "core.User" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    plan = ProcessingPurposePlan.objects.get()
    assert unseal(plan.encrypted_plan)["enforced"] is False
    case.refresh_from_db()
    assert case.status == "reviewing"
