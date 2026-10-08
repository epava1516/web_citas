"""Generic private calendar rejections with native permissions/cursors and real browser."""

import shutil

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import expect, sync_playwright
from test_purpose_calendar import setup_calendar
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_retention_reviews import prepared

from apps.safety.models import PurposeCalendarEvent, RetentionReview, RetentionReviewEvent

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("family", ["purpose", "retention"])
def test_localized_calendar_rejections_private_and_without_effects(
    request, settings, monkeypatch, live_server, language, family
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    if family == "purpose":
        case, _, reviewer, client, _, _, row = setup_calendar(request, settings, monkeypatch)
        queue = reverse("purpose_calendar_queue")
        detail = reverse("purpose_calendar_detail", kwargs={"restriction_id": row.pk})
        events = PurposeCalendarEvent
        date_field = "review_on"
        invalids = [("?attention=all&cursor=invalid", "Invalid cursor", "Cursor inválido")]
    else:
        case, _, reviewer, client, _, _, plan, _ = prepared(request, settings, monkeypatch)
        row = RetentionReview.objects.filter(plan=plan).first()
        queue = reverse("retention_queue")
        detail = reverse("retention_review", kwargs={"review_id": row.pk})
        events = RetentionReviewEvent
        date_field = "next_review_on"
        invalids = [
            ("?attention=unknown", "Invalid attention", "Atención inválida"),
            (
                "?attention=all&cursor=invalid",
                "Invalid calendar cursor",
                "Cursor de calendario inválido",
            ),
        ]
    baseline = row.version, getattr(row, date_field), case.version, case.initial_due_at
    queue = queue.replace("/es/", f"/{language}/", 1).replace("/en/", f"/{language}/", 1)
    detail = detail.replace("/es/", f"/{language}/", 1).replace("/en/", f"/{language}/", 1)
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
                    }
                ]
            )
            page = context.new_page()

            def check(path, status, text):
                response = page.goto(live_server.url + path)
                assert response.status == status
                expect(page.locator("body")).to_have_text(text)
                assert response.headers["cache-control"] == "private, no-store"
                assert response.headers["x-robots-tag"] == "noindex, nofollow"

            for query, en, es in invalids:
                check(queue + query, 400, en if language == "en" else es)
            assert db_sync(lambda: events.objects.count()) == 0
            db_sync(lambda: reviewer.user_permissions.clear())
            for path in [queue, detail]:
                check(path, 403, "Forbidden" if language == "en" else "Acceso denegado")
        finally:
            browser.close()
    row.refresh_from_db()
    case.refresh_from_db()
    assert (row.version, getattr(row, date_field), case.version, case.initial_due_at) == baseline
    assert not events.objects.exists()
