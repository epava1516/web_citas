"""Pending portability assessments can be saved through real mobile sessions ES/EN."""

import json
import shutil

import pyotp
import pytest
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_portability_form_localization import captions
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.crypto import unseal
from apps.safety.models import RightsPortabilityAssessment

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_pending_portability_assessment(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, actor, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    original = (case.version, case.status, case.scope_status)
    reason = "PRIVATE / SYNTHETIC_MOBILE_PORTABILITY"
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
                name="Assess portability datasets"
                if english
                else "Evaluar conjuntos de portabilidad",
                exact=True,
            ).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Assess portability datasets"
                    if english
                    else "Evaluar conjuntos de portabilidad",
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_text(
                    "Private favorites" if english else "Favoritos privados", exact=True
                )
            ).to_be_visible()
            assert page.locator("fieldset").count() == 9
            captions(page, language)
            save_button = "Save assessment draft" if english else "Guardar borrador de evaluación"
            page.locator("[name=reason]").fill("short")
            page.locator("form").first.evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.get_by_role("button", name=save_button, exact=True).click()
            assert invalid.value.status == 400
            captions(page, language)
            assert db_sync(lambda: RightsPortabilityAssessment.objects.count()) == 0
            page.locator("[name=datasets-0-evidence]").fill("Literal / pending evidence")
            page.locator("[name=reason]").fill(reason)
            page.get_by_role(
                "button",
                name="Save assessment draft" if english else "Guardar borrador de evaluación",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Assessment draft saved" if english else "Borrador de evaluación guardado"
            )
            captions(page, language)
            row_id = db_sync(lambda: RightsPortabilityAssessment.objects.get().pk)
            page.locator("[name=assessment_id]").fill(str(row_id))
            page.locator("[name=purpose]").fill(
                "Inspect current synthetic assessment before review"
            )
            with page.expect_response(lambda r: r.request.method == "POST") as inspected:
                page.get_by_role(
                    "button",
                    name="Record access and inspect assessment"
                    if english
                    else "Registrar acceso y consultar evaluación",
                    exact=True,
                ).click()
            assert inspected.value.status == 200
            captions(page, language)
            expect(page.get_by_text("Literal / pending evidence", exact=True)).to_be_visible()
            assert page.locator("article").count() == 9
            for row in page.locator("article").all():
                expect(row.locator("p").first).to_have_text(
                    "Pending · Unknown · Unknown"
                    if english
                    else "Pendiente · Desconocido · Desconocido"
                )
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/")
            page.reload()
            assert "Literal / pending evidence" not in page.content()
            assert reason not in page.content()
            csrf = page.locator("[name=csrfmiddlewaretoken]").first.input_value()
            db_sync(
                lambda: actor.user_permissions.remove(
                    Permission.objects.get(codename="execute_rights_request")
                )
            )
            response = page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/"
            )
            assert response.status == 403 and page.locator("body").inner_text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = page.request.post(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/portability/",
                form={"csrfmiddlewaretoken": csrf},
            )
            assert response.status == 403 and response.text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    row = RightsPortabilityAssessment.objects.get()
    assert any(
        item["evidence"] == "Literal / pending evidence"
        for item in unseal(row.encrypted_assessment).values()
    )
    assert all(item["automated"] is None for item in unseal(row.encrypted_assessment).values())
    assert all(item["status"] == "pending" for item in unseal(row.encrypted_assessment).values())
    case.refresh_from_db()
    assert (case.version, case.status, case.scope_status) == original
