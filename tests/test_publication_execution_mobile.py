"""Initial publication restriction selected through real mobile form and TOTP."""

import json
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_processing_publication import (
    test_reviewed_publication_pause_replay_preserves_data_and_central_guard as run_flow,
)
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.mfa import encrypt

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_initial_publication_execution(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    import apps.safety.processing_execution as module

    settings.DEBUG = True
    original = module.execute
    checked = []

    def mobile(user, case_id, plan_id, key, version, purposes, reason, confirmed):
        if not checked:
            checked.append(True)
            secret = pyotp.random_base32()
            user.mfa_secret_encrypted = encrypt(secret)
            user.save(update_fields=["mfa_secret_encrypted"])
            credentials = json.loads((tmp_path / "credentials.json").read_text())
            root = live_server.url + f"/{language}"
            english = language == "en"
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
                )
                try:
                    page = browser.new_page(viewport={"width": 390, "height": 844})
                    page.goto(root + "/account/login/")
                    page.locator("[name=email]").fill(user.email)
                    page.locator("[name=password]").fill(credentials["password"])
                    page.locator("button[type=submit]").click()
                    page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
                    page.locator("button[type=submit]").click()
                    expect(
                        page.get_by_role(
                            "heading", name="Your account" if english else "Tu cuenta", exact=True
                        )
                    ).to_be_visible()
                    path = root + f"/moderation/rights/{case_id}/processing/{plan_id}/execute/"
                    page.goto(path)
                    page.locator('[name=purposes][value="publication"]').check()
                    page.locator("[name=reason]").fill(reason)
                    page.locator("[name=confirmed]").check()
                    page.locator("[name=key]").evaluate("(el, value) => el.value = value", str(key))
                    page.locator("[name=version]").evaluate(
                        "(el, value) => el.value = value", str(version)
                    )
                    page.locator("button[type=submit]").click()
                    status = (
                        "Selected restriction applied"
                        if english
                        else "Restricción seleccionada aplicada"
                    )
                    expect(page.get_by_role("status")).to_contain_text(status)
                    page.reload()
                    expect(page.get_by_role("status")).to_contain_text(status)
                    assert page.evaluate(
                        "document.documentElement.scrollWidth <= window.innerWidth"
                    )
                    page.goto(path)
                    assert reason not in page.content()
                finally:
                    browser.close()
        return original(user, case_id, plan_id, key, version, purposes, reason, confirmed)

    monkeypatch.setattr(module, "execute", mobile)
    run_flow(request, settings, monkeypatch, "restrict", mixed=False)
    assert checked == [True]
