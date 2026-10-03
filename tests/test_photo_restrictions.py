import os
import shutil

import pytest
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_match_review import conflict, resolution  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_revised_listings import published  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.mediafiles.models import PhotoRestriction


@pytest.fixture
def restricted(request):
    values = request.getfixturevalue("conflict")
    original, revision, match, _, reviewer, _, _ = values
    assert (
        reviewer.post(
            f"/es/moderation/matches/{match.pk}/",
            resolution(
                match,
                outcome="conflict",
                reason="Referencia interna reservada: second-subject@example.invalid",
            ),
        ).status_code
        == 302
    )
    notices = [
        PhotoRestriction.objects.get(person_id=r.listing.person_id) for r in [original, revision]
    ]
    return values, notices


@pytest.mark.django_db(transaction=True)
def test_photo_restriction_notice_is_private_and_has_no_other_account_data(restricted):
    values, notices = restricted
    original, _, _, _, _, owner, second = values
    assert PhotoRestriction.objects.count() == 2
    for client, own, other in zip([owner, second], notices, reversed(notices), strict=True):
        response = client.get(f"/es/person/photo-restrictions/{own.pk}/")
        assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
        assert str(own.photo_id).encode() in response.content
        assert str(other.photo_id).encode() not in response.content
        assert b"second-subject@example.invalid" not in response.content
        assert b"synthetic-authorizations" not in response.content
        assert client.get(f"/es/person/photo-restrictions/{other.pk}/").status_code == 404
    assert Client().get(f"/es/person/photo-restrictions/{notices[0].pk}/").status_code == 302
    person = original.listing.person
    person.manager_version += 1
    person.save(update_fields=["manager_version"])
    assert owner.get(f"/es/person/photo-restrictions/{notices[0].pk}/").status_code == 404


@pytest.mark.django_db(transaction=True)
def test_browser_mobile_photo_restriction_notice(live_server, restricted, settings):
    settings.DEBUG = True
    values, notices = restricted
    original = values[0]
    subject_email = original.listing.person.subject.email
    person_id = original.listing.person_id
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.getenv("BROWSER_EXECUTABLE") or shutil.which("chromium-browser"),
            args=["--no-sandbox"],
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/es/account/login/")
            page.locator("[name=email]").fill(subject_email)
            page.locator("[name=password]").fill("Long-draft-password!847")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/es/person/{person_id}/verification/")
            page.get_by_role("link", name="Restricción de fotografía", exact=False).click()
            page.reload()
            expect(page.get_by_text("La restricción continúa activa.")).to_be_visible()
            assert "second-subject@example.invalid" not in page.content()
            assert (
                page.request.get(
                    live_server.url + f"/es/person/photo-restrictions/{notices[1].pk}/"
                ).status
                == 404
            )
        finally:
            browser.close()


@pytest.mark.django_db(transaction=True)
def test_cleared_photo_notice_remains_private_history_without_republishing(restricted):
    values, notices = restricted
    original, _, match, _, reviewer, owner, _ = values
    match.refresh_from_db()
    assert (
        reviewer.post(f"/es/moderation/matches/{match.pk}/", resolution(match)).status_code == 302
    )
    response = owner.get(f"/es/person/photo-restrictions/{notices[0].pk}/")
    assert response.status_code == 200
    assert "ya no está activo" in response.content.decode()
    assert Client().get(f"/es/listing/{original.listing_id}/").status_code == 404
    assert PhotoRestriction.objects.count() == 2
    match.refresh_from_db()
    assert (
        reviewer.post(
            f"/es/moderation/matches/{match.pk}/", resolution(match, outcome="conflict")
        ).status_code
        == 302
    )
    assert (
        "ya no está activo"
        in owner.get(f"/es/person/photo-restrictions/{notices[0].pk}/").content.decode()
    )
    assert PhotoRestriction.objects.count() == 4
