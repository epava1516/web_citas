"""Localized current match review with private images and actual PostgreSQL effects."""

import re
import shutil

import pytest
from django.conf import settings
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_match_review import conflict  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.mediafiles.models import Match, MatchResolution

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_match_review_preserves_pair_authority_and_state(request, live_server, language):
    original, revision, match, moderator, staff, _, _ = request.getfixturevalue("conflict")
    assert connection.vendor == "postgresql"
    path = f"/{language}/moderation/matches/{match.pk}/"
    reason = "Synthetic authorizations for both people reviewed independently"
    reference = "synthetic-match-review-reference"
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
            for label in [
                ("Outcome" if language == "en" else "Resultado"),
                ("Reason" if language == "en" else "Motivo"),
                ("Review reference" if language == "en" else "Referencia de revisión"),
            ]:
                expect(page.get_by_label(re.compile("^" + label + ":?$"))).to_be_visible()
            expected = [
                ["", "Choose" if language == "en" else "Selecciona"],
                [
                    "false_positive",
                    "Visual false positive" if language == "en" else "Falso positivo visual",
                ],
                [
                    "distinct_people",
                    "Distinct authorized people"
                    if language == "en"
                    else "Personas distintas autorizadas",
                ],
                [
                    "conflict",
                    "Conflict; restrict publication"
                    if language == "en"
                    else "Conflicto; restringir publicación",
                ],
            ]
            assert (
                page.locator("[name=outcome] option").evaluate_all(
                    "es=>es.map(e=>[e.value,e.textContent])"
                )
                == expected
            )
            page.wait_for_function(
                '() => { const es=Array.from(document.querySelectorAll("img")); return es.length===2 && es.every(e=>e.complete && e.naturalWidth>0); }'
            )
            assert (
                page.request.get(live_server.url + path + "candidate/image/").headers[
                    "cache-control"
                ]
                == "private, no-store"
            )
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role(
                    "button",
                    name="Record resolution" if language == "en" else "Registrar resolución",
                    exact=True,
                ).click()
            assert (
                posted.value.status == 400 and db_sync(lambda: MatchResolution.objects.count()) == 0
            )
            page.locator("[name=outcome]").select_option("distinct_people")
            page.locator("[name=reason]").fill(reason)
            page.locator("[name=evidence_reference]").fill(reference)
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            page.get_by_role(
                "button",
                name="Record resolution" if language == "en" else "Registrar resolución",
                exact=True,
            ).click()
            expect(page.get_by_text(reason, exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_text(reason, exact=True)).to_be_visible()
            assert page.request.post(live_server.url + path, form=data).status == 400
            assert db_sync(lambda: MatchResolution.objects.count()) == 2
            assert (
                browser.new_page()
                .request.get(live_server.url + f"/{language}/listing/{revision.listing_id}/")
                .status
                == 404
            )
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert not Match.objects.filter(resolved_at__isnull=True).exists()
    assert (
        MatchResolution.objects.filter(
            outcome="distinct_people",
            reviewer=moderator,
            reason=reason,
            evidence_reference=reference,
        ).count()
        == 2
    )
    revision.refresh_from_db()
    original.refresh_from_db()
    assert revision.status == "pending" and original.status == "approved"
