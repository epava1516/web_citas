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
from test_complaint_assignment import action, coordinator, prepared
from test_report_decisions import action as report_action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.safety.complaint_actions import act
from apps.safety.models import ComplaintAction, ReportAction, Restriction

pytestmark = pytest.mark.django_db(transaction=True)


def decision(request):
    directory_client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-individual")
    report = case(directory_client, person)
    user, staff = reviewer()
    path, data = report_action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    assert (
        staff.post(
            f"/en/moderation/reports/{report.pk}/",
            {"purpose": "Inspect before original synthetic decision"},
        ).status_code
        == 200
    )
    path, data = report_action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 302
    report.refresh_from_db()
    return ReportAction.objects.get(report=report, operation="restrict"), report, user, staff


def link_data(staff, complaint, target, report):
    path, data = action(staff, complaint, "link")
    return path, data | {"decision_id": target.pk, "decision_case_version": report.version}


def test_link_requires_current_read_independence_and_preserves_restriction(request):
    complaint, _, _, receipt = prepared(request)
    target, report, original, original_client = decision(request)
    owner, staff = coordinator()
    path, data = action(staff, complaint, "claim")
    assert staff.post(path, data).status_code == 302
    path, data = link_data(staff, complaint, target, report)
    assert staff.post(path, data | {"decision_id": 10**40}).status_code == 400
    assert staff.post(path, data).status_code == 409
    assert (
        staff.post(
            f"/en/moderation/complaints/{complaint.pk}/",
            {"purpose": "Inspect current complaint before binding decision"},
        ).status_code
        == 200
    )
    assert staff.post(path, data | {"decision_case_version": report.version + 1}).status_code == 409
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    complaint.refresh_from_db()
    assert complaint.decision_id == target.pk and complaint.decision_case_version == report.version
    assert complaint.version == 3 and complaint.assigned_to_id == owner.pk
    assert ComplaintAction.objects.filter(operation="link").count() == 1
    assert Restriction.objects.get(report=report).active
    assert Client().get(f"/en/listing/{report.listing_id}/").status_code == 404
    body = Client().get(receipt).content
    assert str(report.pk).encode() not in body and report.encrypted_payload.encode() not in body
    assert b"private@example.invalid" not in body and b"Private notifier" not in body
    # Existing decision maker loses access to the linked request, including its queue row.
    assert original_client.get(f"/en/moderation/complaints/{complaint.pk}/").status_code == 403
    assert not original_client.get("/en/moderation/complaints/").context["complaints"]
    assert original.pk != owner.pk


def test_original_decision_maker_cannot_link_and_rolls_back(request):
    complaint, _, staff, _ = prepared(request)
    target, report, _, _ = decision(request)
    path, data = action(staff, complaint, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/complaints/{complaint.pk}/",
        {"purpose": "Inspect request before attempted conflicting link"},
    )
    path, data = link_data(staff, complaint, target, report)
    assert staff.post(path, data).status_code == 403
    complaint.refresh_from_db()
    assert complaint.decision_id is None and complaint.version == 2
    assert ComplaintAction.objects.count() == 1


def test_linked_current_manager_cannot_read_or_act_after_management_change(request):
    complaint, _, _, _ = prepared(request)
    target, report, _, _ = decision(request)
    owner, staff = coordinator()
    path, data = action(staff, complaint, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/complaints/{complaint.pk}/",
        {"purpose": "Inspect request before independent decision link"},
    )
    path, data = link_data(staff, complaint, target, report)
    assert staff.post(path, data).status_code == 302
    Person.objects.filter(pk=report.listing.person_id).update(individual=owner)
    owner.user_permissions.add(Permission.objects.get(codename="manage_complaint_assignment"))
    assert staff.get(f"/en/moderation/complaints/{complaint.pk}/").status_code == 403
    assert (
        staff.post(
            f"/en/moderation/complaints/{complaint.pk}/",
            {"purpose": "Attempt access after acquiring conflicting management"},
        ).status_code
        == 403
    )
    assert staff.get(path).status_code == 403
    assert staff.post(path, data).status_code == 403
    assert not staff.get("/en/moderation/complaints/").context["complaints"]


def test_concurrent_link_records_only_one_action(request):
    complaint, _, _, _ = prepared(request)
    target, report, _, _ = decision(request)
    owner, staff = coordinator()
    path, data = action(staff, complaint, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/complaints/{complaint.pk}/",
        {"purpose": "Inspect current evidence before concurrent link"},
    )
    barrier = Barrier(2)

    def link():
        close_old_connections()
        try:
            user = User.objects.get(pk=owner.pk)
            barrier.wait(timeout=10)
            try:
                act(
                    user,
                    complaint.pk,
                    uuid.uuid4(),
                    2,
                    "link",
                    "Concurrent synthetic independent link",
                    target.pk,
                    report.version,
                )
                return "ok"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(link) for _ in range(2)]
        assert sorted(job.result() for job in jobs) == ["conflict", "ok"]
    complaint.refresh_from_db()
    assert complaint.version == 3 and complaint.decision_id == target.pk
    assert ComplaintAction.objects.filter(operation="link").count() == 1


def test_mobile_independent_link_reload_and_minimal_anonymous_receipt(
    live_server, request, settings, tmp_path
):
    settings.DEBUG = True
    complaint, _, _, receipt = prepared(request)
    target, report, _, _ = decision(request)
    coordinator()
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["agency"]
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
            page.get_by_role("link", name="Request actions", exact=True).click()
            page.locator("[name=operation]").select_option("claim")
            page.locator("[name=reason]").fill("Acquire independent synthetic review request")
            page.get_by_role("button", name="Record request action", exact=True).click()
            page.locator("[name=purpose]").fill(
                "Read request before choosing the disputed decision"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_be_visible()
            page.get_by_role("link", name="Request actions", exact=True).click()
            page.locator("[name=operation]").select_option("link")
            page.locator("[name=decision_id]").fill(str(target.pk))
            page.locator("[name=decision_case_version]").fill(str(report.version))
            page.locator("[name=reason]").fill(
                "The synthetic reference identifies this exact decision"
            )
            page.get_by_role("button", name="Record request action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private decision review intake", exact=True)
            ).to_be_visible()
            page.reload()
            expect(page.locator(f'[data-linked-decision="{target.pk}"]')).to_be_visible()
            expect(
                page.get_by_role("heading", name="Restricted information", exact=True)
            ).to_have_count(0)
            anonymous = browser.new_page()
            anonymous.goto(live_server.url + receipt)
            assert "Private notifier" not in anonymous.content()
            assert str(report.pk) not in anonymous.content()
        finally:
            browser.close()
    complaint.refresh_from_db()
    assert complaint.decision_id == target.pk and complaint.version == 3
    assert Restriction.objects.get(report=report).active
