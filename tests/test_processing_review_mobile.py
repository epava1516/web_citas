"""Independent plan inspection and decision through actual mobile sessions ES/EN."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_processing_plans import REASON
from test_processing_review import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import encrypt
from apps.safety.models import ProcessingPlanReview

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_independent_plan_review(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, plan, reviewer, _ = prepared(request, settings, monkeypatch)
    original = (case.version, case.status, case.initial_due_at)
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(reviewer.email)
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Inspect latest request before independent purpose review"
            )
            page.locator("button[type=submit]").first.click()
            path = (
                live_server.url + f"/{language}/moderation/rights/{case.pk}/processing/{plan.pk}/"
            )
            page.goto(path)
            assert REASON not in page.content()
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(
                "Audit current plan before independent operational review"
            )
            button = (
                "Record plan review action" if english else "Registrar acción de revisión de plan"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(REASON, exact=True).first).to_be_visible()
            page.locator("[name=operation]").select_option("review")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill(
                "Independent synthetic review confirms the selected decisions"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Review recorded; processing unchanged"
                if english
                else "Revisión registrada; tratamiento intacto"
            )
            page.reload()
            assert REASON not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    result = ProcessingPlanReview.objects.get(plan=plan)
    assert result.action.actor_id == reviewer.pk and result.outcome == "approved"
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
