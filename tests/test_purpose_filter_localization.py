"""Finite calendar filter presentation, reusing closed cursor/pagination evidence."""

import shutil
from datetime import timedelta

import pytest
from django.db import connection
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_purpose_calendar import setup_calendar
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.models import PurposeCalendarEvent

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_calendar_filters_keep_selection_and_defaults(
    request, settings, monkeypatch, live_server, language
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    case, _, _, client, _, _, restriction = setup_calendar(request, settings, monkeypatch)
    restriction.review_on = timezone.localdate() + timedelta(days=3)
    restriction.save(update_fields=["review_on"])
    baseline = (
        restriction.version,
        restriction.active,
        restriction.review_on,
        case.version,
        case.initial_due_at,
    )
    path = (
        reverse("purpose_calendar_queue")
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
                "attention": (
                    ("Atención", "Attention"),
                    [
                        ["due", "Vencidas", "Due"],
                        ["soon", "Próximos siete días", "Next seven days"],
                        ["all", "Todas", "All"],
                    ],
                ),
                "purpose": (
                    ("Finalidad", "Purpose"),
                    [["", "Todas", "All"], ["account_preferences", "Preferencias", "Preferences"]],
                ),
                "mode": (
                    ("Medida", "Measure"),
                    [
                        ["", "Todos", "All"],
                        ["restrict", "Limitación", "Restriction"],
                        ["cease", "Cese", "Cessation"],
                    ],
                ),
            }
            for name, (labels, choices) in definitions.items():
                expect(page.locator(f"label[for=id_{name}]")).to_have_text(labels[english] + ":")
                assert page.locator(f"[name={name}] option").evaluate_all(
                    "xs=>xs.map(e=>[e.value,e.textContent])"
                ) == [[value, en if english else es] for value, es, en in choices]
            expect(page.locator("[name=attention]")).to_have_value("due")
            link = page.get_by_role(
                "link", name="Follow up" if english else "Seguimiento", exact=True
            )
            expect(link).to_have_count(0)
            button = page.get_by_role("button", name="Filter" if english else "Filtrar", exact=True)
            for attention in ["soon", "all"]:
                page.locator("[name=attention]").select_option(attention)
                page.locator("[name=purpose]").select_option("account_preferences")
                page.locator("[name=mode]").select_option(restriction.mode)
                button.click()
                expect(link).to_have_count(1)
                expect(link).to_have_attribute(
                    "href",
                    reverse("purpose_calendar_detail", kwargs={"restriction_id": restriction.pk})
                    .replace("/es/", f"/{language}/", 1)
                    .replace("/en/", f"/{language}/", 1),
                )
                page.reload()
                expect(page.locator("[name=attention]")).to_have_value(attention)
                expect(link).to_have_count(1)
            page.locator("[name=mode]").select_option(
                "cease" if restriction.mode == "restrict" else "restrict"
            )
            button.click()
            expect(link).to_have_count(0)
            page.locator("[name=attention] option[value=all]").evaluate("e=>e.value='unknown'")
            page.locator("[name=attention]").select_option("unknown")
            with page.expect_response(
                lambda r: r.request.method == "GET" and "attention=unknown" in r.url
            ) as r:
                button.click()
            assert r.value.status == 400
            expect(page.locator("body")).to_have_text(
                "Invalid filters" if english else "Filtros inválidos"
            )
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
    ) == baseline
    assert not PurposeCalendarEvent.objects.exists()
