"""Localized existing appeal cycle with real PG sessions and TCP Chromium."""

import re
import shutil

import pytest
from django.conf import settings
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_agency_appeals import rejected_agency  # noqa: F401
from test_appeals import rejected  # noqa: F401
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_match_review import conflict  # noqa: F401
from test_organization_review import organization  # noqa: F401
from test_photo_appeals import photo_case  # noqa: F401
from test_photo_restrictions import restricted  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.listings.models import Appeal

pytestmark = pytest.mark.django_db(transaction=True)


def authenticated_context(browser, staff, url):
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
    return context


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_appeal_and_independent_review_preserve_authority_and_state(
    request, live_server, language
):
    _, owner, revision, original, reviewer, independent = request.getfixturevalue("rejected")
    assert connection.vendor == "postgresql"
    decision = revision.decisions.get()
    version = revision.edit_version
    path = f"/{language}/draft/decisions/{decision.pk}/appeal/"
    explanation = "Synthetic manager requests independent reconsideration of rejected version"
    reason = "Synthetic independent reviewer authorizes a new review, not publication"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = authenticated_context(browser, owner, live_server.url)
            page = context.new_page()
            assert page.goto(live_server.url + path).status == 200
            expect(
                page.get_by_label(
                    re.compile("^" + ("Explanation" if language == "en" else "Explicación") + ":?$")
                )
            ).to_be_visible()
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role(
                    "button",
                    name="Submit appeal" if language == "en" else "Enviar reclamación",
                    exact=True,
                ).click()
            assert posted.value.status == 400 and db_sync(lambda: Appeal.objects.count()) == 0
            page.locator("[name=explanation]").fill(explanation)
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            page.get_by_role(
                "button",
                name="Submit appeal" if language == "en" else "Enviar reclamación",
                exact=True,
            ).click()
            expect(page.get_by_text(explanation, exact=True)).to_be_visible()
            appeal = db_sync(lambda: Appeal.objects.get())
            assert appeal.explanation == explanation
            assert (
                page.request.post(
                    live_server.url + path,
                    form=data | {"explanation": "Different retry text"},
                    max_redirects=0,
                ).status
                == 302
            )
            assert db_sync(lambda: Appeal.objects.get().explanation) == explanation
            page.reload()
            expect(page.get_by_text(explanation, exact=True)).to_be_visible()
            review_path = f"/{language}/moderation/appeals/{appeal.pk}/"
            assert db_sync(lambda: original.get(review_path).status_code) == 403
            assert page.request.get(live_server.url + review_path).status == 403
            review_context = authenticated_context(browser, independent, live_server.url)
            reviewed = review_context.new_page()
            assert reviewed.goto(live_server.url + review_path).status == 200
            for label in [
                ("Result" if language == "en" else "Resultado"),
                ("Reason" if language == "en" else "Motivo"),
            ]:
                expect(reviewed.get_by_label(re.compile("^" + label + ":?$"))).to_be_visible()
            expected = [
                ["", "Choose" if language == "en" else "Selecciona"],
                ["upheld", "Uphold decision" if language == "en" else "Mantener decisión"],
                ["reconsider", "Reopen review" if language == "en" else "Reabrir revisión"],
            ]
            assert (
                reviewed.locator("[name=result] option").evaluate_all(
                    "es=>es.map(e=>[e.value,e.textContent])"
                )
                == expected
            )
            reviewed.locator("form").evaluate("e=>e.noValidate=true")
            with reviewed.expect_response(
                lambda r: r.url == live_server.url + review_path and r.request.method == "POST"
            ) as posted:
                reviewed.get_by_role(
                    "button",
                    name="Resolve appeal" if language == "en" else "Resolver reclamación",
                    exact=True,
                ).click()
            assert posted.value.status == 400
            assert db_sync(lambda: Appeal.objects.get().status) == "open"
            reviewed.locator("[name=result]").select_option("reconsider")
            reviewed.locator("[name=reason]").fill(reason)
            data = reviewed.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            reviewed.get_by_role(
                "button",
                name="Resolve appeal" if language == "en" else "Resolver reclamación",
                exact=True,
            ).click()
            expect(reviewed.get_by_text(reason, exact=False)).to_be_visible()
            reviewed.reload()
            expect(reviewed.get_by_text(reason, exact=False)).to_be_visible()
            assert reviewed.request.post(live_server.url + review_path, form=data).status == 409
            assert (
                browser.new_page()
                .request.get(live_server.url + f"/{language}/listing/{revision.listing_id}/")
                .status
                == 404
            )
            assert reviewed.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    appeal.refresh_from_db()
    revision.refresh_from_db()
    assert (
        appeal.status == "resolved"
        and appeal.reviewer_id == reviewer.pk
        and appeal.result == "reconsider"
    )
    assert revision.status == "pending" and revision.edit_version == version + 1
    assert not revision.listing.approved_revision_id and Appeal.objects.count() == 1


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("family", ["agency", "photo"])
def test_shared_appeal_consumers_receive_request_language(request, language, family):
    assert connection.vendor == "postgresql"
    if family == "agency":
        _, owner, _, independent, decision = request.getfixturevalue("rejected_agency")
        submit = f"/{language}/agency/decisions/{decision.pk}/appeal/"
        response = owner.get(submit)
        assert response.status_code == 200
        assert (
            owner.post(submit, {"explanation": "Synthetic organization appeal"}).status_code == 302
        )
        from apps.core.models import AgencyAppeal

        case = AgencyAppeal.objects.get()
        review = f"/{language}/moderation/agency-appeals/{case.pk}/"
    else:
        values, notices, case, _, independent = request.getfixturevalue("photo_case")
        owner = values[5]
        submit = f"/{language}/person/photo-restrictions/{notices[0].pk}/"
        response = owner.get(submit)
        assert response.status_code == 200
        review = f"/{language}/moderation/photo-appeals/{case.pk}/"
    assert response.context["form"].fields["explanation"].label == (
        "Explanation" if language == "en" else "Explicación"
    )
    response = independent.get(review)
    assert response.status_code == 200
    form = response.context["form"]
    assert form.fields["result"].label == ("Result" if language == "en" else "Resultado")
    assert form.fields["reason"].label == (
        (
            "Reason for the person; no third-party data"
            if language == "en"
            else "Motivo para la persona; sin datos ajenos"
        )
        if family == "photo"
        else ("Reason" if language == "en" else "Motivo")
    )
    assert list(form.fields["result"].choices) == [
        ("", "Choose" if language == "en" else "Selecciona"),
        ("upheld", "Uphold decision" if language == "en" else "Mantener decisión"),
        ("reconsider", "Reopen review" if language == "en" else "Reabrir revisión"),
    ]
