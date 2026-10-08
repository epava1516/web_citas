"""Private current permission denial; publication covers initial guard only, no fake hold workflow."""

import shutil

import pytest
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_purpose_exception_review import ready
from test_purpose_release import prepared
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync

from apps.safety.models import RightsAction

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("family", ["exception", "account_release", "publication_initial"])
def test_private_measure_denials_localized_and_effect_free(
    request, settings, monkeypatch, live_server, language, family
):
    assert connection.vendor == "postgresql"
    settings.DEBUG = True
    if family == "exception":
        case, _, _, plan, _, proposal, reviewer, client = ready(request, settings, monkeypatch)
        paths = [
            f"/{language}/moderation/rights/{case.pk}/exceptions/prepare/{plan.pk}/",
            f"/{language}/moderation/rights/{case.pk}/exceptions/{proposal.pk}/review/",
        ]
        from django.urls import reverse

        paths = [
            reverse("purpose_exception_prepare", kwargs={"case_id": case.pk, "plan_id": plan.pk}),
            reverse(
                "purpose_exception_review", kwargs={"case_id": case.pk, "proposal_id": proposal.pk}
            ),
        ]
        paths = [
            x.replace("/es/", f"/{language}/", 1).replace("/en/", f"/{language}/", 1) for x in paths
        ]
    else:
        case, _, reviewer, client, _, _, restriction = prepared(request, settings, monkeypatch)
        if family == "account_release":
            paths = [
                f"/{language}/moderation/rights/{case.pk}/restrictions/",
                f"/{language}/moderation/rights/{case.pk}/restrictions/{restriction.pk}/release/",
            ]
        else:
            # The route must deny before looking up a hold. Existing full hold flows are already verified.
            paths = [
                f"/{language}/moderation/rights/{case.pk}/publication-purpose/{2147483647}/release/"
            ]
    before = (case.version, case.status, case.initial_due_at, RightsAction.objects.count())
    reviewer.user_permissions.clear()
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
            for path in paths:
                url = live_server.url + path
                response = page.goto(url)
                assert response.status == 403
                expect(page.locator("body")).to_have_text(
                    "Forbidden" if language == "en" else "Acceso denegado"
                )
                assert response.headers["cache-control"] == "private, no-store"
                assert response.headers["x-robots-tag"] == "noindex, nofollow"
                # Permission precedes form binding. CSRF remains in force for the independent POST check.
                token = db_sync(
                    lambda: (client.get(f"/{language}/account/"), client.cookies.get("csrftoken"))[
                        1
                    ]
                )
                assert token is not None
                context.add_cookies(
                    [{"name": "csrftoken", "value": token.value, "url": live_server.url}]
                )
                posted = page.request.post(
                    url, form={"csrfmiddlewaretoken": token.value}, headers={"Referer": url}
                )
                if family == "account_release" and path == paths[0]:
                    assert posted.status == 405 and posted.headers["allow"] == "GET"
                    assert posted.text() == ""
                    continue
                assert posted.status == 403
                assert posted.text() == ("Forbidden" if language == "en" else "Acceso denegado")
        finally:
            browser.close()
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at, RightsAction.objects.count()) == before
