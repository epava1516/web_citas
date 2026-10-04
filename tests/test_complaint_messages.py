import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from test_complaint_assignment import prepared
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.complaint_actions import act
from apps.safety.complaint_messages import append, complete_read
from apps.safety.crypto import unseal
from apps.safety.models import ComplaintMessage

pytestmark = pytest.mark.django_db(transaction=True)
REASON = "Private reviewed reason for seeking more precise reference details"
TEXT = "Synthetic private clarification about an unresolved decision reference"


def ready(request):
    case, user, staff, receipt = prepared(request)
    act(user, case.pk, uuid.uuid4(), case.version, "claim", REASON)
    case.refresh_from_db()
    assert (
        staff.post(f"/en/moderation/complaints/{case.pk}/", {"purpose": REASON}).status_code == 200
    )
    return case, user, staff, receipt


def test_unknown_reference_question_and_private_reply_preserve_case_and_dates(request):
    case, user, staff, receipt = ready(request)
    dates = case.created_at, case.receipt_expires_at
    key = uuid.uuid4()
    version = case.version
    act(user, case.pk, key, version, "clarify", REASON, clarification_prompt="reference_unknown")
    act(user, case.pk, key, version, "clarify", REASON, clarification_prompt="reference_unknown")
    case.refresh_from_db()
    client = Client()
    page = client.get(receipt)
    assert (
        b"We could not identify the decision" in page.content
        and REASON.encode() not in page.content
    )
    data = dict(page.context["message_form"].initial, text=TEXT)
    path = receipt + "message/"
    assert client.post(path, data).status_code == 302
    assert client.post(path, data).status_code == 302
    assert client.post(path, data | {"text": TEXT + " Changed"}).status_code == 409
    case.refresh_from_db()
    assert (case.created_at, case.receipt_expires_at) == dates
    assert case.status == "reviewing" and not case.decision_id and not case.listing_decision_id
    row = ComplaintMessage.objects.get()
    assert TEXT not in row.encrypted_payload and unseal(row.encrypted_payload)["text"] == TEXT
    assert TEXT.encode() not in client.get(receipt).content
    assert not complete_read(user, case)
    review = f"/en/moderation/complaints/{case.pk}/"
    result = staff.post(review, {"purpose": REASON})
    assert result.status_code == 200 and TEXT.encode() in result.content
    assert result["Cache-Control"] == "private, no-store"
    assert TEXT.encode() not in staff.get(review).content
    assert complete_read(user, case)
    with pytest.raises(ValidationError):
        act(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "clarify",
            REASON,
            clarification_prompt="reference_stale",
        )
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403
    assert client.get(path).status_code == 405
    secret = receipt.rstrip("/").split("/")[-1]
    assert client.post(path.replace(secret, "x" * 43), data).status_code == 404


def test_complete_message_history_requires_all_audited_pages(request):
    case, user, staff, receipt = ready(request)
    secret = receipt.rstrip("/").split("/")[-1]
    for index in range(51):
        case = append(case.pk, secret, uuid.uuid4(), case.version, TEXT + f" item {index}")
    review = f"/en/moderation/complaints/{case.pk}/"
    first = staff.post(review, {"purpose": REASON})
    assert len(first.context["clarification_messages"]) == 50
    assert not complete_read(user, case)
    with pytest.raises(ValidationError):
        act(
            user,
            case.pk,
            uuid.uuid4(),
            case.version,
            "clarify",
            REASON,
            clarification_prompt="reference_unknown",
        )
    second = staff.post(
        review, {"purpose": REASON, "message_before": first.context["next_message_cursor"]}
    )
    assert len(second.context["clarification_messages"]) == 1 and complete_read(user, case)
    assert act(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "clarify",
        REASON,
        clarification_prompt="reference_unknown",
    )


def test_concurrent_private_reply_replay_has_one_message(request):
    case, _, _, receipt = ready(request)
    secret = receipt.rstrip("/").split("/")[-1]
    version = case.version
    key = uuid.uuid4()
    barrier = Barrier(2)

    def run():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return append(case.pk, secret, key, version, TEXT).pk
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run) for _ in range(2)]
        assert [job.result(timeout=30) for job in futures] == [case.pk, case.pk]
    assert ComplaintMessage.objects.count() == 1
    case.refresh_from_db()
    assert case.version == version + 1


def test_stale_linked_reference_can_be_clarified_without_changing_source(request):
    from test_complaint_resolutions import inspection, listing_case

    complaint, person, decision, user, staff, receipt = listing_case(request)
    revision = decision.revision
    # Controlled source-version interleaving; no claim that this fixture is a new moderation decision.
    revision.edit_version += 1
    revision.save(update_fields=["edit_version"])
    assert inspection(staff, complaint).status_code == 200
    complaint.refresh_from_db()
    status = revision.status
    act(
        user,
        complaint.pk,
        uuid.uuid4(),
        complaint.version,
        "clarify",
        REASON,
        clarification_prompt="reference_stale",
    )
    assert b"The reference relates to an earlier version" in Client().get(receipt).content
    revision.refresh_from_db()
    assert revision.status == status
    complaint.refresh_from_db()
    assert complaint.listing_decision_id == decision.pk and complaint.status == "reviewing"
    with pytest.raises(ValidationError):
        act(
            user,
            complaint.pk,
            uuid.uuid4(),
            complaint.version,
            "clarify",
            REASON,
            clarification_prompt="reference_unknown",
        )


def test_mobile_question_reply_and_audited_inspection(live_server, request, settings, tmp_path):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, receipt = ready(request)
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            context = browser.new_context(viewport={"width": 390, "height": 844})
            page = context.new_page()
            page.goto(live_server.url + "/en/account/login/")
            page.locator("[name=email]").fill(account["email"])
            page.locator("[name=password]").fill(credentials["password"])
            page.locator("button[type=submit]").click()
            page.locator("[name=code]").fill(pyotp.TOTP(account["totp_secret"]).now())
            page.locator("button[type=submit]").click()
            expect(page.get_by_role("heading", name="Your account", exact=True)).to_be_visible()
            page.goto(live_server.url + f"/en/moderation/complaints/{case.pk}/action/")
            page.locator("[name=operation]").select_option("clarify")
            page.locator("[name=clarification_prompt]").select_option("reference_unknown")
            page.locator("[name=reason]").fill(REASON)
            page.locator("button[type=submit]").click()
            expect(
                page.get_by_role("heading", name="Private decision review intake", exact=True)
            ).to_be_visible()
            public = browser.new_context(viewport={"width": 390, "height": 844}).new_page()
            public.goto(live_server.url + receipt)
            expect(
                public.get_by_text("We could not identify the decision.", exact=False)
            ).to_be_visible()
            public.locator("[name=text]").fill(TEXT)
            public.get_by_role("button", name="Submit reference clarification", exact=True).click()
            expect(public.get_by_text("Recorded clarifications: 1.", exact=False)).to_be_visible()
            assert TEXT not in public.content()
            page.goto(live_server.url + f"/en/moderation/complaints/{case.pk}/")
            page.locator("[name=purpose]").fill(REASON)
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(page.get_by_text(TEXT, exact=False)).to_be_visible()
            assert TEXT not in " ".join(page.locator("[role=status]").all_text_contents())
            page.goto(live_server.url + f"/en/moderation/complaints/{case.pk}/")
            assert TEXT not in page.content()
        finally:
            browser.close()
    case.refresh_from_db()
    assert case.status == "reviewing" and ComplaintMessage.objects.count() == 1
