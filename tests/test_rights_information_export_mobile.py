"""Approved access information is released through a real mobile form and private download."""

import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pyotp
import pytest
from django.db import connections
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_compilation import review_all
from test_rights_information_export import approved_information

from apps.safety.models import RightsExport, RightsExportInformationBinding

pytestmark = pytest.mark.django_db(transaction=True)


def database_value(query):
    def run():
        connections.close_all()
        try:
            return query()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(run).result(timeout=10)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_generate_pages_with_approved_information(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, actor, _, _, receipt, _, _, row, decision, _, value = approved_information(
        request, settings, monkeypatch
    )
    review_all(case, actor)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.get_by_role(
                "link",
                name="Prepare private copy" if english else "Preparar copia privada",
                exact=True,
            ).click()
            assert "Synthetic reviewed information" not in page.content()
            assert row.encrypted_information not in page.content()
            page.locator("[name=operation]").select_option("generate_pages_with_information")
            page.locator("[name=reason]").fill(
                "Release reviewed pages with independently approved information"
            )
            button = "Record copy action" if english else "Registrar acción de copia"
            page.get_by_role("button", name=button, exact=True).click()
            assert database_value(lambda: RightsExport.objects.count()) == 0
            page.locator("[name=information_review_id]").fill(str(decision.pk))
            page.get_by_role("button", name=button, exact=True).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Private rights inspection" if english else "Consulta privada de derechos",
                    exact=True,
                )
            ).to_be_visible()
            assert (
                database_value(lambda: RightsExportInformationBinding.objects.get().review_id)
                == decision.pk
            )
            assert "Synthetic reviewed information" not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt)
            with anonymous.expect_download() as item:
                anonymous.get_by_role("button", name="Download private copy", exact=True).click()
            copied = json.loads(Path(item.value.path()).read_text())
            assert copied["additional_information"]["access"] == value["access"]
            assert copied["partial"] and copied["simulation"]
        finally:
            browser.close()
