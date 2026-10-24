"""ESEN local verification presentation, preserving explicit simulator limitations."""

import re
import shutil

import pytest
from django.conf import settings
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_organization_review import organization  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_submissions import prepared  # noqa: F401

from apps.core.models import AgencyReview, LegalDocument, ManagerReview

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("family", ["organization", "manager"])
def test_localized_current_review_preserves_authority_and_simulation(
    request, live_server, language, family
):
    assert connection.vendor == "postgresql"
    if family == "organization":
        subject, _, staff = request.getfixturevalue("organization")
        path = f"/{language}/moderation/organizations/{subject.pk}/"
        model = AgencyReview
        outcome = "passed"
        version = subject.review_version
    else:
        subject, owner, _, _, staff = request.getfixturevalue("pending")
        phone = subject.phone_claim
        assert (
            owner.post(
                f"/es/person/{subject.pk}/transfer/",
                {"confirm": "on", "manager_version": subject.manager_version},
            ).status_code
            == 302
        )
        assert (
            owner.post(
                f"/es/person/{subject.pk}/consent/",
                {
                    "authorize": "on",
                    "version": LegalDocument.objects.get(
                        slug="publishing", language="es", active=True
                    ).version,
                },
            ).status_code
            == 302
        )
        assert owner.post(f"/es/person/{subject.pk}/age/", {"outcome": "passed"}).status_code == 302
        subject.refresh_from_db()
        subject.phone_claim = phone
        subject.save(update_fields=["phone_claim"])
        path = f"/{language}/moderation/managers/{subject.pk}/"
        model = ManagerReview
        outcome = "approved"
        version = subject.manager_version
    reason = "Synthetic independent local review; no real organization or identity verification"
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
            ]:
                expect(page.get_by_label(re.compile("^" + label + ":?$"))).to_be_visible()
            expected = [
                ["", "Choose" if language == "en" else "Selecciona"],
                [outcome, "Approve" if language == "en" else "Aprobar"],
                ["failed", "Reject" if language == "en" else "Rechazar"],
            ]
            assert (
                page.locator("[name=outcome] option").evaluate_all(
                    "es=>es.map(e=>[e.value,e.textContent])"
                )
                == expected
            )
            if family == "organization":
                expect(
                    page.get_by_label(
                        re.compile(
                            "^"
                            + (
                                "Synthetic verification reference"
                                if language == "en"
                                else "Referencia sintética de comprobación"
                            )
                            + ":?$"
                        )
                    )
                ).to_be_visible()
                expect(
                    page.get_by_text(
                        "Development simulation. No real organization has been verified through this workflow."
                        if language == "en"
                        else "Simulación de desarrollo. Este recorrido no acredita la comprobación de una organización real.",
                        exact=True,
                    )
                ).to_be_visible()
            button = (
                ("Record decision" if language == "en" else "Registrar decisión")
                if family == "organization"
                else (
                    "Record manager review" if language == "en" else "Registrar revisión del gestor"
                )
            )
            page.locator("form").evaluate("e=>e.noValidate=true")
            with page.expect_response(
                lambda r: r.url == live_server.url + path and r.request.method == "POST"
            ) as posted:
                page.get_by_role("button", name=button, exact=True).click()
            assert posted.value.status == 400 and db_sync(lambda: model.objects.count()) == 0
            page.locator("[name=outcome]").select_option(outcome)
            page.locator("[name=reason]").fill(reason)
            if family == "organization":
                page.locator("[name=evidence_reference]").fill("synthetic-localization-reference")
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            page.get_by_role("button", name=button, exact=True).click()
            expect(page.get_by_text(reason, exact=False)).to_be_visible()
            page.reload()
            expect(page.get_by_text(reason, exact=False)).to_be_visible()
            assert page.request.post(live_server.url + path, form=data).status == 409
            assert db_sync(lambda: model.objects.count()) == 1
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    subject.refresh_from_db()
    record = model.objects.get()
    assert record.outcome == outcome and record.reason == reason
    if family == "organization":
        assert (
            record.procedure == "simulator-v1" and subject.verification_procedure == "simulator-v1"
        )
        assert (
            record.evidence_reference == "synthetic-localization-reference"
            and subject.review_version == version + 1
        )
    else:
        assert (
            record.manager_version == version
            and subject.manager_version == version
            and subject.manager_review_status == "approved"
        )
