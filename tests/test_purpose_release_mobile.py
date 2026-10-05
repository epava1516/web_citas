"""Mobile ES/EN release UI with real sessions and a disclosed simulated scoped check."""

import json
import shutil
from uuid import uuid4

import pyotp
import pytest
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_processing_plans import REASON
from test_purpose_release import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_verification import read

from apps.core.mfa import encrypt
from apps.safety.models import PurposeReleaseProposal
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_propose_reload_receive_and_execute(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, creator, reviewer, _, _, favorite, restriction = prepared(request, settings, monkeypatch)
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    english = language == "en"
    root = live_server.url + f"/{language}"
    case_path = root + f"/moderation/rights/{case.pk}/"
    path = case_path + f"restrictions/{restriction.pk}/release/"
    button = (
        "Record restriction release action"
        if english
        else "Registrar acción de levantamiento de restricción"
    )
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
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
            page.goto(case_path)
            page.locator("[name=purpose]").fill(
                "Read current restriction before independent mobile release"
            )
            page.locator("button[type=submit]").first.click()
            page.get_by_role(
                "link",
                name="Purpose restrictions" if english else "Restricciones por finalidad",
                exact=True,
            ).click()
            page.get_by_role(
                "link", name="Review restriction" if english else "Revisar restricción", exact=True
            ).click()
            assert REASON not in page.content()
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(REASON, exact=True).first).to_be_visible()
            page.locator("[name=operation]").select_option("propose")
            page.locator("[name=ground]").select_option("restriction_resolved")
            page.locator("[name=reason]").fill(
                "Independent mobile review proposes preferences resumption"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Release proposed and notified; restriction remains active"
                if english
                else "Levantamiento propuesto y comunicado; restricción activa"
            )
            page.reload()
            expect(page.get_by_role("status")).to_be_visible()
            assert REASON not in page.content()
            assert page.locator("[name=proposal_id]").input_value()
            state = context.storage_state()
        finally:
            browser.close()
    proposal = PurposeReleaseProposal.objects.get()
    assert (
        Client()
        .post(
            case._receipt_path + f"response/{proposal.response_id}/acknowledge/",
            {"received": "yes"},
        )
        .status_code
        == 302
    )
    # The explicit development adapter prepares the later proof outside Playwright's async loop.
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    case.refresh_from_db()
    read(client, case)
    proof = start(reviewer, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    verifier = Client()
    verifier.force_login(creator)
    session = verifier.session
    session["mfa_version"] = creator.mfa_version
    session.save()
    read(verifier, case)
    receive_event(creator, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(
                viewport={"width": 390, "height": 844}, storage_state=state
            )
            page = context.new_page()
            page.goto(case_path)
            page.locator("[name=purpose]").fill(
                "Read fresh request and notified response before execution"
            )
            page.locator("button[type=submit]").first.click()
            page.goto(path)
            page.locator("[name=operation]").select_option("execute")
            page.locator("[name=reason]").fill(
                "Execute notified proposal after received response and fresh check"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Selected restriction released; request remains open"
                if english
                else "Restricción seleccionada levantada; solicitud abierta"
            )
            page.reload()
            expect(page.get_by_role("status")).to_be_visible()
            assert REASON not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    restriction.refresh_from_db()
    case.refresh_from_db()
    assert not restriction.active and case.status == "reviewing"
    assert favorite.__class__.objects.filter(pk=favorite.pk).exists()
