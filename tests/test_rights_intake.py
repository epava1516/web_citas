from datetime import datetime

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.models import RightsAccess, RightsRequest
from apps.safety.rights import next_month

pytestmark = pytest.mark.django_db(transaction=True)


def data(client, **changes):
    initial = client.get("/en/safety/rights/").context["form"].initial
    return {
        **initial,
        "kind": "access",
        "reference": "My synthetic profile",
        "explanation": "My data",
        "email": "rights-private@example.invalid",
        **changes,
    }


def test_rights_receipt_is_private_replay_safe_and_does_not_grant_data(request):
    request.getfixturevalue("directory")
    client = Client()
    payload = data(client)
    response = client.post("/en/safety/rights/", payload)
    assert response.status_code == 302
    case = RightsRequest.objects.get()
    assert case.actor_id is None and case.status == "received"
    assert payload["email"] not in case.encrypted_payload
    assert unseal(case.encrypted_payload)["explanation"] == "My data"
    receipt = client.get(response.url)
    assert receipt.status_code == 200
    assert (
        b"rights-private@example.invalid" not in receipt.content
        and b"My synthetic profile" not in receipt.content
    )
    assert (
        receipt["Cache-Control"] == "private, no-store"
        and receipt["X-Robots-Tag"] == "noindex, nofollow"
    )
    assert client.post("/en/safety/rights/", payload).url == response.url
    case.refresh_from_db()
    due = case.initial_due_at
    assert client.post("/en/safety/rights/", {**payload, "kind": "erase"}).status_code == 409
    assert RightsRequest.objects.count() == 1
    case.refresh_from_db()
    assert case.initial_due_at == due
    assert client.get(response.url.replace(payload["receipt_secret"], "a" * 43)).status_code == 404
    assert not RightsAccess.objects.exists()


def test_rights_permission_is_separate_mfa_required_and_inspection_audited(request):
    client = request.getfixturevalue("directory")
    client.post("/en/safety/rights/", data(client, kind="representation"))
    case = RightsRequest.objects.get()
    user, staff = reviewer()
    path = f"/en/moderation/rights/{case.pk}/"
    assert staff.get(path).status_code == 403
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    assert staff.get(path).status_code == 200
    assert b"rights-private@example.invalid" not in staff.get(path).content
    response = staff.post(path, {"purpose": "Inspect request to establish identity and scope"})
    assert response.status_code == 200 and b"rights-private@example.invalid" in response.content
    assert RightsAccess.objects.get().actor_id == user.pk
    assert b"rights-private@example.invalid" not in staff.get(path).content
    RightsRequest.objects.filter(pk=case.pk).update(actor=user)
    assert staff.post(path, {"purpose": "Inspect a request submitted by myself"}).status_code == 403
    assert not staff.get("/en/moderation/rights/").context["cases"]
    assert RightsAccess.objects.count() == 1


@pytest.mark.parametrize(
    "value,expected",
    [
        ("2025-01-31T10:00:00+01:00", (2025, 2, 28)),
        ("2024-01-31T10:00:00+01:00", (2024, 2, 29)),
        ("2025-12-31T10:00:00+01:00", (2026, 1, 31)),
    ],
)
def test_internal_target_uses_calendar_month_not_thirty_days(value, expected):
    with timezone.override("Europe/Madrid"):
        result = next_month(datetime.fromisoformat(value))
    assert (result.year, result.month, result.day) == expected
    assert result.hour == 10


def test_rights_only_permission_still_requires_current_mfa(request):
    from apps.core.models import User

    client = request.getfixturevalue("directory")
    client.post("/en/safety/rights/", data(client))
    user = User.objects.get(username="fixture-v1-visitor")
    assert not user.is_staff and not user.mfa_enabled
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    staff = Client()
    staff.force_login(user)
    assert staff.get("/en/moderation/rights/").url == "/en/account/mfa/enroll/"
    user.mfa_enabled = True
    user.mfa_version = 1
    user.save(update_fields=["mfa_enabled", "mfa_version"])
    assert staff.get("/en/moderation/rights/").url == "/en/account/mfa/"
    session = staff.session
    session["mfa_version"] = 1
    session.save()
    assert staff.get("/en/moderation/rights/").status_code == 200
    assert staff.get("/en/moderation/reports/").status_code == 403


def test_concurrent_receipt_replays_create_one_rights_request(request):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    client = request.getfixturevalue("directory")
    submitted = data(client, kind="representation")
    barrier = Barrier(2)

    def submit(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = Client().post("/en/safety/rights/", submitted)
            return response.status_code, response.url
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(submit, range(2)))
    assert responses[0] == responses[1] and responses[0][0] == 302
    assert RightsRequest.objects.count() == 1


def test_mobile_representation_request_without_account_and_private_reload(
    live_server, request, settings
):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    request.getfixturevalue("directory")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + "/en/legal/")
            page.get_by_role(
                "link", name="Rights and representation requests without an account", exact=True
            ).click()
            page.locator("[name=kind]").select_option("representation")
            page.locator("[name=reference]").fill("My synthetic represented profile")
            page.locator("[name=explanation]").fill(
                "I request review of representation and withdrawal of my synthetic profile"
            )
            page.locator("[name=email]").fill("mobile-rights@example.invalid")
            page.get_by_role("button", name="Submit request", exact=True).click()
            expect(page.get_by_role("heading", name="Request received", exact=True)).to_be_visible()
            assert "/account/" not in page.url
            page.reload()
            expect(page.get_by_role("heading", name="Request received", exact=True)).to_be_visible()
            assert "mobile-rights@example.invalid" not in page.content()
            assert "My synthetic represented profile" not in page.content()
        finally:
            browser.close()
    assert RightsRequest.objects.get().kind == "representation"


def test_unverified_account_can_request_rights_and_expired_receipt_is_hidden(request):
    from datetime import timedelta

    from apps.core.models import User

    request.getfixturevalue("directory")
    user = User.objects.get(username="fixture-v1-visitor")
    User.objects.filter(pk=user.pk).update(email_verified_at=None)
    client = Client()
    client.force_login(user)
    submitted = data(client, kind="erase")
    response = client.post("/en/safety/rights/", submitted)
    assert response.status_code == 302
    case = RightsRequest.objects.get()
    assert case.actor_id == user.pk and client.get(response.url).status_code == 200
    RightsRequest.objects.filter(pk=case.pk).update(
        receipt_expires_at=timezone.now() - timedelta(seconds=1)
    )
    assert client.get(response.url).status_code == 404
    assert RightsRequest.objects.get().status == "received"


def test_brief_request_without_reference_or_contact_is_received_for_clarification(request):
    request.getfixturevalue("directory")
    client = Client()
    response = client.post(
        "/en/safety/rights/", data(client, reference="", explanation="Mis datos", email="")
    )
    assert response.status_code == 302
    case = RightsRequest.objects.get()
    assert case.status == "received"
    assert unseal(case.encrypted_payload)["reference"] == ""
    assert client.get(response.url).status_code == 200
    assert not RightsAccess.objects.exists()
