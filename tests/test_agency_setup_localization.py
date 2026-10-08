"""Localized private setup with real PG and Chromium; invitations locmem only."""

import re
import shutil
from urllib.parse import urlsplit

import pytest
from django.core import mail
from django.db import connection
from playwright.sync_api import expect, sync_playwright
from test_consent_transfer_localization import context_for, localized_account
from test_reset_localization import db_sync
from test_verification import ready_accounts  # noqa: F401

from apps.core.models import Agency, AgencyInvitation, AgencyMember, Person, User

pytestmark = pytest.mark.django_db(transaction=True)


def localized_field(page, label):
    field = page.get_by_label(re.compile("^" + re.escape(label) + ":?$"))
    expect(field).to_be_visible()
    return field


def submit(page, language):
    page.get_by_role(
        "button", name="Continue" if language == "en" else "Continuar", exact=True
    ).click()


@pytest.mark.parametrize("language", ["es", "en"])
def test_localized_agency_setup_preserves_private_membership(request, live_server, language):
    request.getfixturevalue("ready_accounts")
    assert connection.vendor == "postgresql"
    owner, staff = localized_account("synthetic-owner", True)
    editor, editor_staff = localized_account("synthetic-editor")
    editor.mfa_enabled = True
    editor.mfa_version = 1
    editor.save(update_fields=["mfa_enabled", "mfa_version"])
    session = editor_staff.session
    session["mfa_version"] = 1
    session.save()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = context_for(browser, staff, live_server.url)
            page = context.new_page()
            path = f"/{language}/agency/create/"
            assert page.goto(live_server.url + path).status == 200
            field = localized_field(
                page, "Agency name" if language == "en" else "Nombre de agencia"
            )
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert (
                page.request.post(live_server.url + path, form=data).status == 200
                and db_sync(lambda: Agency.objects.count()) == 0
            )
            field.fill("Synthetic organization")
            submit(page, language)
            page.wait_for_url(re.compile("/agency/[0-9a-f-]+/$"))
            agency = db_sync(lambda: Agency.objects.get())
            assert agency.owner_id == owner.pk and agency.verification_status == "pending"
            path = f"/{language}/agency/{agency.pk}/people/add/"
            assert page.goto(live_server.url + path).status == 200
            field = localized_field(page, "Public alias" if language == "en" else "Alias público")
            data = page.locator("form").evaluate("e=>Object.fromEntries(new FormData(e))")
            assert (
                page.request.post(live_server.url + path, form=data).status == 200
                and db_sync(lambda: Person.objects.count()) == 0
            )
            field.fill("Synthetic represented alias")
            submit(page, language)
            page.wait_for_url(live_server.url + f"/{language}/agency/{agency.pk}/")
            person = db_sync(lambda: Person.objects.get())
            assert person.agency_id == agency.pk and person.subject_id is None
            path = f"/{language}/agency/{agency.pk}/invite/"
            assert page.goto(live_server.url + path).status == 200
            field = localized_field(
                page, "Editor email" if language == "en" else "Email del editor"
            )
            field.fill("invalid")
            page.locator("form").evaluate("e=>e.noValidate=true")
            submit(page, language)
            expect(page.locator(".errorlist")).to_be_visible()
            assert db_sync(lambda: AgencyInvitation.objects.count()) == 0
            page.locator("[name=email]").fill(editor.email)
            submit(page, language)
            page.wait_for_url(live_server.url + f"/{language}/agency/{agency.pk}/")
            invitation = urlsplit(mail.outbox[-1].body).path
            candidate = context_for(browser, editor_staff, live_server.url).new_page()
            assert candidate.goto(live_server.url + invitation).status == 200
            assert db_sync(lambda: AgencyMember.objects.count()) == 0
            candidate.get_by_role(
                "button",
                name="Accept invitation" if language == "en" else "Aceptar invitación",
                exact=True,
            ).click()
            candidate.wait_for_url(live_server.url + f"/{language}/agency/{agency.pk}/")
            assert candidate.request.get(live_server.url + invitation).status == 403
            member = db_sync(lambda: AgencyMember.objects.get())
            assert member.user_id == editor.pk and member.active
            csrf = context.cookies()[
                next(i for i, c in enumerate(context.cookies()) if c["name"] == "csrftoken")
            ]["value"]
            assert (
                page.request.post(
                    live_server.url + f"/{language}/agency/{agency.pk}/members/{member.pk}/revoke/",
                    form={"csrfmiddlewaretoken": csrf},
                    max_redirects=0,
                ).status
                == 302
            )
            assert not db_sync(lambda: AgencyMember.objects.get().active)
            assert (
                candidate.request.get(live_server.url + f"/{language}/agency/{agency.pk}/").status
                == 403
            )
            page.reload()
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        finally:
            browser.close()
    assert User.objects.get(pk=owner.pk).role == "agency"


@pytest.mark.parametrize("language", ["es", "en"])
def test_shared_individual_alias_is_localized_and_private(request, live_server, language):
    request.getfixturevalue("ready_accounts")
    user, staff = localized_account("synthetic-individual")
    assert connection.vendor == "postgresql"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = context_for(browser, staff, live_server.url).new_page()
            path = f"/{language}/person/create/"
            assert page.goto(live_server.url + path).status == 200
            field = localized_field(page, "Public alias" if language == "en" else "Alias público")
            field.fill("Synthetic own alias")
            submit(page, language)
            page.wait_for_url(re.compile("/person/[0-9a-f-]+/verification/$"))
            page.reload()
        finally:
            browser.close()
    person = Person.objects.get()
    assert (
        person.alias == "Synthetic own alias"
        and person.individual_id == person.subject_id == user.pk
    )
