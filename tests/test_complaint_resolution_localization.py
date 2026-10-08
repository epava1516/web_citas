"""Localized resolution presentation, with actual private audited source and PG effects."""

import re
import shutil

import pytest
from django.conf import settings
from django.db import connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_complaint_resolutions import REASON, RESPONSE, listing_case
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.crypto import unseal
from apps.safety.models import ComplaintAction, ComplaintResolution

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_resolution_localization_preserves_private_response_and_exact_replay(
    live_server, request, language
):
    assert connection.vendor == "postgresql"
    complaint, person, target, _, staff, receipt = listing_case(request)
    inspect_path = f"/{language}/moderation/complaints/{complaint.pk}/"
    path = inspect_path + "resolve/"
    receipt = receipt.replace("/en/", f"/{language}/")
    labels = {
        "outcome": ("Resultado", "Outcome"),
        "reason": ("Motivo interno", "Internal reason"),
        "response": (
            "Respuesta motivada al solicitante, sin información de terceros",
            "Motivated response to requester, without third party information",
        ),
        "redaction_confirmed": (
            "He revisado la respuesta y eliminado datos de terceros y notas internas",
            "I reviewed the response and removed third party information and internal notes",
        ),
    }
    button = "Record resolution" if language == "en" else "Registrar resolución"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    }
                ]
            )
            page = context.new_page()
            assert page.goto(live_server.url + inspect_path).status == 200
            page.locator("[name=purpose]").fill(
                "Read current linked review evidence before independent resolution"
            )
            page.get_by_role(
                "button",
                name="Record access and inspect"
                if language == "en"
                else "Registrar consulta y ver",
                exact=True,
            ).click()
            page.wait_for_function(
                '() => { const images=Array.from(document.querySelectorAll("img"));return images.length>0 && images.every(e=>e.complete && e.naturalWidth>0); }'
            )
            assert page.goto(live_server.url + path).status == 200
            for name, pair in labels.items():
                expect(
                    page.get_by_label(
                        re.compile("^" + re.escape(pair[language == "en"]) + ":?$"), exact=True
                    )
                ).to_be_visible()
            expected = [
                ("upheld", "Uphold decision" if language == "en" else "Mantener decisión"),
                (
                    "reconsidered",
                    "Reconsider decision" if language == "en" else "Reconsiderar decisión",
                ),
                (
                    "unidentified",
                    "Reference unidentified" if language == "en" else "Referencia sin identificar",
                ),
            ]
            assert page.locator("[name=outcome] option").evaluate_all(
                "es=>es.map(e=>[e.value,e.textContent])"
            ) == [list(p) for p in expected]
            page.locator("[name=outcome]").select_option("reconsidered")
            page.locator("[name=reason]").fill(REASON)
            page.locator("[name=response]").fill("short")
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert posted.value.status == 400
            assert db_sync(lambda: ComplaintResolution.objects.count()) == 0
            page.locator("[name=response]").fill(RESPONSE)
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert (
                posted.value.status == 400
            )  # Redaction confirmation remains required independently.
            assert db_sync(lambda: ComplaintResolution.objects.count()) == 0
            page.locator("[name=redaction_confirmed]").check()
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert posted.value.status == 302
            page.wait_for_url(live_server.url + inspect_path)
            assert (
                page.request.post(live_server.url + path, form=data, max_redirects=0).status == 302
            )
            assert db_sync(lambda: ComplaintResolution.objects.count()) == 1
            record = db_sync(lambda: ComplaintResolution.objects.get())
            assert (
                RESPONSE not in record.encrypted_response
                and unseal(record.encrypted_response)["response"] == RESPONSE
            )
            assert db_sync(lambda: ComplaintAction.objects.filter(operation="resolve").count()) == 1
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            assert anonymous.goto(live_server.url + receipt).status == 200
            expect(anonymous.get_by_text(RESPONSE, exact=True)).to_be_visible()
            assert REASON not in anonymous.content() and target.reason not in anonymous.content()
            anonymous.reload()
            expect(anonymous.get_by_text(RESPONSE, exact=True)).to_be_visible()
            assert anonymous.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    complaint.refresh_from_db()
    person.listing.refresh_from_db()
    assert complaint.status == "resolved" and person.listing.status == "pending"
    assert Client().get(f"/en/listing/{person.listing.pk}/").status_code == 404
