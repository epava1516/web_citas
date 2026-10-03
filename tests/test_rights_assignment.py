import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_intake import data

from apps.core.models import User
from apps.safety.models import RightsAction, RightsRequest
from apps.safety.rights_actions import act

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    client = request.getfixturevalue("directory")
    client.post("/en/safety/rights/", data(client, kind="representation"))
    case = RightsRequest.objects.get()
    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    return case, user, staff


def action(staff, case, operation):
    path = f"/en/moderation/rights/{case.pk}/action/"
    initial = staff.get(path).context["form"].initial
    return path, {
        **initial,
        "operation": operation,
        "reason": "Administrative reason for this rights assignment",
    }


def test_assignment_and_coordinator_recovery_preserve_dates_and_replay(request):
    case, user, staff = prepared(request)
    dates = case.received_at, case.initial_due_at
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    assert staff.post(path, claim).status_code == 302
    case.refresh_from_db()
    assert case.assigned_to_id == user.pk and case.status == "reviewing" and case.version == 2
    path, reset = action(staff, case, "unassign")
    assert staff.post(path, reset).status_code == 403
    user.user_permissions.add(Permission.objects.get(codename="manage_rights_assignment"))
    assert staff.post(path, reset).status_code == 302
    path, newer = action(staff, case, "claim")
    assert staff.post(path, newer).status_code == 302
    assert staff.post(path, reset).status_code == 302
    case.refresh_from_db()
    assert case.assigned_to_id == user.pk and case.version == 4
    assert (case.received_at, case.initial_due_at) == dates
    assert RightsAction.objects.count() == 3
    assert "Administrative reason" not in RightsAction.objects.first().encrypted_reason


def test_author_cannot_assign_own_request_and_stale_version_cannot_reset(request):
    case, user, staff = prepared(request)
    path, old = action(staff, case, "claim")
    assert staff.post(path, old).status_code == 302
    user.user_permissions.add(Permission.objects.get(codename="manage_rights_assignment"))
    old.update(key=uuid.uuid4(), operation="unassign")
    assert staff.post(path, old).status_code == 409
    RightsRequest.objects.filter(pk=case.pk).update(actor=user)
    assert staff.post(path, old).status_code == 403
    assert RightsAction.objects.count() == 1


def test_two_reviewers_cannot_claim_same_rights_request(request):
    from django.core.exceptions import ValidationError

    case, first, _ = prepared(request)
    second = User.objects.get(username="fixture-v1-visitor")
    second.mfa_enabled = True
    second.save(update_fields=["mfa_enabled"])
    second.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    barrier = Barrier(2)

    def claim(actor_id):
        close_old_connections()
        try:
            actor = User.objects.get(pk=actor_id)
            barrier.wait(timeout=10)
            try:
                act(
                    actor,
                    case.pk,
                    uuid.uuid4(),
                    1,
                    "claim",
                    "Claim case for proportional rights verification",
                )
                return actor_id
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(claim, [first.pk, second.pk]))
    case.refresh_from_db()
    assert outcomes.count(None) == 1
    assert case.assigned_to_id in [value for value in outcomes if value]
    assert case.version == 2 and RightsAction.objects.count() == 1


def test_independent_coordinator_recovers_after_assignee_loses_permission(request):
    case, original, staff = prepared(request)
    dates = case.received_at, case.initial_due_at
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    original.user_permissions.remove(Permission.objects.get(codename="review_rights_request"))
    assert staff.get(path).status_code == 403
    coordinator = User.objects.get(username="fixture-v1-visitor")
    coordinator.mfa_enabled = True
    coordinator.mfa_version = 1
    coordinator.save(update_fields=["mfa_enabled", "mfa_version"])
    coordinator.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["review_rights_request", "manage_rights_assignment"]
        )
    )
    admin = Client()
    admin.force_login(coordinator)
    session = admin.session
    session["mfa_version"] = 1
    session.save()
    path, reset = action(admin, case, "unassign")
    assert admin.post(path, reset).status_code == 302
    path, newer = action(admin, case, "claim")
    assert admin.post(path, newer).status_code == 302
    case.refresh_from_db()
    assert case.assigned_to_id == coordinator.pk and case.status == "reviewing"
    assert (case.received_at, case.initial_due_at) == dates


def test_mobile_rights_assignment_reset_and_reclaim(live_server, request, settings, tmp_path):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, user, _ = prepared(request)
    dates = case.received_at, case.initial_due_at
    user.user_permissions.add(Permission.objects.get(codename="manage_rights_assignment"))
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
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.goto(live_server.url + "/en/moderation/rights/")
            page.get_by_role("link", name="Inspect request", exact=True).click()
            for operation in ["claim", "unassign", "claim"]:
                page.get_by_role("link", name="Request actions", exact=True).click()
                page.locator("[name=operation]").select_option(operation)
                page.locator("[name=reason]").fill(
                    "Administrative synthetic reason without resetting request deadline"
                )
                page.get_by_role("button", name="Record assignment action", exact=True).click()
                expect(
                    page.get_by_role("heading", name="Private rights inspection", exact=True)
                ).to_be_visible()
            page.reload()
            assert "reviewing" in page.content()
            assert "rights-private@example.invalid" not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.version == 4 and case.assigned_to_id == user.pk
    assert (case.received_at, case.initial_due_at) == dates
    assert RightsAction.objects.count() == 3


def test_overdue_request_remains_visible_while_assigned(request):
    from datetime import timedelta

    from django.utils import timezone

    case, _, staff = prepared(request)
    due = timezone.now() - timedelta(days=1)
    RightsRequest.objects.filter(pk=case.pk).update(initial_due_at=due)
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    response = staff.get("/en/moderation/rights/")
    assert case.pk in [item.pk for item in response.context["cases"]]
    assert b"Internal target overdue" in response.content
    case.refresh_from_db()
    assert case.status == "reviewing" and case.initial_due_at == due
