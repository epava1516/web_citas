"""Operational calendar through real mobile login/MFA and audited history ES/EN."""

import json
import shutil
from datetime import timedelta

import pyotp
import pytest
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_purpose_calendar import setup_calendar
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import encrypt
from apps.safety.models import PurposeCalendarEvent

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_calendar_follow_up_reload_and_audit(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, reviewer, _, subject, favorite, restriction = setup_calendar(
        request, settings, monkeypatch
    )
    before = (
        case.version,
        case.scope_status,
        case.initial_due_at,
        subject.session_version,
        restriction.review_on,
    )
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    english = language == "en"
    root = live_server.url + f"/{language}"
    next_date = timezone.localdate() + timedelta(days=7)
    reason = "Private synthetic mobile follow-up preserves the processing restriction"
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
            page.goto(root + "/moderation/rights/")
            page.get_by_role(
                "link",
                name="Restriction review calendar"
                if english
                else "Calendario de revisión de restricciones",
                exact=True,
            ).click()
            page.locator("[name=attention]").select_option("all")
            page.get_by_role("button", name="Filter" if english else "Filtrar", exact=True).click()
            page.get_by_role(
                "link", name="Follow up" if english else "Seguimiento", exact=True
            ).click()
            page.locator("[name=operation]").select_option("follow_up")
            page.locator("[name=reason]").fill(reason)
            page.locator("[name=next_review_on]").fill(next_date.isoformat())
            button = "Record calendar action" if english else "Registrar acción de calendario"
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Follow-up recorded; restriction unchanged"
                if english
                else "Seguimiento registrado; restricción intacta"
            )
            page.reload()
            assert reason not in page.content()
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(
                "Audit recorded follow-up with current operational authority"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(reason, exact=True)).to_be_visible()
            current_url = page.url
            with page.expect_request(lambda request: request.url == current_url) as reloaded:
                page.reload()
            assert reloaded.value.method == "POST"
            expect(page.get_by_text(reason, exact=True)).to_be_visible()
            page.goto(current_url)
            assert reason not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    restriction.refresh_from_db()
    case.refresh_from_db()
    subject.refresh_from_db()
    assert (
        case.version,
        case.scope_status,
        case.initial_due_at,
        subject.session_version,
    ) == before[:4]
    assert (
        restriction.active
        and restriction.version == 2
        and restriction.initial_review_on == before[4]
    )
    assert (
        restriction.review_on == next_date
        and favorite.__class__.objects.filter(pk=favorite.pk).exists()
    )
    assert PurposeCalendarEvent.objects.count() == 2
