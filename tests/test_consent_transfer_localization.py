"""Real PG/Chromium direct and invited consent and transfer; mail only locmem."""

import re
import shutil
from urllib.parse import urlsplit

import pytest
from django.conf import settings
from django.core import mail
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_reset_localization import db_sync
from test_submissions import prepared  # noqa: F401
from test_verification import account, ready_accounts  # noqa: F401

from apps.core.models import (
    Agency,
    LegalAcceptance,
    LegalDocument,
    Person,
    RepresentationAction,
    RepresentationInvitation,
)

pytestmark = pytest.mark.django_db(transaction=True)


def localized_account(name, agency=False):
    user, staff = account(name, agency)
    for d in LegalDocument.objects.filter(
        active=True, language="en", slug__in=["terms", "privacy"]
    ):
        LegalAcceptance.objects.get_or_create(
            user=user, document=d, action="account_terms" if d.slug == "terms" else "privacy_notice"
        )
    return user, staff


def context_for(browser, staff, url):
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
@pytest.mark.parametrize("mode", ["direct", "invited"])
def test_localized_grant_and_transfer_preserve_current_authority(
    request, live_server, language, mode
):
    request.getfixturevalue("ready_accounts")
    assert connection.vendor == "postgresql"
    user, staff = localized_account("synthetic-subject")
    if mode == "direct":
        person = Person.objects.create(
            individual=user, subject=user, alias="Synthetic direct profile"
        )
    else:
        owner, owner_staff = localized_account("synthetic-owner", True)
        agency = Agency.objects.create(owner=owner, name="Synthetic organization")
        person = Person.objects.create(agency=agency, alias="Synthetic represented profile")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = context_for(browser, staff, live_server.url)
            page = context.new_page()
            if mode == "invited":
                manager = context_for(browser, owner_staff, live_server.url).new_page()
                invite = f"/{language}/person/{person.pk}/consent/invite/"
                assert manager.goto(live_server.url + invite).status == 200
                expect(
                    manager.get_by_label(
                        re.compile(
                            "^"
                            + re.escape(
                                "Person's private email"
                                if language == "en"
                                else "Correo privado de la persona"
                            )
                            + ":?$"
                        )
                    )
                ).to_be_visible()
                manager.locator("[name=email]").fill("invalid")
                manager.locator("form").evaluate("e=>e.noValidate=true")
                manager.get_by_role(
                    "button", name="Continue" if language == "en" else "Continuar", exact=True
                ).click()
                assert db_sync(lambda: RepresentationInvitation.objects.count()) == 0
                manager.locator("[name=email]").fill(user.email)
                manager.get_by_role(
                    "button", name="Continue" if language == "en" else "Continuar", exact=True
                ).click()
                manager.wait_for_url(
                    live_server.url + f"/{language}/person/{person.pk}/verification/"
                )
                path = urlsplit(mail.outbox[-1].body).path
            else:
                path = f"/{language}/person/{person.pk}/consent/"
            assert page.goto(live_server.url + path).status == 200
            label = (
                "I authorize this manager for this profile"
                if language == "en"
                else "Autorizo a este gestor para este perfil"
            )
            expect(page.get_by_label(re.compile("^" + re.escape(label) + ":?$"))).to_be_visible()
            assert db_sync(lambda: RepresentationAction.objects.count()) == 0
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert (
                page.request.post(
                    live_server.url + path, form=data | {"authorize": "on", "version": "obsolete"}
                ).status
                == 200
            )
            assert db_sync(lambda: RepresentationAction.objects.count()) == 0
            assert page.request.post(live_server.url + path, form=data).status == 200
            assert db_sync(lambda: RepresentationAction.objects.count()) == 0
            page.locator("[name=authorize]").check()
            page.get_by_role(
                "button", name="Authorize" if language == "en" else "Autorizar", exact=True
            ).click()
            page.wait_for_url(live_server.url + f"/{language}/person/{person.pk}/verification/")
            state = db_sync(lambda: Person.objects.get(pk=person.pk))
            assert (
                state.subject_id == user.pk
                and state.consent_version == state.manager_version
                and state.consent_revoked_at is None
            )
            assert db_sync(lambda: RepresentationAction.objects.filter(action="grant").count()) == 1
            if mode == "invited":
                assert (
                    page.request.post(
                        live_server.url + path, form=data | {"authorize": "on"}
                    ).status
                    == 403
                )
            transfer = f"/{language}/person/{person.pk}/transfer/"
            assert page.goto(live_server.url + transfer).status == 200
            for label in [
                (
                    "New agency ID; empty for self-management"
                    if language == "en"
                    else "ID de nueva agencia; vacío para gestionar personalmente"
                ),
                (
                    "I confirm the change and new authorization"
                    if language == "en"
                    else "Confirmo el cambio y una nueva autorización"
                ),
            ]:
                expect(
                    page.get_by_label(re.compile("^" + re.escape(label) + ":?$"))
                ).to_be_visible()
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert (
                page.request.post(
                    live_server.url + transfer,
                    form=data | {"target_agency": "invalid", "confirm": "on"},
                ).status
                == 400
            )
            assert page.request.post(live_server.url + transfer, form=data).status == 400
            assert (
                db_sync(lambda: RepresentationAction.objects.filter(action="transfer").count()) == 0
            )
            page.locator("[name=confirm]").check()
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            page.get_by_role(
                "button", name="Continue" if language == "en" else "Continuar", exact=True
            ).click()
            page.wait_for_url(live_server.url + f"/{language}/person/{person.pk}/verification/")
            assert (
                page.request.post(live_server.url + transfer, form=data, max_redirects=0).status
                == 302
            )
            page.reload()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    person.refresh_from_db()
    assert (
        person.individual_id == user.pk
        and person.agency_id is None
        and person.manager_version == state.manager_version + 1
    )
    assert (
        person.consent_version == 0
        and person.consent_revoked_at
        and person.age_status == "pending"
        and person.phone_claim_id is None
    )
    assert RepresentationAction.objects.filter(action="transfer").count() == 1
