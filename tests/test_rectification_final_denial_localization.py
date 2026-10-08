"""Private rectification final initial permission denial preserves effects and CSRF."""

import shutil

import pytest
from django.db import connection
from playwright.sync_api import sync_playwright
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.models import RightsAction, RightsResponse

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_rectification_final_denial_private_and_effect_free(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    case, actor, client, _, _, _ = prepared_account(request, settings, monkeypatch, "rectify")
    before = (
        case.version,
        case.response_version,
        case.status,
        case.initial_due_at,
        RightsAction.objects.count(),
        RightsResponse.objects.count(),
    )
    client.get(f"/{language}/account/")
    token = client.cookies.get("csrftoken")
    assert token is not None
    actor.user_permissions.clear()
    path = f"/{language}/moderation/rights/{case.pk}/rectification/final/"
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            context.add_cookies(
                [
                    {
                        "name": settings.SESSION_COOKIE_NAME,
                        "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                        "url": live_server.url,
                    },
                    {"name": "csrftoken", "value": token.value, "url": live_server.url},
                ]
            )
            page = context.new_page()
            url = live_server.url + path
            response = page.goto(url)
            expected = "Forbidden" if language == "en" else "Acceso denegado"
            assert response.status == 403 and page.locator("body").inner_text() == expected
            posted = page.request.post(
                url, form={"csrfmiddlewaretoken": token.value}, headers={"Referer": url}
            )
            assert posted.status == 403 and posted.text() == expected
            for item in [response, posted]:
                assert item.headers["cache-control"] == "private, no-store"
                assert item.headers["x-robots-tag"] == "noindex, nofollow"
        finally:
            browser.close()
    case.refresh_from_db()
    assert (
        case.version,
        case.response_version,
        case.status,
        case.initial_due_at,
        RightsAction.objects.count(),
        RightsResponse.objects.count(),
    ) == before
