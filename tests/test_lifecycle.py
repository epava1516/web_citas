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
    expiry = LifecycleAction.objects.get(listing=listing, operation="expire")
    assert expiry.actor_id is None and expiry.approved_revision_id == approved
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
    renewal = LifecycleAction.objects.get(listing=listing, operation="renew")
    assert renewal.approved_revision_id == approved and renewal.confirmed
    assert LifecycleAction.objects.filter(listing=listing, operation="expire").count() == 1
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
                expect(
                    page.get_by_role("heading", name="Recent actions", exact=True)
                ).to_be_visible()
            assert page.request.get(live_server.url + f"/en/listing/{listing_id}/").status == 404
        finally:
            browser.close()


def test_expiry_concurrent_tasks_record_one_system_event(request):
    request.getfixturevalue("directory")
    _, listing, client = own()
    Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    barrier = Barrier(2)

    def expire():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return expire_one(listing.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = [executor.submit(expire) for _ in range(2)]
        assert sum(future.result() for future in results) == 1
    assert (
        LifecycleAction.objects.filter(
            listing=listing, operation="expire", actor__isnull=True
        ).count()
        == 1
    )
    page = client.get(f"/en/listing/{listing.pk}/manage/")
    assert b"System" in page.content and b"Recent actions" in page.content
    assert len(page.context["events"]) == 1


def test_action_history_does_not_expose_previous_manager_events(request):
    request.getfixturevalue("directory")
    _, listing, client = own()
    assert (
        client.post(f"/es/listing/{listing.pk}/manage/", payload(listing, "pause")).status_code
        == 302
    )
    event = LifecycleAction.objects.get(listing=listing)
    event.manager_version = 999
    event.save(update_fields=["manager_version"])
    page = client.get(f"/es/listing/{listing.pk}/manage/")
    assert len(page.context["events"]) == 0
    assert b"Sin acciones para el gestor actual" in page.content


def test_agency_editor_assignment_mfa_and_revocation(request):
    from apps.core.models import AgencyMember

    request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    other = Person.objects.get(subject__username="fixture-v1-model-b")
    editor = User.objects.get(username="fixture-v1-editor")
    client = Client()
    client.force_login(editor)
    path = f"/en/listing/{person.listing.pk}/manage/"
    assert client.get(path).status_code == 302  # MFA required before private operations.
    session = client.session
    session["mfa_version"] = editor.mfa_version
    session.save()
    assert client.get(path).status_code == 200
    assert client.get(f"/en/listing/{other.listing.pk}/manage/").status_code == 404
    listing = person.listing
    assert client.post(path, payload(listing, "pause")).status_code == 302
    AgencyMember.objects.filter(user=editor, agency=person.agency).update(active=False)
    listing.refresh_from_db()
    version = listing.lifecycle_version
    assert client.get(path).status_code == 404
    assert client.post(path, payload(listing, "resume")).status_code == 404
    listing.refresh_from_db()
    assert listing.status == "paused" and listing.lifecycle_version == version
    owner = Client()
    owner.force_login(person.agency.owner)
    session = owner.session
    session["mfa_version"] = person.agency.owner.mfa_version
    session.save()
    assert owner.post(path, payload(listing, "resume")).status_code == 302


def test_expiry_racing_renewal_never_expires_new_period(request):
    request.getfixturevalue("directory")
    person, listing, client = own()
    Listing.objects.filter(pk=listing.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    data = payload(listing, "renew", confirm="on")
    barrier = Barrier(2)

    def task():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return expire_one(listing.pk)
        finally:
            connections.close_all()

    def renew():
        close_old_connections()
        try:
            current = Client()
            current.force_login(User.objects.get(pk=person.individual_id))
            barrier.wait(timeout=10)
            return current.post(f"/en/listing/{listing.pk}/manage/", data).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        task_result = executor.submit(task)
        action_result = executor.submit(renew)
        expired, response = task_result.result(), action_result.result()
    assert response in [302, 409]
    if response == 409:
        assert expired
        assert (
            client.post(
                f"/en/listing/{listing.pk}/manage/", payload(listing, "renew", confirm="on")
            ).status_code
            == 302
        )
    listing.refresh_from_db()
    assert listing.status == "published" and listing.expires_at > timezone.now() + timedelta(
        days=29
    )
    assert not expire_one(listing.pk)
    assert LifecycleAction.objects.filter(listing=listing, operation="renew").count() == 1
    assert LifecycleAction.objects.filter(listing=listing, operation="expire").count() <= 1


def test_mobile_renewal_confirms_data_and_preserves_publication(live_server, request, settings):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    request.getfixturevalue("directory")
    _, listing, _ = own()
    listing_id, approved = listing.pk, listing.approved_revision_id
    Listing.objects.filter(pk=listing_id).update(expires_at=timezone.now() + timedelta(days=3))
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
            page.locator("[name=operation]").select_option("renew")
            page.get_by_role("button", name="Apply action", exact=True).click()
            expect(
                page.get_by_text(
                    "Confirm data; renewal opens seven days before expiry", exact=False
                )
            ).to_be_visible()
            page.locator("[name=confirm]").check()
            page.get_by_role("button", name="Apply action", exact=True).click()
            expect(page.locator("p").filter(has_text=" · renew · ")).to_be_visible()
            page.reload()
            expect(page.locator("p").filter(has_text=" · renew · ")).to_be_visible()
            assert str(listing_id) in page.url
        finally:
            browser.close()
    listing.refresh_from_db()
    assert listing.approved_revision_id == approved
    assert listing.expires_at > timezone.now() + timedelta(days=29)
