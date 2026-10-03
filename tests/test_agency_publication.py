import os
import shutil

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.management import call_command
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_browser_revised_listings import moderator_login
from test_drafts import contacts, details
from test_listing_moderation import decision
from test_photos import photo_environment, raw_image, upload  # noqa: F401
from test_verification import account, phone, ready_accounts  # noqa: F401

from apps.core.mfa import encrypt
from apps.core.models import Agency, AgencyMember, Person
from apps.listings.models import Revision


@pytest.fixture
def agency_publication(request):
    request.getfixturevalue("ready_accounts")
    request.getfixturevalue("photo_environment")
    call_command("seed_catalog")
    owner, owner_client = account("publication-agency", agency=True)
    moderator, reviewer = account("publication-reviewer", agency=True)
    moderator.set_password("Long-moderator-password!847")
    moderator.save(update_fields=["password"])
    reviewer.force_login(moderator)
    session = reviewer.session
    session["mfa_version"] = moderator.mfa_version
    session.save()
    moderator.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_agency", "review_listing"])
    )
    assert (
        owner_client.post("/es/agency/create/", {"name": "Agencia de pruebas"}).status_code == 302
    )
    agency = Agency.objects.get(owner=owner)
    assert (
        reviewer.post(
            f"/es/moderation/organizations/{agency.pk}/",
            {
                "review_version": 1,
                "outcome": "passed",
                "reason": "Organización sintética revisada",
                "evidence_reference": "synthetic-agency-2",
            },
        ).status_code
        == 302
    )
    agency.refresh_from_db()
    assert agency.verification_status == "passed"
    editor, editor_client = account("publication-editor", agency=True)
    AgencyMember.objects.create(agency=agency, user=editor)
    revisions = []
    subject_clients = []
    for index in range(2):
        subject, subject_client = account(f"publication-subject-{index}")
        assert (
            owner_client.post(
                f"/es/agency/{agency.pk}/people/add/", {"alias": f"Modelo sintético {index}"}
            ).status_code
            == 302
        )
        person = Person.objects.get(agency=agency, alias=f"Modelo sintético {index}")
        assert (
            owner_client.post(
                f"/es/person/{person.pk}/consent/invite/", {"email": subject.email}
            ).status_code
            == 302
        )
        invitation_path = mail.outbox[-1].body.removeprefix("http://localhost:8000")
        assert (
            subject_client.post(
                invitation_path, {"authorize": "on", "version": "dev-1"}
            ).status_code
            == 302
        )
        assert (
            subject_client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code
            == 302
        )
        assert phone(owner_client, person, "600777333").status_code == 302
        if index == 0:
            assert (
                owner_client.post(
                    f"/es/agency/{agency.pk}/people/{person.pk}/assign/", {"editor": editor.pk}
                ).status_code
                == 302
            )
            manager = editor_client
        else:
            manager = owner_client
            assert editor_client.post(f"/es/person/{person.pk}/listing/start/").status_code == 404
        assert manager.post(f"/es/person/{person.pk}/listing/start/").status_code == 302
        revision = Revision.objects.get(listing__person=person)
        assert (
            manager.post(
                f"/es/draft/{revision.pk}/1/",
                details(revision, title=f"Modelo para fotografía {index}"),
            ).status_code
            == 302
        )
        revision.refresh_from_db()
        assert manager.post(f"/es/draft/{revision.pk}/2/", contacts(revision)).status_code == 302
        assert upload(manager, revision, raw_image(seed=100 + index)).status_code == 302
        revision.refresh_from_db()
        response = manager.post(
            f"/es/draft/{revision.pk}/submit/",
            {"edit_version": revision.edit_version, "declaration": "on"},
        )
        assert response.status_code == 302, response.content.decode()
        revision.refresh_from_db()
        revisions.append(revision)
        subject_clients.append(subject_client)
    return agency, owner_client, editor_client, moderator, reviewer, revisions, subject_clients


@pytest.mark.django_db(transaction=True)
def test_agency_two_people_shared_phone_editor_publication_and_revoke(agency_publication):
    agency, owner, editor, _, reviewer, revisions, subjects = agency_publication
    public = Client()
    assert agency.people.count() == 2
    assert len(set(agency.people.values_list("phone_claim_id", flat=True))) == 1
    for revision in revisions:
        path = f"/es/moderation/listings/{revision.pk}/"
        assert owner.get(path).status_code == editor.get(path).status_code == 403
        assert reviewer.post(path, decision(revision)).status_code == 302
        assert public.get(f"/es/listing/{revision.listing_id}/").status_code == 200
    first = revisions[0]
    assert subjects[0].post(f"/es/person/{first.listing.person_id}/revoke/").status_code == 302
    assert public.get(f"/es/listing/{first.listing_id}/").status_code == 404
    assert public.get(f"/es/listing/{revisions[1].listing_id}/").status_code == 200


@pytest.mark.django_db(transaction=True)
def test_browser_agency_independent_review_of_two_publications(
    live_server, agency_publication, settings
):
    settings.DEBUG = True
    _, _, _, moderator, _, revisions, _ = agency_publication
    secret = pyotp.random_base32()
    moderator.mfa_secret_encrypted = encrypt(secret)
    moderator.save(update_fields=["mfa_secret_encrypted"])
    snapshots = [(revision.pk, revision.listing_id, revision.title) for revision in revisions]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            staff = browser.new_page()
            moderator_login(staff, live_server.url, moderator, secret)
            guest = browser.new_page(viewport={"width": 390, "height": 844})
            for revision_id, listing_id, title in snapshots:
                staff.goto(live_server.url + f"/es/moderation/listings/{revision_id}/")
                expect(staff.get_by_role("img", name="Foto privada para revisión")).to_be_visible()
                staff.locator("[name=outcome]").select_option("approved")
                staff.locator("[name=reason]").fill("Modelo de agencia y autorización revisados")
                staff.get_by_role("button", name="Registrar decisión").click()
                guest.goto(live_server.url + f"/es/listing/{listing_id}/")
                expect(guest.get_by_role("heading", name=title)).to_be_visible()
                image = guest.get_by_role("img", name=title)
                expect(image).to_be_visible()
                assert image.evaluate("img => img.complete && img.naturalWidth > 0")
        finally:
            browser.close()
