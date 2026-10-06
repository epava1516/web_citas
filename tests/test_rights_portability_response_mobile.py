"""Real Chromium mobile preparation/review with synthetic identity evidence."""

import shutil
from uuid import uuid4

import pytest
from django.conf import settings as django_settings
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_portability_covered_export_races import approved_coverage
from test_rights_portability_response_draft import REASON, TEXT, operator
from test_rights_verification import read

from apps.core.models import User
from apps.safety.models import RightsPortabilityResponseDraft, RightsPortabilityResponseReview
from apps.safety.rights_portability_export import generate
from apps.safety.rights_verification import receive_event, simulate_event, start

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("account_only", [False, True])
def test_mobile_final_response_preparation_and_independent_decision(
    live_server, request, settings, monkeypatch, language, account_only
):
    settings.DEBUG = True
    case, author, selection, selected, _, decision, reviewer, _, _, receipt = approved_coverage(
        request, settings, monkeypatch, account_only
    )
    respond = Permission.objects.get(codename="respond_rights_request")
    author.user_permissions.add(respond)
    reviewer.user_permissions.add(respond, Permission.objects.get(codename="verify_rights_scope"))
    author, reviewer = User.objects.get(pk=author.pk), User.objects.get(pk=reviewer.pk)
    export = generate(
        author,
        case.pk,
        case.version,
        selection.pk,
        selected.pk,
        uuid4(),
        REASON,
        coverage_review_id=decision.pk,
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
            page.goto(base + "portability/response/")
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
                "link", name="Review final response" if english else "Revisar respuesta final"
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
            page = contexts[0].new_page()
            page.goto(base + "portability/response/")
            page.get_by_role(
                "link",
                name="Issue approved response and close"
                if english
                else "Emitir respuesta aprobada y cerrar",
            ).click()
            page.locator("#id_reason").fill(REASON)
            page.get_by_role(
                "button",
                name="Issue response and close" if english else "Emitir respuesta y cerrar",
                exact=True,
            ).click()
            expect(page.get_by_role("status")).to_contain_text(
                "Final response issued; request closed"
                if english
                else "Respuesta final emitida; solicitud cerrada"
            )
            assert TEXT not in page.locator("body").inner_text()
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
            recipient = browser.new_context(viewport={"width": 390, "height": 844})
            page = recipient.new_page()
            receipt_path = receipt.replace("/en/", f"/{language}/", 1)
            page.goto(live_server.url + receipt_path)
            expect(page.locator("body")).to_contain_text(TEXT)
            with page.expect_download() as downloaded:
                page.get_by_role(
                    "button",
                    name="Download private copy" if english else "Descargar copia privada",
                    exact=True,
                ).click()
            import json
            from pathlib import Path

            content = json.loads(Path(downloaded.value.path()).read_text())
            assert (
                content["export_schema"] == "covered-portability-v1"
                and content["simulation"] is True
            )
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        finally:
            browser.close()
    draft = RightsPortabilityResponseDraft.objects.get(request=case)
    review = RightsPortabilityResponseReview.objects.get(draft=draft)
    assert review.outcome == "approved" and review.action.actor_id == reviewer.pk
    assert draft.actor_id == author.pk and draft.proof_id == proof.pk
    case.refresh_from_db()
    assert (case.version, case.response_version, case.status, case.initial_due_at) == (
        original[0] + 1,
        original[1] + 1,
        "resolved",
        original[3],
    )

    from apps.safety.models import (
        RightsExportDownload,
        RightsPortabilityClosure,
        RightsResponseAcknowledgement,
    )

    assert RightsPortabilityClosure.objects.filter(review=review).count() == 1
    assert RightsExportDownload.objects.filter(export=export).count() == 1
    assert RightsResponseAcknowledgement.objects.count() == 0
