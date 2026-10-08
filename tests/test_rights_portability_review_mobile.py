"""Independent plan inspection and decision through actual mobile sessions ES/EN."""

import json
import shutil
from uuid import uuid4

import pyotp
import pytest
from django.contrib.auth.models import Permission
from playwright.sync_api import expect, sync_playwright
from test_account_copy_races import prepared_account
from test_copy_information_localization import review_captions
from test_reports import directory, photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_rights_portability import assessment

from apps.core.mfa import encrypt
from apps.core.models import User
from apps.safety.models import RightsPortabilityReview
from apps.safety.rights_portability import save_assessment

REASON = "PRIVATE_SYNTHETIC_REVIEW_INFORMATION"

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_independent_portability_review(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, author, _, _, _, _ = prepared_account(request, settings, monkeypatch, "portability")
    value = assessment()
    for item in value.values():
        item.update(
            status="eligible",
            basis="contract",
            origin="provided",
            automated=True,
            subject_related=True,
            third_party_reviewed=True,
            reason="Synthetic eligibility review before mobile approval",
            evidence=REASON,
        )
    plan = save_assessment(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        "Save synthetic assessment before mobile independent review",
        value,
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_portability",
            ]
        )
    )
    reviewer = User.objects.get(pk=reviewer.pk)
    original = (case.version, case.status, case.initial_due_at)
    secret = pyotp.random_base32()
    reviewer.mfa_secret_encrypted = encrypt(secret)
    reviewer.mfa_version += 1
    reviewer.save(update_fields=["mfa_secret_encrypted", "mfa_version"])
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    english = language == "en"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + f"/{language}/account/login/")
            page.locator("[name=email]").fill(reviewer.email)
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(secret).now())
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role(
                    "heading", name="Your account" if english else "Tu cuenta", exact=True
                )
            ).to_be_visible()
            page.goto(live_server.url + f"/{language}/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Inspect latest request before independent purpose review"
            )
            page.locator("button[type=submit]").first.click()
            page.locator(
                f'a[href="/{language}/moderation/rights/{case.pk}/portability/{plan.pk}/review/"]'
            ).click()
            assert REASON not in page.content()
            review_captions(page, language)
            button = "Record review action" if english else "Registrar acción de revisión"
            page.locator("[name=reason]").fill("short")
            page.locator("form").evaluate("form=>form.noValidate=true")
            with page.expect_response(lambda r: r.request.method == "POST") as invalid:
                page.get_by_role("button", name=button, exact=True).click()
            assert invalid.value.status == 400
            review_captions(page, language)
            assert REASON not in page.content()
            assert db_sync(lambda: RightsPortabilityReview.objects.count()) == 0
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(
                "Audit current plan before independent operational review"
            )
            button = "Record review action" if english else "Registrar acción de revisión"
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(REASON, exact=True).first).to_be_visible()
            review_captions(page, language)
            assert page.locator("article").count() == 9
            for article in page.locator("article").all():
                expect(article.locator("p").first).to_have_text(
                    "Eligible · Contract · Provided by the subject"
                    if english
                    else "Elegible · Contrato · Facilitados por el interesado"
                )
            page.locator("[name=operation]").select_option("review")
            page.locator("[name=outcome]").select_option("approved")
            page.locator("[name=reason]").fill(
                "Independent synthetic review confirms the selected decisions"
            )
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_role("status")).to_have_text(
                "Decision recorded: approved" if english else "Decisión registrada: approved"
            )
            page.goto(
                live_server.url
                + f"/{language}/moderation/rights/{case.pk}/portability/{plan.pk}/review/"
            )
            page.reload()
            assert REASON not in page.content()
            review_captions(page, language)
            csrf = page.locator("[name=csrfmiddlewaretoken]").input_value()
            db_sync(
                lambda: reviewer.user_permissions.remove(
                    Permission.objects.get(codename="review_portability")
                )
            )
            response = page.goto(
                live_server.url
                + f"/{language}/moderation/rights/{case.pk}/portability/{plan.pk}/review/"
            )
            assert response.status == 403 and page.locator("body").inner_text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert "no-store" in response.headers["cache-control"]
            response = page.request.post(
                live_server.url
                + f"/{language}/moderation/rights/{case.pk}/portability/{plan.pk}/review/",
                form={"csrfmiddlewaretoken": csrf},
            )
            assert response.status == 403 and response.text() == (
                "Forbidden" if english else "Acceso denegado"
            )
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    result = RightsPortabilityReview.objects.get(assessment=plan)
    assert result.action.actor_id == reviewer.pk and result.outcome == "approved"
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
