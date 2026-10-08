"""Localized phone labels with real PG/TCP; delivery explicitly locmem simulation."""

import re
import shutil

import pytest
from django.core import mail
from django.db import connection
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_lifecycle import own
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import PhoneChallenge

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_phone_confirmation_preserves_consumption(
    request, live_server, settings, language
):
    request.getfixturevalue("directory")
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    assert connection.vendor == "postgresql"
    person, _, staff = own()
    path = f"/{language}/person/{person.pk}/phone/"
    button = "Continue" if language == "en" else "Continuar"
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
            assert page.goto(live_server.url + path).status == 200
            expect(
                page.get_by_role(
                    "heading",
                    name="Check phone · simulated SMS"
                    if language == "en"
                    else "Comprobar teléfono · SMS simulado",
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_label(
                    re.compile("^" + ("Phone" if language == "en" else "Teléfono") + ":?$")
                )
            ).to_be_visible()
            page.locator("[name=phone]").fill("invalid")
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.locator(".errorlist")).to_be_visible()
            assert db_sync(lambda: PhoneChallenge.objects.count()) == 0
            page.locator("[name=phone]").fill("600 999 123")
            page.get_by_role("button", name=button, exact=True).click()
            expect(
                page.get_by_role(
                    "heading",
                    name="Confirm simulated code"
                    if language == "en"
                    else "Confirmar código simulado",
                    exact=True,
                )
            ).to_be_visible()
            challenge = db_sync(lambda: PhoneChallenge.objects.get())
            code = mail.outbox[-1].body
            assert challenge.phone == "+34600999123" and code not in challenge.digest
            assert (
                challenge.digest == salted_hmac("phone-otp", code, algorithm="sha256").hexdigest()
            )
            expect(
                page.get_by_label(
                    re.compile("^" + ("Code" if language == "en" else "Código") + ":?$")
                )
            ).to_be_visible()
            page.locator("[name=code]").fill("12")
            page.locator("form").evaluate("e=>e.noValidate=true")
            page.get_by_role("button", name=button, exact=True).click()
            assert db_sync(lambda: PhoneChallenge.objects.get().attempts) == 0
            wrong = "000000" if code != "000000" else "111111"
            page.locator("[name=code]").fill(wrong)
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.locator(".errorlist")).to_be_visible()
            assert db_sync(lambda: PhoneChallenge.objects.get().used_at) is None
            page.locator("[name=code]").fill(code)
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            confirm = page.url
            page.get_by_role("button", name=button, exact=True).click()
            page.wait_for_url(live_server.url + f"/{language}/person/{person.pk}/verification/")
            assert page.request.post(confirm, form=data).status == 400
            page.reload()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    person.refresh_from_db()
    challenge.refresh_from_db()
    assert challenge.used_at and challenge.attempts == 2
    assert (
        person.phone_claim.phone == "+34600999123"
        and person.phone_claim.verification_procedure == "simulator-v1"
    )
