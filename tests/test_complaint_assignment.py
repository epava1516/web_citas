import json
import shutil
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pyotp
import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_complaint_intake import moderator, payload
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.complaint_actions import act
from apps.safety.crypto import unseal
from apps.safety.models import Complaint, ComplaintAction

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    request.getfixturevalue("directory")
    client = Client()
    receipt = client.post("/en/safety/complaints/", payload(client)).url
    case = Complaint.objects.get()
    user, staff = moderator()
    return case, user, staff, receipt


def action(staff, case, operation):
    path = f"/en/moderation/complaints/{case.pk}/action/"
    form = staff.get(path).context["form"]
    return path, form.initial | {
        "operation": operation,
        "reason": "Private synthetic case assignment reason",
    }


def coordinator():
    user = User.objects.get(username="fixture-v1-agency")
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_complaint", "manage_complaint_assignment"])
    )
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session.save()
    return user, client


def test_assignment_recovery_replay_and_private_receipt_without_clock_reset(request):
    case, user, staff, receipt = prepared(request)
    created, expires, cipher = case.created_at, case.receipt_expires_at, case.encrypted_payload
    path, data = action(staff, case, "claim")
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    case.refresh_from_db()
    assert case.assigned_to_id == user.pk and case.version == 2 and case.status == "reviewing"
    assert ComplaintAction.objects.count() == 1
    assert unseal(ComplaintAction.objects.get().encrypted_reason)["reason"] == data["reason"]
    assert data["reason"].encode() not in Client().get(receipt).content
    path, unassign = action(staff, case, "unassign")
    assert staff.post(path, unassign).status_code == 403
    _, admin = coordinator()
    path, unassign = action(admin, case, "unassign")
    user.user_permissions.remove(Permission.objects.get(codename="review_complaint"))
    assert admin.post(path, unassign).status_code == 302
    path, claim = action(admin, case, "claim")
    assert admin.post(path, claim).status_code == 302
    assert admin.post(path, unassign).status_code == 302
    case.refresh_from_db()
    assert case.status == "reviewing" and case.version == 4 and case.assigned_to_id is not None
    assert (
        case.created_at == created
        and case.receipt_expires_at == expires
        and case.encrypted_payload == cipher
    )
    assert ComplaintAction.objects.count() == 3
    assert len(admin.get("/en/moderation/complaints/").context["complaints"]) == 1


def test_own_case_stale_version_wrong_key_and_closed_case_cannot_be_reassigned(request):
    case, user, staff, _ = prepared(request)
    path, data = action(staff, case, "claim")
    Complaint.objects.filter(pk=case.pk).update(actor=user)
    assert staff.post(path, data).status_code == 403
    Complaint.objects.filter(pk=case.pk).update(actor=None)
    assert staff.post(path, data | {"version": 999}).status_code == 409
    assert not ComplaintAction.objects.exists()
    assert staff.post(path, data).status_code == 302
    assert (
        staff.post(path, data | {"reason": "Different reason for the same action key"}).status_code
        == 409
    )
    admin, second = coordinator()
    path, unassign = action(second, case, "unassign")
    Complaint.objects.filter(pk=case.pk).update(status="resolved")
    assert second.post(path, unassign).status_code == 409
    assert ComplaintAction.objects.count() == 1
    # Controlled future state, not a claim of an implemented resolution route.
    assert admin.pk != user.pk


def test_two_moderators_concurrently_claim_one_case(request):
    case, first, _, _ = prepared(request)
    second, _ = coordinator()
    barrier = Barrier(2)

    def claim(user_id):
        close_old_connections()
        try:
            user = User.objects.get(pk=user_id)
            barrier.wait(timeout=10)
            try:
                act(
                    user,
                    case.pk,
                    uuid.uuid4(),
                    1,
                    "claim",
                    "Acquire synthetic request for private review",
                )
                return "ok"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(claim, user.pk) for user in [first, second]]
        assert sorted(job.result() for job in jobs) == ["conflict", "ok"]
    case.refresh_from_db()
    assert case.version == 2 and ComplaintAction.objects.count() == 1


def test_same_key_across_cases_rolls_back_losing_assignment(request):
    case, user, _, _ = prepared(request)
    client = Client()
    client.post("/en/safety/complaints/", payload(client))
    other = Complaint.objects.exclude(pk=case.pk).get()
    key, barrier = uuid.uuid4(), Barrier(2)

    def claim(case_id):
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                act(
                    actor,
                    case_id,
                    key,
                    1,
                    "claim",
                    "Acquire one synthetic request with shared action key",
                )
                return "ok"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(claim, item.pk) for item in [case, other]]
        assert sorted(job.result() for job in jobs) == ["conflict", "ok"]
    assert ComplaintAction.objects.count() == 1
    assert list(Complaint.objects.order_by("version").values_list("version", flat=True)) == [1, 2]
    assert Complaint.objects.filter(status="received", assigned_to__isnull=True).count() == 1


def test_mobile_claim_recovery_reload_and_no_private_reason_in_receipt(
    live_server, request, settings, tmp_path
):
    settings.DEBUG = True
    case, user, _, receipt = prepared(request)
    user.user_permissions.add(Permission.objects.get(codename="manage_complaint_assignment"))
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
            page.get_by_role("link", name="Private review requests", exact=True).click()
            page.get_by_role("link", name="Inspect review request", exact=True).click()
            for operation in ["claim", "unassign", "claim"]:
                page.get_by_role("link", name="Request actions", exact=True).click()
                page.locator("[name=operation]").select_option(operation)
                page.locator("[name=reason]").fill("Private mobile request assignment reason")
                page.get_by_role("button", name="Record request action", exact=True).click()
                expect(
                    page.get_by_role("heading", name="Private decision review intake", exact=True)
                ).to_be_visible()
                page.reload()
            anonymous = browser.new_page()
            anonymous.goto(live_server.url + receipt)
            expect(anonymous.get_by_text("reviewing", exact=False)).to_be_visible()
            assert "Private mobile request assignment reason" not in anonymous.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.version == 4 and case.assigned_to_id == user.pk
