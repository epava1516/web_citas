"""Mobile account inventory, reviewed erasure and surviving rights response channel."""

import json
import shutil
from datetime import timedelta

import pyotp
import pytest
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_erasure_plans import BASIS, REASON, SCOPE
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import TEXT

from apps.core.models import AccountToken, Person, RecoveryCode
from apps.listings.models import Favorite, Listing
from apps.safety.models import ErasureExecution, ErasureInventory, ErasurePlan, RightsResponse

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_account_inventory_plan_execution_and_response(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, _, _, subject, _, receipt = prepared_account(request, settings, monkeypatch, "erase")
    AccountToken.objects.create(
        user=subject,
        purpose="reset",
        digest="0" * 64,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    RecoveryCode.objects.create(user=subject, digest="1" * 64)
    Favorite.objects.create(user=subject, listing=Listing.objects.first())
    profiles = list(Person.objects.order_by("pk").values())
    before_versions = subject.session_version, subject.mfa_version
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    moderator = credentials["accounts"]["moderator"]
    review_date = (timezone.localdate() + timedelta(days=30)).isoformat()
    english = language == "en"
    purposes = {"account", "authentication", "account_preferences", "transient_copy"}
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
            page.goto(
                live_server.url + f"/{language}/moderation/rights/{case.pk}/erasure-inventory/"
            )
            assert subject.email not in page.content() and page.locator("table").count() == 0
            page.locator("[name=purpose]").fill(REASON)
            page.get_by_role(
                "button",
                name="Record and inspect inventory"
                if english
                else "Registrar y consultar inventario",
                exact=True,
            ).click()
            expect(page.locator("table")).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            page.get_by_role(
                "link",
                name="Review erasure and retention decisions"
                if english
                else "Revisar decisiones de supresión y conservación",
                exact=True,
            ).click()
            for fieldset in page.locator("fieldset").all():
                purpose = fieldset.locator("[name$=-purpose]").input_value()
                selected = purpose in purposes
                fieldset.locator("select").select_option("erase" if selected else "retain")
                fieldset.locator("[name$=-scope]").fill(SCOPE)
                fieldset.locator("[name$=-basis]").fill(BASIS)
                fieldset.locator("[name$=-reason]").fill(REASON)
                if not selected:
                    fieldset.locator("[name$=-review_on]").fill(review_date)
            page.get_by_role(
                "button",
                name="Record per-purpose decisions"
                if english
                else "Registrar decisiones por finalidad",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_have_text(
                "Plan recorded; execution pending"
                if english
                else "Plan registrado; ejecución pendiente"
            )
            page.get_by_role(
                "link",
                name="Execute reviewed supported scopes"
                if english
                else "Ejecutar ámbitos revisados implementados",
                exact=True,
            ).click()
            assert page.locator("[name=purposes][value=publication]").count() == 0
            for purpose in purposes:
                page.locator(f"[name=purposes][value={purpose}]").check()
            page.locator("[name=reason]").fill(REASON)
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
            expect(page.get_by_role("status")).to_have_text(
                "Selected scopes executed; request remains open"
                if english
                else "Ámbitos seleccionados ejecutados; solicitud abierta"
            )
            page.goto(page.url)
            assert page.get_by_role("status").count() == 0 and subject.email not in page.content()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Review current open request after scoped account erasure"
            )
            page.get_by_role(
                "button",
                name="Record access and inspect" if english else "Registrar consulta y ver",
                exact=True,
            ).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Restricted information" if english else "Información restringida",
                    exact=True,
                )
            ).to_be_visible()
            page.get_by_role(
                "link",
                name="Issue private response" if english else "Emitir respuesta privada",
                exact=True,
            ).click()
            page.locator("[name=kind]").select_option("progress")
            page.locator("[name=reason]").fill(REASON)
            page.locator("[name=response]").fill(TEXT)
            page.locator("[name=redaction_confirmed]").check()
            page.get_by_role(
                "button",
                name="Record motivated response" if english else "Registrar respuesta motivada",
                exact=True,
            ).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Private rights inspection" if english else "Consulta privada de derechos",
                    exact=True,
                )
            ).to_be_visible()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt.replace("/en/", f"/{language}/", 1))
            expect(anonymous.get_by_text(TEXT, exact=True)).to_be_visible()
            anonymous.reload()
            expect(anonymous.get_by_text(TEXT, exact=True)).to_be_visible()
            assert REASON not in anonymous.content()
            assert anonymous.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    subject.refresh_from_db()
    case.refresh_from_db()
    assert (subject.session_version, subject.mfa_version) == tuple(
        value + 1 for value in before_versions
    )
    assert subject.account_erased_at and not subject.is_active and case.status == "reviewing"
    assert (
        ErasureInventory.objects.filter(account_subject=subject).count()
        == ErasurePlan.objects.count()
        == ErasureExecution.objects.filter(account_subject=subject).count()
        == RightsResponse.objects.filter(request=case).count()
        == 1
    )
    assert list(Person.objects.order_by("pk").values()) == profiles
