"""Real PostgreSQL/TCP localization of existing publication and review operations."""

import re
import shutil

import pytest
from django.conf import settings
from django.db import connection
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_discovery import directory  # noqa: F401
from test_drafts import scenario  # noqa: F401
from test_lifecycle import own
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_submissions import prepared  # noqa: F401

from apps.listings.models import LifecycleAction, ModerationDecision

pytestmark = pytest.mark.django_db(transaction=True)


def browser_context(playwright, staff, url):
    browser = playwright.chromium.launch(
        executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
    )
    context = browser.new_context(viewport={"width": 390, "height": 844})
    context.add_cookies(
        [
            {
                "name": settings.SESSION_COOKIE_NAME,
                "value": staff.cookies[settings.SESSION_COOKIE_NAME].value,
                "url": url,
            }
        ]
    )
    return browser, context


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_publication_actions_persist_and_preserve_guards(request, live_server, language):
    request.getfixturevalue("directory")
    assert connection.vendor == "postgresql"
    _, listing, staff = own()
    path = f"/{language}/listing/{listing.pk}/manage/"
    before = LifecycleAction.objects.count()
    expected = ["pause", "resume", "renew", "withdraw", "available", "unavailable"]
    with sync_playwright() as playwright:
        browser, context = browser_context(playwright, staff, live_server.url)
        try:
            page = context.new_page()
            assert page.goto(live_server.url + path).status == 200
            expect(
                page.get_by_label(
                    re.compile("^" + ("Operation" if language == "en" else "Operación") + ":?$")
                )
            ).to_be_visible()
            assert (
                page.locator("[name=operation] option").evaluate_all("es=>es.map(e=>e.value)")
                == expected
            )
            assert " / " not in page.locator("[name=operation] option").all_text_contents()[0]
            expect(
                page.get_by_label(
                    re.compile(
                        "^"
                        + re.escape(
                            "I confirm approved information is still correct"
                            if language == "en"
                            else "Confirmo que los datos aprobados siguen siendo correctos"
                        )
                        + ":?$"
                    ),
                    exact=True,
                )
            ).to_be_visible()
            invalid = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))") | {
                "operation": "unknown"
            }
            assert page.request.post(live_server.url + path, form=invalid).status == 400
            assert db_sync(lambda: LifecycleAction.objects.count()) == before
            for operation, status in [
                ("available", "published"),
                ("pause", "paused"),
                ("resume", "published"),
                ("withdraw", "withdrawn"),
            ]:
                page.locator("[name=operation]").select_option(operation)
                page.get_by_role(
                    "button",
                    name="Apply action" if language == "en" else "Aplicar acción",
                    exact=True,
                ).click()
                expect(page.get_by_text(status, exact=True)).to_be_visible()
                page.reload()
                expect(page.get_by_text(status, exact=True)).to_be_visible()
            assert (
                page.request.get(live_server.url + f"/{language}/listing/{listing.pk}/").status
                == 404
            )
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert LifecycleAction.objects.count() == before + 4


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_moderation_records_exact_public_revision(request, live_server, language):
    _, _, revision, moderator, _ = request.getfixturevalue("pending")
    assert connection.vendor == "postgresql"
    staff = Client()
    staff.force_login(moderator)
    session = staff.session
    session["mfa_version"] = moderator.mfa_version
    session.save()
    assert moderator.mfa_enabled  # Real persisted synthetic session, not a new TOTP proof.
    path = f"/{language}/moderation/listings/{revision.pk}/"
    with sync_playwright() as playwright:
        browser, context = browser_context(playwright, staff, live_server.url)
        try:
            page = context.new_page()
            assert page.goto(live_server.url + path).status == 200
            expect(
                page.get_by_label(
                    re.compile("^" + ("Outcome" if language == "en" else "Resultado") + ":?$")
                )
            ).to_be_visible()
            expect(
                page.get_by_label(
                    re.compile("^" + ("Reason" if language == "en" else "Motivo") + ":?$")
                )
            ).to_be_visible()
            expected = [
                ["", "Choose" if language == "en" else "Selecciona"],
                ["approved", "Approve" if language == "en" else "Aprobar"],
                ["rejected", "Reject" if language == "en" else "Rechazar"],
            ]
            assert (
                page.locator("[name=outcome] option").evaluate_all(
                    "es=>es.map(e=>[e.value,e.textContent])"
                )
                == expected
            )
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role(
                    "button",
                    name="Record decision" if language == "en" else "Registrar decisión",
                    exact=True,
                ).click()
            assert posted.value.status == 400
            assert db_sync(lambda: ModerationDecision.objects.count()) == 0
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill(
                "Synthetic independent moderator review of current publication"
            )
            page.get_by_role(
                "button",
                name="Record decision" if language == "en" else "Registrar decisión",
                exact=True,
            ).click()
            expect(
                page.get_by_text(
                    "Synthetic independent moderator review of current publication", exact=True
                )
            ).to_be_visible()
            page.reload()
            guest = browser.new_page(viewport={"width": 390, "height": 844})
            assert (
                guest.goto(live_server.url + f"/{language}/listing/{revision.listing_id}/").status
                == 200
            )
            expect(guest.get_by_role("heading", name=revision.title, exact=True)).to_be_visible()
        finally:
            browser.close()
    record = ModerationDecision.objects.get()
    assert record.revision_id == revision.pk and record.reviewer_id == moderator.pk
