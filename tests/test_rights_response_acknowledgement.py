import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_responses import ready, values

from apps.safety.models import RightsResponseAcknowledgement
from apps.safety.rights_responses import issue

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request, settings, monkeypatch):
    case, user, staff, client, receipt, person = ready(request, settings, monkeypatch)
    response = issue(user, case.pk, **values(case))
    secret = receipt.rstrip("/").split("/")[-1]
    path = reverse(
        "rights_response_acknowledge",
        kwargs={"case_id": case.pk, "secret": secret, "response_id": response.pk},
    )
    return case, client, receipt, path, response


def test_explicit_receipt_is_private_idempotent_and_changes_no_authorization(
    request, settings, monkeypatch
):
    case, client, receipt, path, response = prepared(request, settings, monkeypatch)
    case.refresh_from_db()
    original = (
        case.version,
        case.response_version,
        case.status,
        case.scope_status,
        case.received_at,
        case.initial_due_at,
    )
    assert client.get(receipt).status_code == 200
    assert not RightsResponseAcknowledgement.objects.exists()
    assert client.get(path).status_code == 405
    assert client.post(path, {}).status_code == 400
    assert not RightsResponseAcknowledgement.objects.exists()
    assert client.post(path, {"received": "yes"}).status_code == 302
    ack = RightsResponseAcknowledgement.objects.get(response=response)
    initial = (ack.pk, ack.created_at, ack.channel_digest)
    assert ack.channel_digest == case.receipt_digest
    assert client.post(path, {"received": "yes"}).status_code == 302
    ack.refresh_from_db()
    assert (ack.pk, ack.created_at, ack.channel_digest) == initial
    body = client.get(receipt)
    assert (
        body["Cache-Control"] == "private, no-store" and body["X-Robots-Tag"] == "noindex, nofollow"
    )
    assert b"Receipt recorded" in body.content
    assert b"Record response receipt" not in body.content
    case.refresh_from_db()
    assert (
        case.version,
        case.response_version,
        case.status,
        case.scope_status,
        case.received_at,
        case.initial_due_at,
    ) == original
    assert response.rightsnotice.status == "queued"


def test_invalid_or_expired_receipt_and_foreign_response_cannot_acknowledge(
    request, settings, monkeypatch
):
    case, client, receipt, path, response = prepared(request, settings, monkeypatch)
    secret = receipt.rstrip("/").split("/")[-1]
    assert client.post(path.replace(secret, "x" * 43), {"received": "yes"}).status_code == 404
    assert (
        client.post(
            path.replace(f"/response/{response.pk}/", f"/response/{response.pk + 1}/"),
            {"received": "yes"},
        ).status_code
        == 404
    )
    assert Client(enforce_csrf_checks=True).post(path, {"received": "yes"}).status_code == 403
    case.receipt_expires_at = timezone.now() - timedelta(seconds=1)
    case.save(update_fields=["receipt_expires_at"])
    assert client.post(path, {"received": "yes"}).status_code == 404
    assert not RightsResponseAcknowledgement.objects.exists()


def test_two_postgresql_connections_keep_one_receipt_record(request, settings, monkeypatch):
    _, _, _, path, _ = prepared(request, settings, monkeypatch)
    barrier = Barrier(2)

    def submit():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return Client().post(path, {"received": "yes"}).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(submit) for _ in range(2)]
        assert [job.result(timeout=30) for job in jobs] == [302, 302]
    assert RightsResponseAcknowledgement.objects.count() == 1


def test_mobile_receipt_confirmation_persists_without_account(
    live_server, request, settings, monkeypatch
):
    settings.DEBUG = True
    _, _, receipt, _, _ = prepared(request, settings, monkeypatch)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + receipt)
            page.locator("[name=received]").check()
            page.get_by_role("button", name="Record response receipt", exact=True).click()
            expect(page.get_by_text("Receipt recorded", exact=False)).to_be_visible()
            page.reload()
            expect(page.get_by_text("Receipt recorded", exact=False)).to_be_visible()
            assert (
                page.get_by_role("button", name="Record response receipt", exact=True).count() == 0
            )
        finally:
            browser.close()
    assert RightsResponseAcknowledgement.objects.count() == 1
