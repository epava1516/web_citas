"""Mobile ES/EN independent inspection and decision using real login and MFA."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_processing_plans import REASON
from test_purpose_exception_review import ready
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import encrypt
from apps.listings.models import Favorite
from apps.safety.models import PurposeExceptionRead, PurposeExceptionReview, PurposeRestriction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_audited_independent_review_preserves_active_restriction(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, _, favorite, proposal, reviewer, _ = ready(request, settings, monkeypatch)
    original = case.version, case.status, case.initial_due_at
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    english = language == "en"
    root = live_server.url + f"/{language}"
    path = root + f"/moderation/rights/{case.pk}/exceptions/{proposal.pk}/review/"
    button = "Record review action" if english else "Registrar acción de revisión"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(root + "/account/login/")
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
            page.goto(root + f"/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Inspect current request before independently reviewing exception"
            )
            page.locator("button[type=submit]").first.click()
            page.goto(path)
            assert REASON not in page.content()
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(
                "Audit the current complete scope before deciding this exception"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(REASON, exact=True).first).to_be_visible()
            page.locator("[name=operation]").select_option("review")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill(
                "Independent synthetic decision for one scoped reviewed operation"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Independent decision recorded; restrictions remain active"
                if english
                else "Decisión independiente registrada; las restricciones siguen activas"
            )
            page.reload()
            expect(page.get_by_role("status")).to_be_visible()
            page.goto(path)
            assert REASON not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    review = PurposeExceptionReview.objects.get(proposal=proposal)
    assert review.action.actor_id == reviewer.pk and review.outcome == "approved"
    assert review.consumed_action_id is None
    assert PurposeExceptionRead.objects.filter(proposal=proposal).count() == 1
    assert Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.get().active
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
