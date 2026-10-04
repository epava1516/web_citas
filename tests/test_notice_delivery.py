import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connections, transaction
from django.test import Client
from django.utils import timezone
from playwright.sync_api import expect, sync_playwright
from test_complaint_resolutions import inspection, listing_case, resolution
from test_report_decisions import action as report_action
from test_report_inspection import case as report_case
from test_report_inspection import reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety import notice_delivery
from apps.safety.models import (
    ComplaintNotice,
    ReportNotice,
    SimulatedComplaintNoticeDelivery,
    SimulatedNoticeDelivery,
)
from apps.safety.notice_delivery import process_outbox
from apps.safety.tasks import deliver_safety_notices

pytestmark = pytest.mark.django_db(transaction=True)


def queued(request, settings):
    settings.SAFETY_NOTICE_BACKEND = "simulator"
    complaint, _, _, _, staff, receipt = listing_case(request)
    inspection(staff, complaint)
    path, data = resolution(staff, complaint)
    assert staff.post(path, data).status_code == 302
    return ComplaintNotice.objects.get(), receipt


def test_due_outbox_exactly_once_private_receipt_and_production_disabled(request, settings):
    notice, receipt = queued(request, settings)
    settings.PRODUCTION = True
    assert process_outbox()["disabled"]
    notice.refresh_from_db()
    assert notice.status == "queued" and notice.attempts == 0
    settings.PRODUCTION = False
    result = deliver_safety_notices.run()
    assert result["simulated"] == 1 and result["processed"] == 1
    assert process_outbox()["processed"] == 0
    notice.refresh_from_db()
    assert notice.attempts == 1 and notice.simulated_at
    assert SimulatedComplaintNoticeDelivery.objects.count() == 1
    body = Client().get(receipt).content
    assert b"Simulated notice; no real delivery" in body
    assert b"own-channel@example.invalid" not in body


def test_retry_backoff_dead_state_and_no_exception_details_persisted(
    request, settings, monkeypatch, caplog
):
    notice, receipt = queued(request, settings)

    def fail(item):
        SimulatedComplaintNoticeDelivery.objects.create(notice=item)
        raise RuntimeError("private-recipient@example.invalid SECRET BODY")

    monkeypatch.setattr(notice_delivery, "simulated_adapter", fail)
    for attempt in range(1, 6):
        before = timezone.now()
        result = process_outbox()
        notice.refresh_from_db()
        assert notice.attempts == attempt and notice.error_code == "adapter_failure"
        assert not SimulatedComplaintNoticeDelivery.objects.exists()
        if attempt < 5:
            assert result["retry"] == 1 and notice.next_attempt_at >= before + timedelta(
                seconds=60 * 2 ** (attempt - 1)
            )
            assert process_outbox()["processed"] == 0
            ComplaintNotice.objects.filter(pk=notice.pk).update(
                next_attempt_at=timezone.now() - timedelta(seconds=1)
            )
        else:
            assert result["failed"] == 1 and notice.next_attempt_at is None
    assert process_outbox()["processed"] == 0
    assert "SECRET BODY" not in caplog.text
    assert b"Notification attempt failed" in Client().get(receipt).content


def test_two_workers_claim_one_notice_without_duplicate_simulation(request, settings):
    queued(request, settings)
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return process_outbox()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs = [executor.submit(worker) for _ in range(2)]
        assert sum(job.result()["simulated"] for job in jobs) == 1
    assert SimulatedComplaintNoticeDelivery.objects.count() == 1
    assert ComplaintNotice.objects.get().attempts == 1


def test_locked_notice_is_skipped_then_recovered_and_backend_disabled_is_inert(request, settings):
    notice, _ = queued(request, settings)
    with transaction.atomic():
        ComplaintNotice.objects.select_for_update().get(pk=notice.pk)
        with ThreadPoolExecutor(max_workers=1) as executor:

            def worker():
                close_old_connections()
                try:
                    return process_outbox()
                finally:
                    connections.close_all()

            assert executor.submit(worker).result(timeout=10)["processed"] == 0
    settings.SAFETY_NOTICE_BACKEND = "disabled"
    assert process_outbox()["disabled"]
    notice.refresh_from_db()
    assert notice.attempts == 0
    settings.SAFETY_NOTICE_BACKEND = "simulator"
    assert process_outbox()["simulated"] == 1


def test_report_and_complaint_outboxes_share_bounded_processing_without_duplicates(
    request, settings
):
    queued(request, settings)
    report = report_case(request.getfixturevalue("directory"))
    _, staff = reviewer()
    path, data = report_action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect independent generic report before dismissal"},
    )
    path, data = report_action(staff, report, "dismiss")
    assert staff.post(path, data).status_code == 302
    assert ReportNotice.objects.count() == 2
    first = process_outbox(limit=2)
    assert first["processed"] == 2 and first["simulated"] == 2
    assert SimulatedComplaintNoticeDelivery.objects.count() == 1
    assert SimulatedNoticeDelivery.objects.count() == 1
    assert process_outbox()["simulated"] == 1
    assert process_outbox()["processed"] == 0
    assert list(ReportNotice.objects.values_list("attempts", flat=True)) == [1, 1]


def test_mobile_receipt_status_changes_only_to_explicit_simulation(live_server, request, settings):
    settings.DEBUG = True
    _, receipt = queued(request, settings)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=shutil.which("chromium-browser"), args=["--no-sandbox"]
        )
        try:
            page = browser.new_page(viewport={"width": 390, "height": 844})
            page.goto(live_server.url + receipt)
            expect(
                page.get_by_text(
                    "Notification delivery not confirmed; your response is available here.",
                    exact=True,
                )
            ).to_be_visible()

            def worker():
                close_old_connections()
                try:
                    return deliver_safety_notices.run()
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=1) as executor:
                assert executor.submit(worker).result(timeout=10)["simulated"] == 1
            page.reload()
            expect(
                page.get_by_text("Simulated notice; no real delivery.", exact=True)
            ).to_be_visible()
            assert "own-channel@example.invalid" not in page.content()
        finally:
            browser.close()
