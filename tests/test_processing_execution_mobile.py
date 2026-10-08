"""Real mobile execution and subject-side restriction in ES/EN."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_processing_execution import prepared
from test_processing_localization import assert_execution
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety.models import PurposeRestriction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_apply_and_subject_favorites_block(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, actor, subject, plan, favorite, _ = prepared(request, settings, monkeypatch)
    original = (case.initial_due_at, subject.session_version, subject.is_active)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
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
                "Read current request before applying reviewed preferences restriction"
            )
            page.locator("button[type=submit]").first.click()
            path = (
                live_server.url
                + f"/{language}/moderation/rights/{case.pk}/processing/{plan.pk}/execute/"
            )
            page.goto(path)
            assert_execution(page, language)
            page.locator("[name=purposes][value=account_preferences]").check()
            reason = "Apply selected independently reviewed synthetic preferences restriction"
            page.locator("[name=reason]").fill(reason)
            page.locator("[name=confirmed]").check()
            page.get_by_role(
                "button",
                name="Apply selected restriction"
                if english
                else "Aplicar restricción seleccionada",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_have_text(
                "Selected restriction applied; request remains open"
                if english
                else "Restricción seleccionada aplicada; solicitud abierta"
            )
            assert_execution(page, language)
            page.reload()
            assert_execution(page, language)
            assert reason not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            own_context = browser.new_context(viewport={"width": 390, "height": 844})
            own = own_context.new_page()
            own.goto(live_server.url + f"/{language}/account/login/")
            own.locator("[name=email]").fill(subject.email)
            own.locator("[name=password]").fill("Synthetic-private-setup-123")
            own.locator("button[type=submit]").click()
            expect(
                own.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            response = own.goto(live_server.url + f"/{language}/favorites/")
            assert response.status == 409
            expect(
                own.get_by_text(
                    "This processing purpose is restricted / Esta finalidad de tratamiento está limitada",
                    exact=True,
                )
            ).to_be_visible()
            assert own.goto(live_server.url + f"/{language}/safety/rights/").status == 200
        finally:
            browser.close()
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (case.initial_due_at, subject.session_version, subject.is_active) == original
    assert case.status == "reviewing" and Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.get().active is True
