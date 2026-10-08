"""Generic private denials and unsupported kind with native PostgreSQL browser requests."""

import shutil

import pytest
from django.db import connection
from playwright.sync_api import sync_playwright
from test_processing_review import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.models import RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_processing_private_rejections_localized(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    case, _, _, plan, reviewer, client = prepared(request, settings, monkeypatch)
    case.kind = "access"
    case.save(update_fields=["kind"])
    before = (case.version, case.status, case.initial_due_at, RightsAction.objects.count())
    token = client.get(f"/{language}/account/").cookies.get("csrftoken") or client.cookies.get(
        "csrftoken"
    )
    assert token is not None
    base = f"/{language}/moderation/rights/{case.pk}/processing/"
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

            def check(path, code, body):
                url = live_server.url + path
                response = page.goto(url)
                assert response.status == code and page.locator("body").inner_text() == body
                assert response.headers["cache-control"] == "private, no-store"
                assert response.headers["x-robots-tag"] == "noindex, nofollow"
                posted = page.request.post(
                    url, form={"csrfmiddlewaretoken": token.value}, headers={"Referer": url}
                )
                assert posted.status == code and posted.text() == body
                assert posted.headers["cache-control"] == "private, no-store"

            check(
                base,
                409,
                "Unsupported request type" if language == "en" else "Tipo de solicitud no admitido",
            )
            db_sync(lambda: reviewer.user_permissions.clear())
            for path in [base, base + f"{plan.pk}/", base + f"{plan.pk}/execute/"]:
                check(path, 403, "Forbidden" if language == "en" else "Acceso denegado")
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at, RightsAction.objects.count()) == before
    assert case.kind == "access"
