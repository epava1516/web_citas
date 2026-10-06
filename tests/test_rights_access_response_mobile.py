"""Real Chromium mobile preparation/review with synthetic identity evidence."""

import shutil
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_access_response_draft import REASON, TEXT
from test_rights_information_export import approved_information
from test_rights_portability_response_draft import operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import RightsAccessResponseDraft, RightsAccessResponseReview
from apps.safety.rights_exports import generate, preview
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_mobile_final_response_preparation_and_independent_decision(
    live_server, request, settings, monkeypatch, language, account_only
):
    settings.DEBUG = True
    case, author, _, _, _, _, _, _, decision, _, _ = approved_information(
        request, settings, monkeypatch, account_only
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    respond = Permission.objects.get(codename="respond_rights_request")
    author.user_permissions.add(respond)
    reviewer.user_permissions.add(respond, Permission.objects.get(codename="verify_rights_scope"))
    author, reviewer = User.objects.get(pk=author.pk), User.objects.get(pk=reviewer.pk)
    export = generate(
        author,
        case.pk,
        uuid4(),
        case.version,
        REASON,
        preview(author, case.pk, case.version, REASON),
        information_review_id=decision.pk,
    )
    case.refresh_from_db()
    staff, other = operator(author), operator(reviewer)
    read(staff, case)
    proof = start(author, case.pk, uuid4(), case.version, REASON)
    case.refresh_from_db()
    read(other, case)
    receive_event(reviewer, simulate_event(proof.pk, uuid4(), case.version, "passed", REASON))
    case.refresh_from_db()
    read(staff, case)
    read(other, case)
    original = case.version, case.response_version, case.status, case.initial_due_at
    cookies = [
        client.cookies[django_settings.SESSION_COOKIE_NAME].value for client in (staff, other)
    ]
    base = live_server.url + f"/{language}/moderation/rights/{case.pk}/"
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            contexts = [
                browser.new_context(viewport={"width": 390, "height": 844}) for _ in cookies
            ]
            for context, cookie in zip(contexts, cookies, strict=True):
                context.add_cookies(
                    [
                        {
                            "name": django_settings.SESSION_COOKIE_NAME,
                            "value": cookie,
                            "url": live_server.url,
                        }
                    ]
                )
            page = contexts[0].new_page()
            page.goto(base + "access/response/")
            page.locator("#id_export").select_option(str(export.pk))
            page.locator("#id_reason").fill(REASON)
            page.locator("#id_response").fill(TEXT)
            page.locator("#id_redaction_confirmed").check()
            page.get_by_role(
                "button",
                name="Save response draft" if english else "Guardar borrador de respuesta",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Final response draft prepared"
                if english
                else "Borrador de respuesta final preparado"
            )
            assert TEXT not in page.locator("body").inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page = contexts[1].new_page()
            page.goto(base)
            page.get_by_role(
                "link", name="Review response" if english else "Revisar respuesta"
            ).click()
            assert TEXT not in page.locator("body").inner_text()
            page.locator("#id_reason").fill(REASON)
            page.get_by_role(
                "button",
                name="Inspect response draft" if english else "Consultar borrador de respuesta",
                exact=True,
            ).click()
            expect(page.locator("body")).to_contain_text(TEXT)
            page.locator("#decision_reason").fill(REASON)
            page.locator("#decision_outcome").select_option("approved")
            page.get_by_role(
                "button",
                name="Record independent decision"
                if english
                else "Registrar decisión independiente",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text("approved")
            assert TEXT not in page.locator("body").inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            page.goto(page.url)
            assert TEXT not in page.locator("body").inner_text()
        finally:
            browser.close()
    draft = RightsAccessResponseDraft.objects.get(request=case)
    review = RightsAccessResponseReview.objects.get(draft=draft)
    assert review.outcome == "approved" and review.action.actor_id == reviewer.pk
    assert draft.actor_id == author.pk and draft.proof_id == proof.pk
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == original
