"""ES/EN mobile consumes an approved exception through the actual erasure form."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_purpose_exception_consumption import approved
from test_reports import directory, photo_environment  # noqa: F401

from apps.listings.models import Favorite
from apps.safety.models import ErasureExecution, PurposeExceptionReview, PurposeRestriction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_consume_reload_and_active_measure(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, plan, favorite, proposal, _, _ = approved(request, settings, monkeypatch)
    original = case.version, case.initial_due_at
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
    root = live_server.url + f"/{language}"
    from django.urls import reverse

    path = live_server.url + reverse(
        "erasure_execute", kwargs={"case_id": case.pk, "plan_id": plan.pk}
    )
    if language == "en":
        path = path.replace("/es/", "/en/", 1)
    else:
        path = path.replace("/en/", "/es/", 1)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(root + "/account/login/")
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
            page.goto(path)
            page.locator("[name=purposes][value=account_preferences]").check()
            page.locator("[name=exception_id]").fill(str(proposal.pk))
            page.locator("[name=reason]").fill(
                "Execute the exact independently approved synthetic erasure scope"
            )
            page.locator("[name=confirmed]").check()
            page.get_by_role(
                "button",
                name="Execute confirmed scoped erasure"
                if english
                else "Ejecutar supresión confirmada por ámbito",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_have_text(
                "Selected scopes executed; request remains open"
                if english
                else "Ámbitos seleccionados ejecutados; solicitud abierta"
            )
            page.reload()
            expect(page.get_by_role("status")).to_be_visible()
            page.goto(path)
            assert page.get_by_role("status").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    execution = ErasureExecution.objects.get()
    assert (
        PurposeExceptionReview.objects.get(proposal=proposal).consumed_action_id
        == execution.action_id
    )
    assert not Favorite.objects.filter(pk=favorite.pk).exists()
    assert PurposeRestriction.objects.get().active
    case.refresh_from_db()
    assert case.version == original[0] + 1 and case.initial_due_at == original[1]
