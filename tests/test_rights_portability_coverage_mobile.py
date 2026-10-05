"""Actual Chromium mobile coverage form, with synthetic authenticated sessions."""

import shutil

import pytest
from django.conf import settings as django_settings
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_export_races import prepared_selection

from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilityCoverage

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only,images", [(False, False), (True, False), (False, True)])
def test_mobile_guided_coverage_save_and_clean_get(
    live_server, request, settings, monkeypatch, language, account_only, images
):
    settings.DEBUG = True
    case, author, _, decision, _, _, _ = prepared_selection(
        request, settings, monkeypatch, account_only
    )
    client = Client()
    client.force_login(author)
    session = client.session
    session["mfa_version"] = author.mfa_version
    session.save()
    cookie = client.cookies[django_settings.SESSION_COOKIE_NAME].value
    original = case.version, case.status, case.initial_due_at
    english = language == "en"
    url = live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/coverage/"
    if images:
        url += "images/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": django_settings.SESSION_COOKIE_NAME,
                        "value": cookie,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            page.goto(url)
            expect(
                page.get_by_role(
                    "heading",
                    name=("Justify omitted images" if english else "Justificar imágenes omitidas")
                    if images
                    else (
                        "Justify portability omissions"
                        if english
                        else "Justificar omisiones de portabilidad"
                    ),
                    exact=True,
                )
            ).to_be_visible()
            assert page.locator("fieldset").count() == 0
            page.locator("[name=review]").select_option(str(decision.pk))
            if not images:
                page.locator("[name=dataset]").select_option(
                    "subject_account" if account_only else "profile"
                )
            page.locator("[name=purpose]").fill(
                "Inspect synthetic omissions before independent review"
            )
            page.get_by_role(
                "button",
                name="Inspect omitted fields" if english else "Consultar campos omitidos",
                exact=True,
            ).click()
            expect(page.locator("fieldset").first).to_be_visible()
            page.locator("[name=paths]").first.check()
            fields = page.locator("fieldset").first
            fields.locator("select[name$=-basis]").select_option("other")
            fields.locator("select[name$=-origin]").select_option("inferred")
            for suffix in ("automated", "subject_related", "third_party_reviewed"):
                fields.locator(f"select[name$=-{suffix}]").select_option("yes")
            fields.locator("textarea[name$=-reason]").fill(
                "Synthetic omission exclusion without production factual claim"
            )
            fields.locator("textarea[name$=-evidence]").fill("PRIVATE_MOBILE_COVERAGE_EVIDENCE")
            page.locator("#id_reason").fill("Save synthetic coverage for later independent review")
            page.get_by_role(
                "button",
                name="Save justified omissions on this page"
                if english
                else "Guardar omisiones justificadas de esta página",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Coverage draft saved" if english else "Borrador de cobertura guardado"
            )
            page.goto(url)
            assert "PRIVATE_MOBILE_COVERAGE_EVIDENCE" not in page.content()
            assert page.locator("fieldset").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    row = RightsPortabilityCoverage.objects.get(request=case)
    body = unseal(row.encrypted_coverage)
    assert body["allow_partial"] is True
    assert "PRIVATE_MOBILE_COVERAGE_EVIDENCE" in str(
        body["image_omissions"] if images else body["omissions"]
    )
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
