"""Account-only SSR copy and anonymous download on mobile in both languages."""

import json
import shutil
from pathlib import Path

import pyotp
import pytest
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_compilation import review_all

from apps.core.models import PhoneClaim
from apps.safety.models import RightsExportDownload

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_direct_account_copy_generation_and_download(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, actor, _, subject, _, receipt = prepared_account(request, settings, monkeypatch)
    claim = PhoneClaim.objects.create(phone="+34960000096", individual=subject)
    review_all(case, actor)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    english = language == "en"
    submit = "Record copy action" if english else "Registrar acción de copia"
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
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/export/")
            expect(
                page.get_by_role(
                    "heading",
                    name="Prepare private account copy"
                    if english
                    else "Preparar copia privada de cuenta",
                    exact=True,
                )
            ).to_be_visible()
            assert (
                page.locator("[name=copy]").input_value() == ""
                and subject.email not in page.content()
            )
            assert claim.phone not in page.content()
            page.locator("[name=operation]").select_option("inspect_page")
            page.locator("[name=section]").select_option("personal_contacts")
            page.locator("[name=purpose]").fill(
                "Inspect owned phone claims before mobile redaction"
            )
            page.get_by_role("button", name=submit, exact=True).click()
            expect(page.locator("#inspection-page-output")).to_contain_text(claim.phone)
            save_label = "Save page decisions" if english else "Guardar decisiones de página"
            save_form = page.locator("form").filter(
                has=page.get_by_role("button", name=save_label, exact=True)
            )
            contacts = json.loads(save_form.locator("[name=entries]").input_value())
            for contact in contacts:
                contact["phone"] = ""
            save_form.locator("[name=entries]").fill(json.dumps(contacts))
            save_form.locator("[name=reason]").fill("Redact phone values before mobile delivery")
            save_form.get_by_role("button", name=save_label, exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("personal_contacts")
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/export/")
            assert claim.phone not in page.content()
            page.locator("[name=operation]").select_option("generate_pages")
            page.locator("[name=reason]").fill(
                "Generate synthetic copy directly from reviewed pages"
            )
            with page.expect_request(
                lambda item: item.method == "POST" and item.url.endswith("/export/")
            ) as posted:
                page.get_by_role("button", name=submit, exact=True).click()
            from urllib.parse import parse_qs

            fields = parse_qs(posted.value.post_data, keep_blank_values=True)
            assert fields.get("copy", [""]) == [""]
            assert fields["operation"] == ["generate_pages"]
            expect(
                page.get_by_role(
                    "heading",
                    name="Private rights inspection" if english else "Consulta privada de derechos",
                    exact=True,
                )
            ).to_be_visible()
            page.reload()
            assert subject.email not in page.content()
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt.replace("/en/", f"/{language}/", 1))
            with anonymous.expect_download() as item:
                anonymous.get_by_role(
                    "button",
                    name="Download private copy" if english else "Descargar copia privada",
                    exact=True,
                ).click()
            copied = json.loads(Path(item.value.path()).read_text())
            assert copied["schema"] == "subject-account-copy-v1" and copied["partial"] is True
            assert copied["subject_account"]["email"] == ""
            assert copied["profile"] is None and copied["revisions"] == []
            assert copied["account_activity"]["personal_contacts"]
            assert all(
                contact["phone"] == ""
                for contact in copied["account_activity"]["personal_contacts"]
            )
            anonymous.reload()
            assert subject.email not in anonymous.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            assert anonymous.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert RightsExportDownload.objects.filter(export__account_subject=subject).count() == 1
    claim.refresh_from_db()
    assert claim.phone == "+34960000096"
