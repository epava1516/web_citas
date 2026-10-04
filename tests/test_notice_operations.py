import json
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_complaint_listing_linking import staff_for
from test_notice_delivery import queued
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import ComplaintNotice, NoticeRecovery, ReportNotice
from apps.safety.notice_delivery import process_outbox
from apps.safety.notice_operations import requeue

pytestmark = pytest.mark.django_db(transaction=True)


def grant(user):
    user.user_permissions.add(Permission.objects.get(codename="manage_notice_delivery"))
    for attr in ["_perm_cache", "_user_perm_cache"]:
        user.__dict__.pop(attr, None)


def failed_report(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    notice = ReportNotice.objects.get(report=report)
    notice.status, notice.attempts, notice.error_code = "failed", 5, "adapter_failure"
    notice.save()
    user, staff = reviewer()
    grant(user)
    return notice, user, staff


def data(version=0):
    return {
        "key": uuid.uuid4(),
        "version": version,
        "reason": "Synthetic operational repair reviewed before retry",
    }


def test_recovery_preserves_history_replays_and_case_decision(request, settings):
    notice, user, staff = failed_report(request)
    path = f"/en/moderation/notices/report/{notice.pk}/"
    response = staff.get(path)
    assert response.status_code == 200 and response["Cache-Control"] == "private, no-store"
    assert b"private@example.invalid" not in response.content
    first = data()
    assert staff.post(path, first).status_code == 302
    notice.refresh_from_db()
    assert (notice.status, notice.attempts, notice.recovery_version) == ("queued", 0, 1)
    action = NoticeRecovery.objects.get()
    assert (
        action.previous_attempts == 5
        and unseal(action.encrypted_reason)["reason"] == first["reason"]
    )
    assert first["reason"] not in action.encrypted_reason
    assert notice.report.status == "received" and notice.report.version == 1
    assert staff.post(path, first).status_code == 302
    assert NoticeRecovery.objects.count() == 1
    settings.SAFETY_NOTICE_BACKEND = "simulator"
    assert process_outbox()["simulated"] == 1
    # A later failure must not be reset by the old successful replay or an old form.
    ReportNotice.objects.filter(pk=notice.pk).update(status="failed", attempts=5)
    assert staff.post(path, first).status_code == 302
    notice.refresh_from_db()
    assert notice.status == "failed" and notice.attempts == 5
    assert staff.post(path, data()).status_code == 409
    assert staff.post(path, data(1)).status_code == 302
    assert NoticeRecovery.objects.count() == 2


def test_permission_mfa_expiry_and_conflict_are_revalidated(request):
    notice, user, staff = failed_report(request)
    path = f"/en/moderation/notices/report/{notice.pk}/"
    assert Client().post(path, data()).status_code == 302
    user.user_permissions.remove(Permission.objects.get(codename="manage_notice_delivery"))
    assert staff.get(path).status_code == 403
    grant(user)
    session = staff.session
    session.pop("mfa_version", None)
    session.save()
    assert staff.post(path, data()).status_code == 302
    session = staff.session
    session["mfa_version"] = user.mfa_version
    session.save()
    notice.report.receipt_expires_at = timezone.now() - timedelta(seconds=1)
    notice.report.save()
    assert staff.post(path, data()).status_code == 409
    assert not NoticeRecovery.objects.exists()
    notice.report.actor = user
    notice.report.save()
    assert staff.get(path).status_code == 403
    assert not staff.get("/en/moderation/notices/").context["items"]
    with pytest.raises(PermissionDenied):
        requeue(User.objects.get(pk=user.pk), "report", notice.pk, **data())
    for suffix in ["/missing/1/", "/report/99999999/"]:
        response = staff.get("/en/moderation/notices" + suffix)
        assert response.status_code == 404 and response["Cache-Control"] == "private, no-store"


def test_complaint_recovery_requires_own_scope_and_preserves_resolution(request, settings):
    notice, receipt = queued(request, settings)
    user = notice.resolution.action.actor
    staff = staff_for(user)
    grant(user)
    user.user_permissions.add(Permission.objects.get(codename="review_complaint"))
    ComplaintNotice.objects.filter(pk=notice.pk).update(status="failed", attempts=5)
    path = f"/en/moderation/notices/complaint/{notice.pk}/"
    assert staff.get(path).status_code == 200
    assert staff.post(path, data()).status_code == 302
    assert NoticeRecovery.objects.get().complaint_notice_id == notice.pk
    notice.refresh_from_db()
    assert notice.resolution.complaint.status == "resolved"
    assert b"Notification delivery not confirmed" in Client().get(receipt).content
    notice.resolution.complaint.actor = user
    notice.resolution.complaint.save()
    assert staff.post(path, data(1)).status_code == 403
    assert not staff.get("/en/moderation/notices/?kind=complaint").context["items"]


def test_two_connections_recover_only_once(request):
    notice, user, _ = failed_report(request)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                requeue(actor, "report", notice.pk, **data())
                return "recovered"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker) for _ in range(2)]
        assert sorted(f.result(timeout=20) for f in futures) == ["conflict", "recovered"]
    assert NoticeRecovery.objects.count() == 1
    notice.refresh_from_db()
    assert notice.recovery_version == 1 and notice.attempts == 0


def test_mobile_queue_recovery_and_reload(live_server, request, settings, tmp_path):
    settings.DEBUG = True
    failed_report(request)
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
            page.get_by_role("link", name="Private notice operations", exact=True).click()
            page.get_by_role("link", name="Inspect notice state", exact=True).click()
            page.locator("[name=reason]").fill(
                "Synthetic failure investigated and repaired before recovery"
            )
            page.get_by_role("button", name="Record reason and recover notice", exact=True).click()
            expect(page.get_by_role("heading", name="Recovery history", exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_text("Prior attempts: 5", exact=False)).to_be_visible()
            assert "private@example.invalid" not in page.content()
            assert "Synthetic failure investigated" not in page.content()
        finally:
            browser.close()


def test_scoped_pagination_invalid_identifiers_and_global_key_conflict(request):
    notice, user, staff = failed_report(request)
    extra = [
        ReportNotice.objects.create(
            report=notice.report,
            kind="ack",
            event_key="queue-probe-" + str(index),
            encrypted_payload=notice.encrypted_payload,
        )
        for index in range(51)
    ]
    response = staff.get("/en/moderation/notices/")
    assert len(response.context["items"]) == 50 and response.context["cursor"]
    cursor = response.context["cursor"]
    tail = staff.get(f"/en/moderation/notices/?after={cursor}")
    assert len(tail.context["items"]) == 2 and not tail.context["cursor"]
    assert all(item["notice"].pk > cursor for item in tail.context["items"])
    for query in ["after=bad", "after=-1", "after=999999999999999999999", "kind=other"]:
        assert staff.get("/en/moderation/notices/?" + query).status_code == 400
    response = staff.get("/en/moderation/notices/report/999999999999999999999/")
    assert response.status_code == 404 and response["X-Robots-Tag"] == "noindex, nofollow"
    assert staff.put("/en/moderation/notices/").status_code == 405
    other = extra[0]
    other.status, other.attempts = "failed", 5
    other.save()
    first = data()
    requeue(user, "report", notice.pk, **first)
    with pytest.raises(ValidationError):
        requeue(user, "report", other.pk, **first)
    other.refresh_from_db()
    assert other.status == "failed" and other.recovery_version == 0
    assert NoticeRecovery.objects.count() == 1
    malformed = staff.post(f"/en/moderation/notices/report/{other.pk}/?before=bad", data())
    assert malformed.status_code == 400 and NoticeRecovery.objects.count() == 1


def test_complete_recovery_history_and_csrf_input_guards(request):
    notice, user, staff = failed_report(request)
    path = f"/en/moderation/notices/report/{notice.pk}/"
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    session = csrf.session
    session["mfa_version"] = user.mfa_version
    session.save()
    assert csrf.post(path, data()).status_code == 403
    assert not NoticeRecovery.objects.exists()
    assert staff.post(path, data() | {"reason": "bad"}).status_code == 400
    assert not NoticeRecovery.objects.exists()
    # Synthetic failed cycles; recovery itself uses the real transactional service.
    for version in range(52):
        ReportNotice.objects.filter(pk=notice.pk).update(status="failed", attempts=5)
        requeue(user, "report", notice.pk, **data(version))
    page = staff.get(path)
    assert len(page.context["history"]) == 50 and page.context["history_cursor"]
    tail = staff.get(path + f"?before={page.context['history_cursor']}")
    assert len(tail.context["history"]) == 2 and not tail.context["history_cursor"]
    assert {item.pk for item in page.context["history"]}.isdisjoint(
        {item.pk for item in tail.context["history"]}
    )
    assert b"Synthetic operational repair reviewed" not in page.content
    assert staff.get(path + "?before=0").status_code == 400
    user.user_permissions.remove(Permission.objects.get(codename="review_report"))
    assert staff.get(path).status_code == 403
    assert not staff.get("/en/moderation/notices/").context["items"]
