import pytest
from django.test import Client
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_assignment import action
from test_rights_intake import data
from test_rights_messages import clarification

from apps.safety.crypto import unseal
from apps.safety.models import RightsAction, RightsRequest

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    from django.contrib.auth.models import Permission

    request.getfixturevalue("directory")
    client = Client()
    receipt = client.post("/en/safety/rights/", data(client)).url
    case = RightsRequest.objects.get()
    user, staff = reviewer()
    user.user_permissions.add(Permission.objects.get(codename="review_rights_request"))
    path, claim = action(staff, case, "claim")
    assert staff.post(path, claim).status_code == 302
    return client, receipt, case, staff


def test_question_requires_assignment_current_read_and_is_minimized(request):
    client, receipt, case, staff = prepared(request)
    dates = case.received_at, case.initial_due_at
    path, question = action(staff, case, "clarify")
    question["clarification_prompt"] = "scope"
    assert staff.post(path, question).status_code == 409
    staff.post(
        f"/en/moderation/rights/{case.pk}/", {"purpose": "Read request before asking clarification"}
    )
    assert staff.post(path, question).status_code == 302
    assert staff.post(path, question).status_code == 302
    record = RightsAction.objects.get(operation="clarify")
    assert unseal(record.encrypted_reason)["reason"] == question["reason"]
    content = client.get(receipt).content
    assert b"Clarify the action you request" in content
    assert question["reason"].encode() not in content
    assert b"rights-private@example.invalid" not in content
    assert (
        Client().get(receipt.replace(receipt.rstrip("/").rsplit("/", 1)[1], "a" * 43)).status_code
        == 404
    )
    assert b"Aclara qu" in client.get(receipt.replace("/en/", "/es/")).content
    case.refresh_from_db()
    assert case.version == 3 and case.scope_status == "unverified"
    assert (case.received_at, case.initial_due_at) == dates
    assert client.post(receipt, clarification(client, receipt)).status_code == 302
    case.refresh_from_db()
    assert case.version == 4 and case.status == "reviewing"
    assert b"Clarify the action you request" in client.get(receipt).content


def test_bad_question_and_stale_evidence_cannot_create_response(request):
    client, receipt, case, staff = prepared(request)
    inspect = f"/en/moderation/rights/{case.pk}/"
    staff.post(inspect, {"purpose": "Read request before asking clarification"})
    path, question = action(staff, case, "clarify")
    assert staff.post(path, {**question, "clarification_prompt": "invented"}).status_code == 400
    assert staff.post(path, question).status_code == 409
    client.post(receipt, clarification(client, receipt))
    path, question = action(staff, case, "clarify")
    question["clarification_prompt"] = "reference"
    assert staff.post(path, question).status_code == 409
    staff.post(inspect, {"purpose": "Read updated requester reference and clarification"})
    assert staff.post(path, question).status_code == 302
    assert staff.post(path, {**question, "clarification_prompt": "contact"}).status_code == 409
    assert RightsAction.objects.filter(operation="clarify").count() == 1


def test_mobile_requester_reads_question_and_replies_without_account(
    live_server, request, settings
):
    import shutil

    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    _, receipt, case, staff = prepared(request)
    staff.post(
        f"/en/moderation/rights/{case.pk}/", {"purpose": "Read request before asking clarification"}
    )
    path, question = action(staff, case, "clarify")
    assert staff.post(path, {**question, "clarification_prompt": "contact"}).status_code == 302
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + receipt)
            expect(page.get_by_role("heading", name="Questions from the reviewer")).to_be_visible()
            assert "does not verify identity" in page.content()
            page.locator("[name=text]").fill("I can provide my own synthetic contact channel")
            page.get_by_role("button", name="Submit clarification", exact=True).click()
            page.reload()
            expect(page.get_by_text("Recorded clarifications: 1", exact=True)).to_be_visible()
            assert question["reason"] not in page.content()
            assert "own synthetic contact" not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.version == 4 and case.scope_status == "unverified"


def test_question_and_requester_reply_cannot_both_use_same_version(request):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.core.exceptions import ValidationError
    from django.db import close_old_connections, connections

    from apps.core.models import User
    from apps.safety.models import RightsMessage
    from apps.safety.rights_actions import act

    client, receipt, case, staff = prepared(request)
    staff.post(
        f"/en/moderation/rights/{case.pk}/", {"purpose": "Read request before asking clarification"}
    )
    _, question = action(staff, case, "clarify")
    question["clarification_prompt"] = "scope"
    reply = clarification(client, receipt)
    actor_id = case.__class__.objects.get(pk=case.pk).assigned_to_id
    barrier = Barrier(2)

    def perform(operation):
        close_old_connections()
        try:
            actor = User.objects.get(pk=actor_id) if operation == "question" else None
            barrier.wait(timeout=10)
            if operation == "question":
                try:
                    act(actor, case.pk, **question)
                    return 302
                except ValidationError:
                    return 409
            return Client().post(receipt, reply).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(perform, ["question", "reply"]))
    assert sorted(outcomes) == [302, 409]
    case.refresh_from_db()
    assert case.version == 3
    assert (
        RightsAction.objects.filter(operation="clarify").count() + RightsMessage.objects.count()
        == 1
    )
