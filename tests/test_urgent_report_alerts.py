import json
import shutil
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pyotp
import pytest
from django.db import close_old_connections, connections, transaction
from django.test import Client
from playwright.sync_api import expect, sync_playwright
from test_report_inspection import case, reviewer
from test_reports import directory, payload, photo_environment  # noqa: F401

from apps.safety.models import Report, ReportAccess, UrgentReportAlert
from apps.safety.tasks import reconcile_urgent_report_alerts

pytestmark = pytest.mark.django_db(transaction=True)
PATH = "/en/moderation/reports/urgent-alerts/"


def test_intake_atomic_alert_replay_and_bounded_reconciliation(request):
    request.getfixturevalue("directory")
    client = Client()
    data = payload(client)
    response = client.post("/en/safety/report/", data)
    assert response.status_code == 302
    assert UrgentReportAlert.objects.count() == 1
    assert client.post("/en/safety/report/", data).url == response.url
    assert UrgentReportAlert.objects.count() == 1
    assert client.post("/en/safety/report/", payload(client, reason="other")).status_code == 302
    assert UrgentReportAlert.objects.count() == 1
    report = Report.objects.get(priority=0)
    UrgentReportAlert.objects.all().delete()
    assert reconcile_urgent_report_alerts() == {"reconciled": 1}
    assert reconcile_urgent_report_alerts() == {"reconciled": 0}
    UrgentReportAlert.objects.all().delete()
    with pytest.raises(RuntimeError), transaction.atomic():
        assert reconcile_urgent_report_alerts()["reconciled"] == 1
        raise RuntimeError("Synthetic transaction rollback")
    assert not UrgentReportAlert.objects.exists()
    assert Report.objects.filter(pk=report.pk).exists()


def test_private_acknowledgement_does_not_read_assign_or_resolve(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    assert Client().get(PATH).status_code == 302
    assert staff.post(PATH, {"report_id": "invalid"}).status_code == 400
    response = staff.get(PATH)
    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert response["X-Robots-Tag"] == "noindex, nofollow"
    assert b"private@example.invalid" not in response.content
    assert report.encrypted_payload.encode() not in response.content
    # Closed reports keep the pending operational alert until explicit acknowledgement.
    Report.objects.filter(pk=report.pk).update(status="dismissed")
    assert len(staff.get(PATH).context["page"]) == 1
    assert staff.post(PATH, {"report_id": report.pk}).status_code == 302
    alert = UrgentReportAlert.objects.get(report=report)
    first = (alert.acknowledged_by_id, alert.acknowledged_at)
    assert first[0] == user.pk and first[1]
    assert staff.post(PATH, {"report_id": report.pk}).status_code == 302
    alert.refresh_from_db()
    assert (alert.acknowledged_by_id, alert.acknowledged_at) == first
    report.refresh_from_db()
    assert report.version == 1 and report.assigned_to_id is None and report.status == "dismissed"
    assert not ReportAccess.objects.exists() and not report.actions.exists()
    assert len(staff.get(PATH).context["page"]) == 0
    Report.objects.filter(pk=report.pk).update(actor=user)
    assert staff.post(PATH, {"report_id": report.pk}).status_code == 403
    assert not staff.get(PATH).context["page"]
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    assert csrf.post(PATH, {"report_id": report.pk}).status_code == 403


def test_concurrent_acknowledgement_preserves_single_first_attention(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, _ = reviewer()
    barrier = Barrier(2)

    def acknowledge():
        close_old_connections()
        try:
            staff = Client()
            staff.force_login(user)
            session = staff.session
            session["mfa_version"] = user.mfa_version
            session.save()
            barrier.wait(timeout=10)
            return staff.post(PATH, {"report_id": report.pk}).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(acknowledge) for _ in range(2)]
        assert [f.result(timeout=30) for f in futures] == [302, 302]
    assert UrgentReportAlert.objects.count() == 1
    assert UrgentReportAlert.objects.get().acknowledged_by_id == user.pk
    report.refresh_from_db()
    assert report.version == 1 and not report.actions.exists()


def test_mobile_attention_persists_after_reload(live_server, request, settings, tmp_path):
    settings.DEBUG = True
    client = request.getfixturevalue("directory")
    report = case(client)
    reviewer()
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
            page.goto(live_server.url + "/en/moderation/reports/")
            page.get_by_role("link", name="Urgent report alerts", exact=True).click()
            assert "private@example.invalid" not in page.content()
            page.get_by_role("button", name="Acknowledge attention", exact=True).click()
            expect(page.get_by_text("No unacknowledged urgent alerts", exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_text("No unacknowledged urgent alerts", exact=True)).to_be_visible()
            page.locator("select[name=attention]").select_option("follow_up")
            page.get_by_role("button", name="Filter alerts", exact=True).click()
            expect(
                page.get_by_text(
                    "No case owner assigned: inspect the report to assign responsibility.",
                    exact=False,
                )
            ).to_be_visible()
            page.reload()
            expect(page.get_by_role("link", name="Inspect report", exact=True)).to_be_visible()
            assert "private@example.invalid" not in page.content()
            page.get_by_role("link", name="Inspect report", exact=True).click()
            expect(
                page.get_by_role("heading", name="Private report inspection", exact=True)
            ).to_be_visible()
            assert "private@example.invalid" not in page.content()
        finally:
            browser.close()
    assert UrgentReportAlert.objects.get(report=report).acknowledged_at
    assert not ReportAccess.objects.exists()


def test_reconciler_batch_limit_and_intake_rollback(request, monkeypatch):
    client = request.getfixturevalue("directory")
    report = case(client)
    UrgentReportAlert.objects.all().delete()
    import uuid

    Report.objects.bulk_create(
        [
            Report(
                submission_key=uuid.uuid4(),
                receipt_digest="0" * 64,
                payload_digest="0" * 64,
                encrypted_payload=report.encrypted_payload,
                mode="general",
                reason="minor",
                priority=0,
                receipt_expires_at=report.receipt_expires_at,
            )
            for _ in range(101)
        ]
    )
    assert reconcile_urgent_report_alerts() == {"reconciled": 100}
    assert reconcile_urgent_report_alerts() == {"reconciled": 2}
    assert reconcile_urgent_report_alerts() == {"reconciled": 0}
    data = payload(client)

    def fail(**kwargs):
        raise RuntimeError("Synthetic alert persistence failure")

    monkeypatch.setattr(UrgentReportAlert.objects, "create", fail)
    with pytest.raises(RuntimeError):
        client.post("/en/safety/report/", data)
    assert not Report.objects.filter(submission_key=data["key"]).exists()


def test_acknowledgement_rechecks_management_and_historical_conflict(request, monkeypatch):
    from apps.core.models import Person
    from apps.safety import urgent_alerts

    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    report = case(client, person)
    user, staff = reviewer()
    original = urgent_alerts.permitted
    changed = False

    def interleave(actor, candidate):
        nonlocal changed
        allowed = original(actor, candidate)
        if not changed:
            changed = True
            Person.objects.filter(pk=person.pk).update(
                agency=None, individual=user, assigned_editor=None
            )
        return allowed

    monkeypatch.setattr(urgent_alerts, "permitted", interleave)
    assert staff.post(PATH, {"report_id": report.pk}).status_code == 409
    assert UrgentReportAlert.objects.get(report=report).acknowledged_at is None
    assert not staff.get(PATH).context["page"]
    monkeypatch.setattr(urgent_alerts, "permitted", original)
    Person.objects.filter(pk=person.pk).update(individual=person.subject)
    Report.objects.filter(pk=report.pk).update(reported_subject=user)
    assert staff.post(PATH, {"report_id": report.pk}).status_code == 403
    assert not staff.get(PATH).context["page"]


@pytest.mark.parametrize("revoked", ["permission", "session", "mfa", "active"])
@pytest.mark.parametrize("replay", [False, True])
def test_acknowledgement_rechecks_revoked_authority(request, monkeypatch, revoked, replay):
    from apps.core.models import User
    from apps.safety import urgent_alerts

    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    if replay:
        assert staff.post(PATH, {"report_id": report.pk}).status_code == 302
    before = UrgentReportAlert.objects.get(report=report)
    original = urgent_alerts.permitted
    changed = False

    def revoke(actor, candidate):
        nonlocal changed
        result = original(actor, candidate)
        if not changed:
            changed = True
            if revoked == "permission":
                user.user_permissions.clear()
                user.groups.clear()
                User.objects.filter(pk=user.pk).update(is_superuser=False)
            elif revoked == "session":
                User.objects.filter(pk=user.pk).update(session_version=user.session_version + 1)
            elif revoked == "mfa":
                User.objects.filter(pk=user.pk).update(mfa_version=user.mfa_version + 1)
            else:
                User.objects.filter(pk=user.pk).update(is_active=False)
        return result

    monkeypatch.setattr(urgent_alerts, "permitted", revoke)
    assert staff.post(PATH, {"report_id": report.pk}).status_code == 403
    after = UrgentReportAlert.objects.get(report=report)
    assert (after.acknowledged_at, after.acknowledged_by_id) == (
        before.acknowledged_at,
        before.acknowledged_by_id,
    )
    report.refresh_from_db()
    assert report.version == 1 and not report.actions.exists()


@pytest.mark.parametrize("language", ["es", "en"])
def test_acknowledged_alert_remains_in_scoped_followup_until_terminal(request, language):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    path = f"/{language}/moderation/reports/urgent-alerts/"
    assert len(staff.get(path, {"attention": "follow_up"}).context["page"]) == 0
    assert staff.post(path, {"report_id": report.pk}).status_code == 302
    assert len(staff.get(path).context["page"]) == 0
    for state in ["received", "reviewing", "restricted", "upheld", "unknown_fixture"]:
        Report.objects.filter(pk=report.pk).update(status=state)
        response = staff.get(path, {"attention": "follow_up"})
        assert response.status_code == 200 and len(response.context["page"]) == 1
        assert response["Cache-Control"] == "private, no-store"
        assert b"private@example.invalid" not in response.content
        assert b'name="report_id"' not in response.content
    for state in ["dismissed", "lifted"]:
        Report.objects.filter(pk=report.pk).update(status=state)
        assert len(staff.get(path, {"attention": "follow_up"}).context["page"]) == 0
    Report.objects.filter(pk=report.pk).update(status="reviewing", assigned_to=user)
    assert user.username.encode() in staff.get(path, {"attention": "follow_up"}).content
    Report.objects.filter(pk=report.pk).update(actor=user)
    assert len(staff.get(path, {"attention": "follow_up"}).context["page"]) == 0
    assert staff.get(path, {"attention": "invalid"}).status_code == 400
    report.refresh_from_db()
    assert report.version == 1 and not report.actions.exists() and not ReportAccess.objects.exists()
