from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.db import close_old_connections, connections
from django.test import Client
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_intake import data

from apps.safety.crypto import unseal
from apps.safety.models import RightsAccess, RightsMessage, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    request.getfixturevalue("directory")
    client = Client()
    receipt = client.post("/en/safety/rights/", data(client)).url
    case = RightsRequest.objects.get()
    return client, receipt, case


def clarification(client, receipt, **changes):
    return {
        **client.get(receipt).context["form"].initial,
        "text": "Confidential additional information about my request",
        **changes,
    }


def test_clarification_is_encrypted_replay_safe_and_does_not_reset_clock(request):
    client, receipt, case = prepared(request)
    dates = case.received_at, case.initial_due_at
    submitted = clarification(client, receipt)
    assert client.post(receipt, submitted).status_code == 302
    assert client.post(receipt, submitted).status_code == 302
    message = RightsMessage.objects.get()
    assert submitted["text"] not in message.encrypted_payload
    assert unseal(message.encrypted_payload)["text"] == submitted["text"]
    case.refresh_from_db()
    assert case.version == 2 and (case.received_at, case.initial_due_at) == dates
    assert case.scope_status == "unverified" and case.status == "received"
    assert submitted["text"].encode() not in client.get(receipt).content
    assert (
        client.post(
            receipt, {**submitted, "text": "Different clarification using the old key"}
        ).status_code
        == 409
    )
    assert RightsMessage.objects.count() == 1
    bad = receipt.rstrip("/").rsplit("/", 1)[0] + "/" + "a" * 43 + "/"
    assert client.post(bad, submitted).status_code == 404
    assert Client(enforce_csrf_checks=True).post(receipt, submitted).status_code == 403


def test_reviewer_only_reads_clarifications_after_audited_post(request):
    client, receipt, case = prepared(request)
    text = "<script>window.privateClarification=true</script> Synthetic evidence"
    assert client.post(receipt, clarification(client, receipt, text=text)).status_code == 302
    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    path = f"/en/moderation/rights/{case.pk}/"
    assert b"privateClarification" not in staff.get(path).content
    response = staff.post(path, {"purpose": "Inspect the new clarification and its scope"})
    assert response.status_code == 200
    assert response.context["messages"][0]["text"] == text
    assert (
        b"&lt;script&gt;" in response.content
        and b"<script>window.privateClarification" not in response.content
    )
    assert RightsAccess.objects.count() == 1
    assert b"privateClarification" not in staff.get(path).content
    assert b"privateClarification" not in client.get(receipt).content


def test_concurrent_same_reply_creates_one_message_and_one_version_increment(request):
    client, receipt, case = prepared(request)
    submitted = clarification(client, receipt)
    barrier = Barrier(2)

    def reply(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            response = Client().post(receipt, submitted)
            return response.status_code, response.url
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(reply, range(2)))
    assert outcomes[0] == outcomes[1] and outcomes[0][0] == 302
    assert RightsMessage.objects.count() == 1
    case.refresh_from_db()
    assert case.version == 2


def test_new_clarification_invalidates_old_staff_form_and_scope_marker(request):
    from test_rights_assignment import action

    client, receipt, case = prepared(request)
    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    path, old = action(staff, case, "claim")
    # Fault injection of a stale marker is not evidence of verified identity.
    RightsRequest.objects.filter(pk=case.pk).update(scope_status="verified")
    assert client.post(receipt, clarification(client, receipt)).status_code == 302
    assert staff.post(path, old).status_code == 409
    case.refresh_from_db()
    assert case.scope_status == "unverified" and case.assigned_to_id is None


def test_older_clarifications_are_accessible_with_audited_cursor(request):
    client, receipt, case = prepared(request)
    for index in range(52):
        submitted = clarification(client, receipt, text=f"Synthetic clarification number {index}")
        response = Client(REMOTE_ADDR=f"192.0.2.{index + 1}").post(receipt, submitted)
        assert response.status_code == 302
    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    path = f"/en/moderation/rights/{case.pk}/"
    first = staff.post(path, {"purpose": "Inspect latest clarification messages for this request"})
    assert len(first.context["messages"]) == 50
    second = staff.post(
        path,
        {
            "purpose": "Inspect earlier clarification messages for this request",
            "message_before": first.context["next_message_cursor"],
        },
    )
    assert len(second.context["messages"]) == 2 and second.context["next_message_cursor"] is None
    texts = [
        message["text"] for response in [first, second] for message in response.context["messages"]
    ]
    assert texts == [f"Synthetic clarification number {index}" for index in range(51, -1, -1)]
    assert RightsAccess.objects.count() == 2


def test_mobile_clarification_persists_without_account_or_text_disclosure(
    live_server, request, settings
):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    _, receipt, case = prepared(request)
    dates = case.received_at, case.initial_due_at
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + receipt)
            page.locator("[name=text]").fill(
                "Synthetic confidential clarification added without an account"
            )
            page.get_by_role("button", name="Submit clarification", exact=True).click()
            expect(page.get_by_role("heading", name="Request received", exact=True)).to_be_visible()
            expect(page.get_by_text("Recorded clarifications: 1", exact=True)).to_be_visible()
            page.reload()
            assert "Synthetic confidential clarification" not in page.content()
            assert "/account/" not in page.url
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.version == 2 and (case.received_at, case.initial_due_at) == dates
    assert RightsMessage.objects.count() == 1
