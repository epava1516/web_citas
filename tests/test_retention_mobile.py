"""Real mobile login and independent retention follow-up in both languages."""

import json
import shutil
from datetime import timedelta

import pyotp
import pytest
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_erasure_plans import BASIS
from test_reports import directory, photo_environment  # noqa: F401
from test_retention_reviews import prepared

from apps.core.mfa import encrypt
from apps.safety.models import RetentionReview, RetentionReviewEvent

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_independent_retention_followup(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, reviewer, _, _, _, plan, _ = prepared(request, settings, monkeypatch)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    review = RetentionReview.objects.filter(plan=plan).first()
    original = (plan.encrypted_decisions, plan.review_on, case.version, case.initial_due_at)
    english = language == "en"
    reason = "Independent mobile review records the remaining operational work"
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
                "Read the current request before independent retention review"
            )
            page.locator("button[type=submit]").first.click()
            page.goto(live_server.url + f"/{language}/moderation/rights/retention/?attention=all")
            expect(
                page.get_by_role(
                    "heading",
                    name="Retention review calendar"
                    if english
                    else "Calendario de revisión de conservación",
                    exact=True,
                )
            ).to_be_visible()
            path = live_server.url + f"/{language}/moderation/rights/retention/{review.pk}/"
            page.goto(path)
            assert BASIS not in page.content()
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(reason)
            button = "Record review action" if english else "Registrar acción de revisión"
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(BASIS, exact=True)).to_be_visible()
            page.locator("[name=operation]").select_option("follow_up")
            page.locator("[name=reason]").fill(reason)
            page.locator("[name=next_review_on]").fill(
                (timezone.localdate() + timedelta(days=7)).isoformat()
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Follow-up recorded; original plan unchanged"
                if english
                else "Seguimiento registrado; plan original intacto"
            )
            page.reload()
            assert BASIS not in page.content() and reason not in page.content()
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(
                "Read the independently recorded follow-up after reload"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(reason, exact=True)).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    review.refresh_from_db()
    plan.refresh_from_db()
    case.refresh_from_db()
    assert review.version == 2 and review.responsible_id == reviewer.pk
    assert RetentionReviewEvent.objects.filter(review=review, operation="follow_up").count() == 1
    assert (plan.encrypted_decisions, plan.review_on, case.version, case.initial_due_at) == original
