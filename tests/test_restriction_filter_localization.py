"""Prepared per-case queue selection through native private HTTP, no new volume run."""

import shutil
from datetime import timedelta

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_purpose_release import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.models import PurposeReleaseProposal

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_per_case_filters_keep_measures_and_authority(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    case, _, reviewer, client, _, _, restriction = prepared(request, settings, monkeypatch)
    restriction.review_on = timezone.localdate() + timedelta(days=3)
    restriction.save(update_fields=["review_on"])
    before = (
        restriction.version,
        restriction.active,
        restriction.review_on,
        case.version,
        case.initial_due_at,
    )
    path = (
        reverse("purpose_restriction_queue", kwargs={"case_id": case.pk})
        .replace("/es/", f"/{language}/", 1)
        .replace("/en/", f"/{language}/", 1)
    )
    english = language == "en"
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
            url = live_server.url + path
            page.goto(url)
            definitions = {
                "state": (
                    ("Estado", "State"),
                    [
                        ("", "Activas", "Active"),
                        ("active", "Activas", "Active"),
                        ("released", "Levantadas", "Released"),
                    ],
                ),
                "due": (
                    ("Revisión", "Review"),
                    [
                        ("", "Todas las fechas", "All dates"),
                        ("due", "Revisión vencida", "Review due"),
                    ],
                ),
                "purpose": (
                    ("Finalidad", "Purpose"),
                    [("", "Todas", "All"), ("account_preferences", "Preferencias", "Preferences")],
                ),
            }
            for name, (labels, choices) in definitions.items():
                expect(page.locator(f"label[for=id_{name}]")).to_have_text(labels[english] + ":")
                assert page.locator(f"[name={name}] option").evaluate_all(
                    "xs=>xs.map(e=>[e.value,e.textContent])"
                ) == [[value, en if english else es] for value, es, en in choices]
            expect(page.locator("[name=state]")).to_have_value("")
            link = page.get_by_role(
                "link", name="Review restriction" if english else "Revisar restricción", exact=True
            )
            expect(link).to_have_count(1)
            button = page.get_by_role("button", name="Filter" if english else "Filtrar", exact=True)
            page.locator("[name=state]").select_option("released")
            button.click()
            expect(link).to_have_count(0)
            page.locator("[name=state]").select_option("active")
            page.locator("[name=purpose]").select_option("account_preferences")
            page.locator("[name=due]").select_option("due")
            button.click()
            expect(link).to_have_count(0)
            page.locator("[name=due]").select_option("")
            button.click()
            page.reload()
            expect(link).to_have_count(1)
            expect(page.locator("[name=state]")).to_have_value("active")
            expect(page.locator("[name=purpose]")).to_have_value("account_preferences")
            page.locator("[name=state] option[value=active]").evaluate("e=>e.value='unknown'")
            page.locator("[name=state]").select_option("unknown")
            with page.expect_response(
                lambda r: r.request.method == "GET" and "state=unknown" in r.url
            ) as r:
                button.click()
            assert r.value.status == 400
            expect(page.locator(".errorlist")).to_be_visible()
            expect(link).to_have_count(0)
            db_sync(lambda: reviewer.user_permissions.clear())
            assert page.goto(url).status == 403
        finally:
            browser.close()
    restriction.refresh_from_db()
    case.refresh_from_db()
    assert (
        restriction.version,
        restriction.active,
        restriction.review_on,
        case.version,
        case.initial_due_at,
    ) == before
    assert not PurposeReleaseProposal.objects.exists()
