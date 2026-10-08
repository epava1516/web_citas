"""Independent plan inspection and decision through actual mobile sessions ES/EN."""

import json
import shutil
from uuid import uuid4

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.db import transaction
from playwright.sync_api import expect, sync_playwright
from test_copy_information_localization import review_captions
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_information import draft
from test_rights_exports import prepared

from apps.core.mfa import encrypt
from apps.core.models import LegalDocument, User
from apps.safety.models import RightsCopyInformationReview
from apps.safety.rights_copy_information import record as save
from apps.safety.rights_information_policy import published_policy

REASON = "PRIVATE_SYNTHETIC_REVIEW_INFORMATION"

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_mobile_independent_information_review(
    live_server, request, settings, monkeypatch, tmp_path, language
):
    settings.DEBUG = True
    case, author, _, _, _, _ = prepared(request, settings)
    document = LegalDocument.objects.get(slug="privacy", language=language, active=True)
    with transaction.atomic():
        _, digest = published_policy(document.pk, language)
    value = draft()
    for item in value["access"].values():
        item.update(status="reviewed", source="reviewer", text=REASON)
    plan = save(
        author,
        case.pk,
        case.version,
        uuid4(),
        0,
        document.version,
        "Save synthetic information before mobile independent review",
        value,
        policy_document_id=document.pk,
        expected_policy_digest=digest,
    )
    reviewer = User.objects.get(username="fixture-v1-visitor")
    reviewer.user_permissions.add(
        *Permission.objects.filter(
            codename__in=[
                "review_rights_request",
                "execute_rights_request",
                "review_copy_information",
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
                f'a[href="/{language}/moderation/rights/{case.pk}/information/{plan.pk}/review/"]'
            ).click()
            assert REASON not in page.content()
            review_captions(page, language)
            page.locator("[name=operation]").select_option("inspect")
            page.locator("[name=reason]").fill(
                "Audit current plan before independent operational review"
            )
            button = "Record review action" if english else "Registrar acción de revisión"
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(REASON, exact=True).first).to_be_visible()
            review_captions(page, language)
            assert page.locator("article").count() == 10
            for article in page.locator("article").all():
                expect(article.locator("p").first).to_have_text(
                    "Reviewed · Reviewer"
                    if english
                    else "Revisado · Revisor"
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
            page.reload()
            assert REASON not in page.content()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    result = RightsCopyInformationReview.objects.get(information=plan)
    assert result.action.actor_id == reviewer.pk and result.outcome == "approved"
    case.refresh_from_db()
    assert (case.version, case.status, case.initial_due_at) == original
