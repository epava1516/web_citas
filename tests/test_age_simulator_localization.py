"""ESEN simulator presentation; never proof of real identity or age verification."""

import re
import shutil

import pytest
from django.conf import settings
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_consent_transfer_localization import localized_account
from test_reset_localization import db_sync
from test_verification import ready_accounts  # noqa: F401

from apps.core.models import Person, VerificationCheck, VerificationEvent
from apps.core.verification_services import publication_ready

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_age_simulator_preserves_explicit_scope_and_current_events(
    request, live_server, language
):
    request.getfixturevalue("ready_accounts")
    assert connection.vendor == "postgresql"
    user, staff = localized_account("synthetic-age-subject")
    _, foreign = localized_account("synthetic-age-foreign")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic local subject")
    path = f"/{language}/person/{person.pk}/age/"
    assert foreign.get(path).status_code == 404
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
            expect(
                page.get_by_role(
                    "heading",
                    name="Age simulator" if language == "en" else "Simulador de edad",
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_text(
                    "Synthetic test only: no identity document, biometric data or actual age verification. Simulated results cannot authorize production."
                    if language == "en"
                    else "Prueba sintética: sin documentos de identidad, biometría ni verificación real de edad. Los resultados simulados no autorizan producción.",
                    exact=True,
                )
            ).to_be_visible()
            expect(
                page.get_by_label(
                    re.compile(
                        "^"
                        + ("Simulated result" if language == "en" else "Resultado simulado")
                        + ":?$"
                    )
                )
            ).to_be_visible()
            expected = [
                ["pending", "Pending" if language == "en" else "Pendiente"],
                ["failed", "Failed" if language == "en" else "Fallido"],
                ["passed", "Passed" if language == "en" else "Superado"],
            ]
            assert (
                page.locator("[name=outcome] option").evaluate_all(
                    "es=>es.map(e=>[e.value,e.textContent])"
                )
                == expected
            )
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            response = page.request.post(live_server.url + path, form=data | {"outcome": "unknown"})
            assert response.status == 200 and "errorlist" in response.text()
            assert db_sync(lambda: VerificationEvent.objects.count()) == 0
            for index, outcome in enumerate(["pending", "failed", "passed"], 1):
                assert page.goto(live_server.url + path).status == 200
                page.locator("[name=outcome]").select_option(outcome)
                page.get_by_role(
                    "button",
                    name="Simulate result" if language == "en" else "Simular resultado",
                    exact=True,
                ).click()
                page.wait_for_url(live_server.url + f"/{language}/person/{person.pk}/verification/")
                state = db_sync(lambda: Person.objects.get(pk=person.pk))
                assert state.age_status == outcome
                check = db_sync(lambda: VerificationCheck.objects.latest("created_at"))
                assert (
                    check.person_id == person.pk
                    and check.subject_id == user.pk
                    and check.manager_version == person.manager_version
                )
                assert check.provider == "simulator" and check.procedure == "simulator-v1"
                assert db_sync(lambda: VerificationEvent.objects.count()) == index
                assert (
                    db_sync(lambda: VerificationEvent.objects.get(verification=check).outcome)
                    == outcome
                )
                assert not db_sync(lambda: publication_ready(Person.objects.get(pk=person.pk)))
                page.reload()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert VerificationCheck.objects.count() == 3 and VerificationEvent.objects.count() == 3
