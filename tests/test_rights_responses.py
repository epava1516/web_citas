import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connections
from django.test import Client
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_exports import make_copy, url
from test_rights_verification import read

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import RightsNotice, RightsResponse, SimulatedRightsNoticeDelivery
from apps.safety.notice_delivery import process_outbox
from apps.safety.rights_actions import act
from apps.safety.rights_responses import issue

pytestmark = pytest.mark.django_db(transaction=True)
TEXT = "Se ha revisado el alcance de la solicitud y las actuaciones indicadas. La información aquí facilitada no incluye datos de terceros."


def ready(request, settings, monkeypatch, kind="access"):
    import test_rights_exports

    original = test_rights_exports.data
    with monkeypatch.context() as patch:
        patch.setattr(
            test_rights_exports,
            "data",
            lambda client, **changes: original(client, **(changes | {"kind": kind})),
        )
        result = test_rights_exports.prepared(request, settings)
    case, user, staff, client, receipt, person = result
    user.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    user = User.objects.get(pk=user.pk)
    return case, user, staff, client, receipt, person


def values(case, **changes):
    return {
        "key": uuid.uuid4(),
        "version": case.version,
        "response_version": case.response_version,
        "kind": "progress",
        "reason": "Private operational reason for the scoped response",
        "response": TEXT,
        "redaction_confirmed": True,
    } | changes


def test_progress_keeps_existing_copy_and_evidence_dates_private(request, settings, monkeypatch):
    case, user, staff, client, receipt, _ = ready(request, settings, monkeypatch)
    export = make_copy(case, user)
    case.refresh_from_db()
    read(staff, case)
    original = case.version, case.received_at, case.initial_due_at
    data = values(case)
    path = f"/en/moderation/rights/{case.pk}/response/"
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    case.refresh_from_db()
    assert (
        case.version,
        case.received_at,
        case.initial_due_at,
    ) == original and case.status == "reviewing"
    assert case.response_version == 1 and RightsResponse.objects.count() == 1
    assert client.post(url(receipt, export), {"key": uuid.uuid4()}).status_code == 200
    body = client.get(receipt).content
    assert TEXT.encode() in body and data["reason"].encode() not in body
    assert b"AEPD" in body and b"judicial remedy" in body
    record = RightsResponse.objects.get()
    assert TEXT not in record.encrypted_response
    notice = RightsNotice.objects.get()
    payload = unseal(notice.encrypted_payload)
    assert TEXT not in payload["body"] and data["reason"] not in payload["body"]
    settings.SAFETY_NOTICE_BACKEND = "simulator"
    assert process_outbox()["simulated"] == 1
    assert SimulatedRightsNoticeDelivery.objects.count() == 1
    assert process_outbox()["processed"] == 0
    assert b"Simulated notice; no real delivery" in client.get(receipt).content
    assert staff.post(path, values(case, response_version=0)).status_code == 409
    assert Client(enforce_csrf_checks=True).post(path, data).status_code == 403


def test_representation_close_requires_actual_current_withdrawal_and_hides_source_notes(
    request, settings, monkeypatch
):
    case, user, staff, client, receipt, person = ready(
        request, settings, monkeypatch, "representation"
    )
    with pytest.raises(ValidationError):
        issue(user, case.pk, **values(case, kind="representation_complete"))
    act(
        user,
        case.pk,
        uuid.uuid4(),
        case.version,
        "withdraw",
        "Withdraw scoped representation after synthetic independent proof",
    )
    case.refresh_from_db()
    read(staff, case)
    data = values(case, kind="representation_complete")
    from apps.safety.models import RightsWithdrawal

    proof = RightsWithdrawal.objects.get(action__request=case).proof
    procedure = proof.procedure
    proof.procedure = "untrusted-procedure"
    proof.save(update_fields=["procedure"])
    with pytest.raises(ValidationError):
        issue(user, case.pk, **data)
    proof.procedure = procedure
    proof.save(update_fields=["procedure"])
    settings.PRODUCTION = True
    with pytest.raises(ValidationError):
        issue(user, case.pk, **data)
    settings.PRODUCTION = False
    record = issue(user, case.pk, **data)
    assert record.withdrawal_id and unseal(record.encrypted_response)["simulation"]
    assert issue(user, case.pk, **data).pk == record.pk
    case.refresh_from_db()
    assert case.status == "resolved" and case.response_version == 1
    person.refresh_from_db()
    assert person.listing.status == "withdrawn"
    assert b"Development simulation; identity not verified" in client.get(receipt).content
    assert (
        client.post(
            receipt,
            {
                "key": uuid.uuid4(),
                "version": case.version,
                "text": "A clarification should not reopen a resolved request.",
            },
        ).status_code
        == 409
    )
    assert RightsResponse.objects.count() == RightsNotice.objects.count() == 1


def test_two_connections_and_permissions_cannot_duplicate_or_inject_identity(
    request, settings, monkeypatch
):
    case, user, staff, _, _, _ = ready(request, settings, monkeypatch)
    path = f"/en/moderation/rights/{case.pk}/response/"
    assert (
        staff.post(
            path,
            values(case, response="An external person has this contact private@example.invalid"),
        ).status_code
        == 409
    )
    user.user_permissions.remove(Permission.objects.get(codename="respond_rights_request"))
    assert staff.get(path).status_code == 403
    user.user_permissions.add(Permission.objects.get(codename="respond_rights_request"))
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            actor = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                issue(actor, case.pk, **values(case))
                return "responded"
            except ValidationError:
                return "conflict"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(worker) for _ in range(2)]
        assert sorted(f.result(timeout=20) for f in futures) == ["conflict", "responded"]
    assert RightsResponse.objects.count() == 1


def test_new_response_requires_audited_outgoing_history_and_rights_notice_recovery(
    request, settings, monkeypatch
):
    from apps.safety.models import RightsAccess
    from apps.safety.notice_operations import requeue

    case, user, staff, client, receipt, _ = ready(request, settings, monkeypatch)
    issue(user, case.pk, **values(case))
    case.refresh_from_db()
    with pytest.raises(ValidationError):
        issue(user, case.pk, **values(case))
    assert not staff.get(f"/en/moderation/rights/{case.pk}/").context["outgoing_responses"]
    read(staff, case)
    assert RightsAccess.objects.filter(request=case, response_version=1).exists()
    issue(user, case.pk, **values(case))
    notice = RightsNotice.objects.first()
    RightsNotice.objects.filter(pk=notice.pk).update(status="failed", attempts=5)
    user.user_permissions.add(Permission.objects.get(codename="manage_notice_delivery"))
    user = User.objects.get(pk=user.pk)
    requeue(
        user,
        "rights",
        notice.pk,
        uuid.uuid4(),
        0,
        "Repair of synthetic notice failure reviewed before recovery",
    )
    notice.refresh_from_db()
    assert notice.status == "queued" and notice.recovery_version == 1
    assert staff.get("/en/moderation/notices/?kind=rights").context["items"]
    assert client.get(receipt + "?response_before=bad").status_code == 400


def test_mobile_response_history_and_receipt_without_account(
    live_server, request, settings, monkeypatch, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    case, _, _, _, receipt, _ = ready(request, settings, monkeypatch)
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
            page.goto(live_server.url + f"/en/moderation/rights/{case.pk}/")
            page.locator("[name=purpose]").fill(
                "Read source and outgoing response history before reply"
            )
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            page.get_by_role("link", name="Issue private response", exact=True).click()
            page.locator("[name=kind]").select_option("progress")
            page.locator("[name=reason]").fill("Internal synthetic reason for this progress reply")
            page.locator("[name=response]").fill(TEXT)
            page.locator("[name=redaction_confirmed]").check()
            page.get_by_role("button", name="Record motivated response", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private rights inspection", exact=True)
            ).to_be_visible()
            anonymous = browser.new_page(viewport={"width": 390, "height": 844})
            anonymous.goto(live_server.url + receipt)
            expect(
                anonymous.get_by_role("heading", name="Private response", exact=True)
            ).to_be_visible()
            expect(anonymous.get_by_text(TEXT, exact=True)).to_be_visible()
            assert "Internal synthetic reason" not in anonymous.content()
            anonymous.reload()
            expect(anonymous.get_by_text(TEXT, exact=True)).to_be_visible()
        finally:
            browser.close()


def test_all_outgoing_pages_are_required_and_receipt_has_complete_history(
    request, settings, monkeypatch
):
    from apps.safety.crypto import seal

    case, user, staff, client, receipt, _ = ready(request, settings, monkeypatch)
    # Synthetic history to exercise pagination, not 52 acknowledged communications.
    RightsResponse.objects.bulk_create(
        [
            RightsResponse(
                key=uuid.uuid4(),
                request=case,
                actor=user,
                case_version=case.version,
                response_version=index + 1,
                kind="progress",
                payload_digest="0" * 64,
                encrypted_reason=seal({"reason": "Synthetic private history fixture"}),
                encrypted_response=seal({"text": TEXT, "simulation": False}),
            )
            for index in range(52)
        ]
    )
    case.response_version = 52
    case.save(update_fields=["response_version"])
    first = staff.post(
        f"/en/moderation/rights/{case.pk}/",
        {"purpose": "Read latest outgoing responses before another reply"},
    )
    assert len(first.context["outgoing_responses"]) == 50
    cursor = first.context["outgoing_cursor"]
    assert cursor
    with pytest.raises(ValidationError):
        issue(user, case.pk, **values(case))
    second = staff.post(
        f"/en/moderation/rights/{case.pk}/",
        {
            "purpose": "Read all earlier outgoing responses before another reply",
            "response_before": cursor,
        },
    )
    assert len(second.context["outgoing_responses"]) == 2 and not second.context["outgoing_cursor"]
    own = client.get(receipt)
    assert len(own.context["responses"]) == 50
    old = client.get(receipt + f"?response_before={own.context['response_cursor']}")
    assert len(old.context["responses"]) == 2 and not old.context["response_cursor"]
    assert b"Synthetic private history fixture" not in own.content
    issue(user, case.pk, **values(case))
    assert RightsResponse.objects.count() == 53
