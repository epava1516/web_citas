import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.listings.models import LifecycleAction, Listing
from apps.listings.tasks import expire_one

pytestmark = pytest.mark.django_db(transaction=True)


def own():
    person = Person.objects.get(individual__username="fixture-v1-individual")
    client = Client()
    client.force_login(person.individual)
    return person, person.listing, client


def payload(listing, operation, **extra):
    listing.refresh_from_db()
    return {
        "key": str(uuid.uuid4()),
        "version": listing.lifecycle_version,
        "operation": operation,
        **extra,
    }


def test_availability_pause_resume_withdraw_and_old_retry(request):
    request.getfixturevalue("directory")
    person, listing, client = own()
    path = f"/en/listing/{listing.pk}/manage/"
    assert client.get(path).status_code == 200
    assert Client().get(path).status_code == 302
    outsider = Client()
    outsider.force_login(User.objects.get(username="fixture-v1-visitor"))
    assert outsider.get(path).status_code == 404
    data = payload(listing, "available")
    assert client.post(path, data).status_code == 302
    listing.refresh_from_db()
    available_until = listing.available_until
    assert (
        timezone.now() + timedelta(hours=3, minutes=59)
        < available_until
        < timezone.now() + timedelta(hours=4, seconds=1)
    )
    assert client.post(path, data).status_code == 302
    listing.refresh_from_db()
    assert listing.available_until == available_until
    pause = payload(listing, "pause")
    assert client.post(path, pause).status_code == 302
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 404
    listing.refresh_from_db()
    assert listing.available_until is None
    assert client.post(path, payload(listing, "resume")).status_code == 302
    assert Client().get(f"/en/listing/{listing.pk}/").status_code == 200
    assert client.post(path, payload(listing, "withdraw")).status_code == 302
    assert client.post(path, data).status_code == 302  # Exact old retry never republishes.
    listing.refresh_from_db()
    assert listing.status == "withdrawn"
    assert client.post(path, payload(listing, "resume")).status_code == 409
    assert not expire_one(listing.pk)
    assert LifecycleAction.objects.filter(listing=listing).count() == 4


def test_renewal_same_id_confirmation_expiry_and_delayed_task(request):
    request.getfixturevalue("directory")
    _, listing, client = own()
    path = f"/es/listing/{listing.pk}/manage/"
    approved = listing.approved_revision_id
    assert client.post(path, payload(listing, "renew", confirm="on")).status_code == 409
    Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert Client().get(f"/es/listing/{listing.pk}/").status_code == 404
    assert expire_one(listing.pk)
    assert not expire_one(listing.pk)
    assert client.post(path, payload(listing, "renew")).status_code == 409
    data = payload(listing, "renew", confirm="on")
    assert client.post(path, data).status_code == 302
    listing.refresh_from_db()
    expires = listing.expires_at
    assert listing.status == "published" and listing.approved_revision_id == approved
    assert expires > timezone.now() + timedelta(days=29)
    assert not expire_one(listing.pk)
    assert client.post(path, data).status_code == 302
    listing.refresh_from_db()
    assert listing.expires_at == expires and Listing.objects.filter(pk=listing.pk).count() == 1
    assert client.post(path, data | {"confirm": ""}).status_code == 409


def test_stale_form_revocation_and_key_payload_conflict(request):
    request.getfixturevalue("directory")
    person, listing, client = own()
    path = f"/es/listing/{listing.pk}/manage/"
    old = payload(listing, "available")
    assert client.post(path, payload(listing, "pause")).status_code == 302
    response = client.post(path, old)
    assert response.status_code == 409 and response["Cache-Control"] == "private, no-store"
    data = payload(listing, "resume")
    assert client.post(path, data).status_code == 302
    assert client.post(path, data | {"operation": "withdraw"}).status_code == 409
    stale = payload(listing, "available")
    assert client.post(f"/es/person/{person.pk}/revoke/").status_code == 302
    assert client.post(path, stale).status_code == 409
    assert client.post(path, payload(listing, "resume")).status_code == 409
    assert client.post(path, {"operation": "available"}).status_code == 400


def test_concurrent_actions_accept_only_one_version(request):
    request.getfixturevalue("directory")
    person, listing, _ = own()
    data = payload(listing, "pause")
    barrier = Barrier(2)

    def post():
        close_old_connections()
        try:
            client = Client()
            client.force_login(User.objects.get(pk=person.individual_id))
            barrier.wait(timeout=10)
            return client.post(
                f"/es/listing/{listing.pk}/manage/", data | {"key": str(uuid.uuid4())}
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(post) for _ in range(2)]
        assert sorted(future.result() for future in futures) == [302, 409]
    assert LifecycleAction.objects.filter(listing=listing).count() == 1


def test_withdraw_pending_revision_prevents_late_moderation(request):
    from apps.listings.models import Revision

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-b")
    client = Client()
    client.force_login(person.agency.owner)
    session = client.session
    session["mfa_version"] = person.agency.owner.mfa_version
    session.save()
    listing = person.listing
    revision = listing.revisions.get(status="pending")
    assert (
        client.post(f"/es/listing/{listing.pk}/manage/", payload(listing, "withdraw")).status_code
        == 302
    )
    assert Revision.objects.get(pk=revision.pk).status == "withdrawn"
    moderator = Client()
    moderator.force_login(User.objects.get(username="fixture-v1-moderator"))
    session = moderator.session
    session["mfa_version"] = User.objects.get(username="fixture-v1-moderator").mfa_version
    session.save()
    assert (
        moderator.post(
            f"/es/moderation/listings/{revision.pk}/",
            {
                "edit_version": revision.edit_version,
                "outcome": "approved",
                "reason": "Late old review",
            },
        ).status_code
        == 400
    )
    listing.refresh_from_db()
    assert listing.status == "withdrawn" and listing.approved_revision_id is None


def test_mobile_pause_resume_withdraw_persists(live_server, request, settings):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    request.getfixturevalue("directory")
    _, listing, _ = own()
    listing_id = listing.pk
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill("fixture-individual@example.invalid")
            page.locator("[name=password]").fill("Long-directory-fixture-password!873")
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/en/listing/{listing_id}/manage/")
            for operation, status in [
                ("available", "published"),
                ("pause", "paused"),
                ("resume", "published"),
                ("withdraw", "withdrawn"),
            ]:
                page.locator("[name=operation]").select_option(operation)
                page.get_by_role("button", name="Apply action", exact=True).click()
                expect(page.get_by_text(status, exact=True)).to_be_visible()
                page.reload()
                expect(page.get_by_text(status, exact=True)).to_be_visible()
            assert page.request.get(live_server.url + f"/en/listing/{listing_id}/").status == 404
        finally:
            browser.close()
