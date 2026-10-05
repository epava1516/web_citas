"""Guided information save/read on a real mobile browser, without GET body recovery."""

import json
import re
import shutil

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import prepared

from apps.safety.models import RightsAction, RightsCopyInformation

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_information_save_audited_read_replay_and_clean_get(
    live_server, request, settings, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, _, _, _ = prepared(request, settings)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
    path = f"/{language}/moderation/rights/{case.pk}/information/"
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
            page.goto(live_server.url + path)
            expect(
                page.get_by_role(
                    "heading",
                    name="Additional access information"
                    if english
                    else "Información adicional de acceso",
                    exact=True,
                )
            ).to_be_visible()
            save_label = "Save information draft" if english else "Guardar borrador de información"
            form = page.locator("form").filter(
                has=page.get_by_role("button", name=save_label, exact=True)
            )
            form.locator("[name=policy_version]").fill("synthetic-mobile-policy-v1")
            form.locator("[name=reason]").fill(
                "Save partial information through guided mobile form"
            )
            form.locator("[name=information-1-status]").select_option("reviewed")
            form.locator("[name=information-1-source]").select_option("reviewer")
            form.locator("[name=information-1-text]").fill("PRIVATE_MOBILE_INFORMATION")
            form.get_by_role("button", name=save_label, exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("1")
            reference = re.search(r": (\d+) ·", page.get_by_role("status").inner_text()).group(1)
            assert "PRIVATE_MOBILE_INFORMATION" not in page.content()
            page.reload()
            expect(page.get_by_role("status")).to_contain_text("1")
            page.goto(live_server.url + path)
            assert "PRIVATE_MOBILE_INFORMATION" not in page.content()
            read_label = "Inspect saved draft" if english else "Consultar borrador guardado"
            read_form = page.locator("form").filter(
                has=page.get_by_role("button", name=read_label, exact=True)
            )
            read_form.locator("[name=information_id]").fill(reference)
            read_form.locator("[name=purpose]").fill("Inspect saved information on mobile device")
            read_form.get_by_role("button", name=read_label, exact=True).click()
            expect(page.locator("[name=information-1-text]")).to_have_value(
                "PRIVATE_MOBILE_INFORMATION"
            )
            page.reload()
            expect(page.locator("[name=information-1-text]")).to_have_value(
                "PRIVATE_MOBILE_INFORMATION"
            )
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.goto(live_server.url + path)
            assert "PRIVATE_MOBILE_INFORMATION" not in page.content()
        finally:
            browser.close()
    assert RightsCopyInformation.objects.filter(request=case).count() == 1
    assert RightsAction.objects.filter(request=case, operation="copy_info_save").count() == 1
    assert RightsAction.objects.filter(request=case, operation="copy_info_read").count() == 1
