from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from test_report_decisions import action
from test_report_inspection import reviewer
from test_reports import directory, payload, photo_environment  # noqa: F401

from apps.safety.crypto import unseal
from apps.safety.models import (
    Report,
    ReportAction,
    ReportNotice,
    Restriction,
    SimulatedNoticeDelivery,
)
from apps.safety.notices import simulate_delivery

pytestmark = pytest.mark.django_db(transaction=True)


def submitted(request, email="synthetic-recipient@example.invalid"):
    client = request.getfixturevalue("directory")
    data = payload(
        client,
        email=email,
        explanation="Confidential synthetic allegation must never be in notification email.",
    )
    response = client.post("/en/safety/report/", data)
    assert response.status_code == 302
    return client, data, response.url, Report.objects.get(submission_key=data["key"])


def test_ack_is_atomic_encrypted_minimized_and_not_duplicated(request):
    client, data, receipt, report = submitted(request)
    assert client.post("/en/safety/report/", data).status_code == 302
    notice = ReportNotice.objects.get()
    assert notice.report_id == report.pk and notice.kind == "ack" and notice.status == "queued"
    assert data["email"] not in notice.encrypted_payload
    message = unseal(notice.encrypted_payload)
    assert message["recipient"] == data["email"]
    assert data["explanation"] not in message["body"]
    assert data["receipt_secret"] not in message["body"]
    response = client.get(receipt)
    assert b"Queued; delivery not confirmed" in response.content
    assert data["email"].encode() not in response.content
    assert not SimulatedNoticeDelivery.objects.exists()


def test_no_contact_creates_no_notice_and_outcome_does_not_include_internal_reason(request):
    client, _, _, report = submitted(request, email="")
    assert not ReportNotice.objects.exists()
    _, staff = reviewer()
    path, data = action(staff, report, "claim")
    staff.post(path, data)
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Read private evidence before deciding case"},
    )
    path, data = action(staff, report, "dismiss")
    assert staff.post(path, data).status_code == 302
    assert not ReportNotice.objects.exists()
    contact = payload(client, email="other-synthetic@example.invalid")
    assert client.post("/en/safety/report/", contact).status_code == 302
    other = Report.objects.get(submission_key=contact["key"])
    path, data = action(staff, other, "claim")
    staff.post(path, data)
    staff.post(
        f"/en/moderation/reports/{other.pk}/",
        {"purpose": "Read supporting evidence for the other report"},
    )
    path, data = action(staff, other, "dismiss")
    data["reason"] = "Confidential internal reason not suitable for an unverified email"
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    notice = ReportNotice.objects.get(kind="outcome")
    assert data["reason"] not in unseal(notice.encrypted_payload)["body"]
    assert ReportNotice.objects.count() == 2


def test_notice_failure_rolls_back_case_decision(request, monkeypatch):
    _, _, _, report = submitted(request)
    _, staff = reviewer()
    path, data = action(staff, report, "claim")
    staff.post(path, data)
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect evidence before transactional decision"},
    )
    path, data = action(staff, report, "dismiss")

    def failure(*args):
        raise RuntimeError("Synthetic outbox failure")

    monkeypatch.setattr("apps.safety.decisions.enqueue_outcome", failure)
    with pytest.raises(RuntimeError, match="Synthetic outbox failure"):
        staff.post(path, data)
    report.refresh_from_db()
    assert report.status == "reviewing" and report.version == 2
    assert ReportAction.objects.count() == 1
    assert ReportNotice.objects.count() == 1 and not Restriction.objects.exists()


def test_simulator_is_explicit_disabled_in_production_and_concurrent_once(request, settings):
    client, _, receipt, _ = submitted(request)
    notice = ReportNotice.objects.get()
    settings.SAFETY_NOTICE_BACKEND = "disabled"
    assert not simulate_delivery(notice.pk)
    settings.SAFETY_NOTICE_BACKEND = "simulator"
    settings.PRODUCTION = True
    assert not simulate_delivery(notice.pk)
    assert not SimulatedNoticeDelivery.objects.exists()
    settings.PRODUCTION = False
    barrier = Barrier(2)

    def deliver(_):
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            return simulate_delivery(notice.pk)
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(deliver, range(2))) == [False, True]
    assert SimulatedNoticeDelivery.objects.count() == 1
    notice.refresh_from_db()
    assert notice.status == "simulated" and notice.simulated_at
    assert b"Development simulation; no email was sent" in client.get(receipt).content
