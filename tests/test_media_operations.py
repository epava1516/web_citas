import json
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_erasure_execution import payload
from test_media_erasure import setup
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.mediafiles.erasure import erase_one
from apps.mediafiles.models import MediaErasure, MediaErasureRecovery
from apps.safety.erasure_execution import execute
from apps.safety.media_operations import requeue

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Synthetic storage incident reviewed and authorization for another deletion cycle"


def exhausted(request, settings, monkeypatch):
    case, actor, person, plan, blob = setup(request, settings, monkeypatch)
    execute(actor, case.pk, plan.pk, **(payload(case) | {"purposes": ["media"]}))
    job = MediaErasure.objects.get(blob=blob)
    MediaErasure.objects.filter(pk=job.pk).update(status="failed", attempts=5)
    actor.user_permissions.add(Permission.objects.get(codename="manage_media_erasure"))
    return case, User.objects.get(pk=actor.pk), person, job


def test_recovery_is_audited_replay_does_not_reset_new_attempts_and_files_finish(
    request, settings, monkeypatch
):
    case, actor, _, job = exhausted(request, settings, monkeypatch)
    key = uuid.uuid4()
    recovery = requeue(actor, case.pk, job.pk, key, 1, REASON)
    job.refresh_from_db()
    assert job.status == "queued" and job.attempts == 0 and job.recovery_version == 2
    assert recovery.previous_attempts == 5 and recovery.previous_version == 1
    assert REASON not in recovery.action.encrypted_reason
    assert erase_one(job.pk)
    job.refresh_from_db()
    assert job.status == "completed" and job.attempts == 1
    assert requeue(actor, case.pk, job.pk, key, 1, REASON).pk == recovery.pk
    job.refresh_from_db()
    assert job.status == "completed" and job.attempts == 1
    assert MediaErasureRecovery.objects.count() == 1
    case.refresh_from_db()
    assert case.status == "reviewing"


def test_recovery_http_permissions_csrf_state_and_private_paths(request, settings, monkeypatch):
    case, actor, person, job = exhausted(request, settings, monkeypatch)
    client = Client()
    client.force_login(actor)
    session = client.session
    session["mfa_version"] = actor.mfa_version
    session.save()
    path = f"/en/moderation/rights/{case.pk}/media-jobs/{job.pk}/"
    data = {"key": uuid.uuid4(), "version": 1, "reason": REASON}
    page = client.get(path)
    assert page.status_code == 200 and page["X-Robots-Tag"] == "noindex, nofollow"
    assert job.blob.original.name.encode() not in page.content
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    assert client.post(path, data | {"version": 999}).status_code == 409
    settings.PRODUCTION = True
    assert client.post(path, data).status_code == 409
    settings.PRODUCTION = False
    manager = Client()
    manager.force_login(person.agency.owner)
    assert manager.get(path).status_code in {302, 403}
    actor.user_permissions.remove(Permission.objects.get(codename="manage_media_erasure"))
    assert client.post(path, data).status_code == 403
    assert not MediaErasureRecovery.objects.exists()


def test_concurrent_recovery_same_key_has_one_cycle(request, settings, monkeypatch):
    case, actor, _, job = exhausted(request, settings, monkeypatch)
    key, barrier = uuid.uuid4(), Barrier(2)

    def run():
        close_old_connections()
        try:
            user = User.objects.get(pk=actor.pk)
            barrier.wait(timeout=10)
            return requeue(user, case.pk, job.pk, key, 1, REASON).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run) for _ in range(2)]
        assert futures[0].result(timeout=30) == futures[1].result(timeout=30)
    job.refresh_from_db()
    assert job.recovery_version == 2 and MediaErasureRecovery.objects.count() == 1


def test_mobile_recovery_queue_and_form(live_server, request, settings, monkeypatch, tmp_path):
    settings.DEBUG = True
    case, _, _, _ = exhausted(request, settings, monkeypatch)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/media-jobs/")
            page.get_by_role("link", name="Review job", exact=True).click()
            page.locator("[name=reason]").fill(REASON)
            page.get_by_role("button", name="Authorize another deletion cycle", exact=True).click()
            expect(
                page.get_by_role("heading", name="File deletion jobs", exact=True)
            ).to_be_visible()
            assert "queued" in page.locator("main").inner_text()
            page.reload()
            assert "queued" in page.locator("main").inner_text()
        finally:
            browser.close()
    assert MediaErasureRecovery.objects.count() == 1


def test_manager_with_operational_permissions_is_still_excluded(request, settings, monkeypatch):
    from django.core.exceptions import PermissionDenied

    case, _, person, job = exhausted(request, settings, monkeypatch)
    manager = person.agency.owner
    manager.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_rights_request", "manage_media_erasure"])
    )
    manager = User.objects.get(pk=manager.pk)
    with pytest.raises(PermissionDenied):
        requeue(manager, case.pk, job.pk, uuid.uuid4(), 1, REASON)
    assert not MediaErasureRecovery.objects.exists()


def test_old_recovery_does_not_reset_a_later_cycle(request, settings, monkeypatch):
    case, actor, _, job = exhausted(request, settings, monkeypatch)
    first_key = uuid.uuid4()
    first = requeue(actor, case.pk, job.pk, first_key, 1, REASON)
    MediaErasure.objects.filter(pk=job.pk).update(status="failed", attempts=5)
    second = requeue(actor, case.pk, job.pk, uuid.uuid4(), 2, REASON)
    assert first.pk != second.pk
    MediaErasure.objects.filter(pk=job.pk).update(attempts=3)
    assert requeue(actor, case.pk, job.pk, first_key, 1, REASON).pk == first.pk
    job.refresh_from_db()
    assert job.recovery_version == 3 and job.attempts == 3
