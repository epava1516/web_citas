import shutil
from urllib.parse import urlsplit

import pytest
from django.test import Client
from django.utils import timezone
from django.utils.crypto import salted_hmac
from playwright.sync_api import expect, sync_playwright
from test_account_email_confirmation import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.core.models import RateWindow
from apps.safety.crypto import unseal
from apps.safety.models import RightsAccountEmailConfirmation

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_destination_confirmation_preserves_token_and_account(
    request, settings, monkeypatch, live_server, language
):
    settings.DEBUG = True
    _, _, staff, person, _, path, data = prepared(request, settings, monkeypatch)
    assert staff.post(path, data).status_code == 302
    token = RightsAccountEmailConfirmation.objects.get()
    public_path = urlsplit(unseal(token.encrypted_delivery)["url"]).path
    public_path = public_path.replace("/en/", f"/{language}/", 1)
    raw = public_path.rstrip("/").split("/")[-1]
    old_email = person.subject.email
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + public_path)
            page.reload()
            assert raw not in page.url and raw not in page.content()
            assert "new-subject@example.invalid" not in page.content()
            expect(page.locator("label[for=id_confirmed]")).to_have_text(
                ("Confirm this destination" if language == "en" else "Confirmar este destino") + ":"
            )
            assert (
                db_sync(
                    lambda: RightsAccountEmailConfirmation.objects.get(pk=token.pk).confirmed_at
                )
                is None
            )
            form_data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert page.request.post(page.url, form=form_data).status == 400
            assert (
                db_sync(
                    lambda: RightsAccountEmailConfirmation.objects.get(pk=token.pk).confirmed_at
                )
                is None
            )
            expect(page.locator('[name="confirmed"]')).to_be_visible()
            page.locator('[name="confirmed"]').check()
            page.get_by_role(
                "button",
                name="Confirm destination" if language == "en" else "Confirmar destino",
                exact=True,
            ).click()
            label = "Destination confirmed." if language == "en" else "Destino confirmado."
            expect(page.get_by_role("status")).to_contain_text(label)
            expect(page.locator("form")).to_have_count(0)
            page.reload()
            expect(page.get_by_role("status")).to_contain_text(label)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    token.refresh_from_db()
    person.subject.refresh_from_db()
    assert token.confirmed_at and not token.encrypted_delivery
    assert person.subject.email == old_email

    test_ip = "192.0.2.93"
    key = salted_hmac(
        "rate-window", f"account-email-confirm:{test_ip}", algorithm="sha256"
    ).hexdigest()
    RateWindow.objects.create(key=key, starts_at=timezone.now(), attempts=15)
    result = Client().post(
        f"/{language}/safety/account-email-confirm/{token.pk}/",
        {"confirmed": "on"},
        REMOTE_ADDR=test_ip,
    )
    assert result.status_code == 429
    assert result.content.decode() == (
        "Too many attempts" if language == "en" else "Demasiados intentos"
    )
    assert RateWindow.objects.get(key=key).attempts == 16
    assert "no-store" in result["Cache-Control"]
