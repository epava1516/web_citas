import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Barrier
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action
from test_rights_intake import data

from apps.core.models import User
from apps.safety.models import RightsExtension, RightsRequest
from apps.safety.rights import calendar_months
from apps.safety.rights_actions import act

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    request.getfixturevalue("directory")
    client = Client()
    receipt = client.post("/en/safety/rights/", data(client, kind="access")).url
    case = RightsRequest.objects.get()
    user, staff = reviewer()
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_rights_request", "extend_rights_deadline"])
    )
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    assert (
        staff.post(
            f"/en/moderation/rights/{case.pk}/",
            {"purpose": "Review grounds and timing of a response extension"},
        ).status_code
        == 200
    )
    case.refresh_from_db()
    return case, User.objects.get(pk=user.pk), staff, client, receipt


def payload(staff, case, **changes):
    path, values = action(staff, case, "extend")
    return path, {**values, "additional_months": 2, "extension_reason": "complexity", **changes}


def test_extension_preserves_original_dates_and_privacy_and_replay(request):
    case, _, staff, client, receipt = prepared(request)
    original = case.received_at, case.initial_due_at
    path, values = payload(staff, case)
    assert staff.post(path, values).status_code == 302
    assert staff.post(path, values).status_code == 302
    extension = RightsExtension.objects.get()
    case.refresh_from_db()
    assert case.version == 3 and case.status == "reviewing"
    assert (case.received_at, case.initial_due_at) == original
    assert case.effective_due_at == calendar_months(case.received_at, 3) == extension.new_due_at
    assert values["reason"] not in extension.action.encrypted_reason
    page = client.get(receipt)
    assert (
        b"Response target extended" in page.content
        and b"delivery through another channel is not confirmed" in page.content
    )
    assert values["reason"].encode() not in page.content
    assert b"rights-private@example.invalid" not in page.content
    assert (
        b"Fecha prevista de respuesta ampliada"
        in client.get(receipt.replace("/en/", "/es/")).content
    )
    path, newer = payload(staff, case)
    assert staff.post(path, newer).status_code == 409
    assert RightsExtension.objects.count() == 1


def test_late_extension_missing_permission_and_stale_evidence_rejected(request):
    case, user, staff, _, _ = prepared(request)
    path, values = payload(staff, case)
    user.user_permissions.remove(Permission.objects.get(codename="extend_rights_deadline"))
    assert staff.post(path, values).status_code == 403
    user.user_permissions.add(Permission.objects.get(codename="extend_rights_deadline"))
    case.accesses.update(case_version=None)
    assert staff.post(path, values).status_code == 409
    staff.post(
        f"/en/moderation/rights/{case.pk}/",
        {"purpose": "Read latest request evidence for deadline assessment"},
    )
    RightsRequest.objects.filter(pk=case.pk).update(
        initial_due_at=timezone.now() - timedelta(seconds=1)
    )
    assert staff.post(path, values).status_code == 409
    assert not RightsExtension.objects.exists()


@pytest.mark.parametrize(
    "value,months,expected",
    [
        ((2023, 1, 31), 3, (2023, 4, 30)),
        ((2023, 1, 31), 2, (2023, 3, 31)),
        ((2027, 12, 31), 2, (2028, 2, 29)),
        ((2025, 11, 30), 3, (2026, 2, 28)),
    ],
)
def test_calendar_extension_anchored_to_original_month_without_short_month_drift(
    value, months, expected
):
    initial = datetime(*value, 10, 0, tzinfo=ZoneInfo("Europe/Madrid"))
    result = calendar_months(initial, months)
    assert (result.year, result.month, result.day) == expected
    assert result.hour == 10


def test_two_concurrent_extensions_only_record_one_target(request):
    case, user, _, _, _ = prepared(request)
    barrier = Barrier(2)

    def extend(months):
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                act(
                    actor,
                    case.pk,
                    uuid.uuid4(),
                    case.version,
                    "extend",
                    "Motivated synthetic operational deadline extension",
                    additional_months=months,
                    extension_reason="complexity",
                )
                return months
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(extend, [1, 2]))
    assert outcomes.count(None) == 1
    assert RightsExtension.objects.count() == 1
    case.refresh_from_db()
    assert case.version == 3


def test_mobile_extension_action_and_private_requester_notice(
    live_server, request, settings, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, receipt = prepared(request)
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
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/action/")
            page.locator("[name=operation]").select_option("extend")
            page.locator("[name=additional_months]").fill("2")
            page.locator("[name=extension_reason]").select_option("volume")
            page.locator("[name=reason]").fill(
                "Private operational justification for synthetic extension"
            )
            page.get_by_role("button", name="Record assignment action", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt)
            expect(
                anonymous.get_by_role("heading", name="Response target extended", exact=True)
            ).to_be_visible()
            assert "number of requests" in anonymous.content()
            assert "Private operational justification" not in anonymous.content()
            anonymous.reload()
            expect(
                anonymous.get_by_role("heading", name="Response target extended", exact=True)
            ).to_be_visible()
        finally:
            browser.close()
    assert RightsExtension.objects.count() == 1


def test_extension_does_not_hide_overdue_original_notice_delivery(request, monkeypatch):
    from types import SimpleNamespace

    from apps.safety import models

    case, _, staff, _, _ = prepared(request)
    path, values = payload(staff, case)
    assert staff.post(path, values).status_code == 302
    case.refresh_from_db()
    later = case.initial_due_at + timedelta(days=1)
    # Move the deadline presentation clock, preserving session/MFA expiry checks.
    monkeypatch.setattr(models, "timezone", SimpleNamespace(now=lambda: later))
    assert not case.overdue and case.extension_notice_overdue
    response = staff.get("/en/moderation/rights/")
    assert b"Extension delivery unconfirmed; original notice target overdue" in response.content
    assert case.pk in [item.pk for item in response.context["cases"]]
