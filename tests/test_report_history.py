import uuid

import pytest
from django.contrib.auth.models import Permission
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, payload, photo_environment  # noqa: F401

from apps.safety.decisions import act
from apps.safety.models import Report, ReportAccess

pytestmark = pytest.mark.django_db(transaction=True)


def test_history_is_only_revealed_by_audited_post_and_remains_escaped(request):
    client = request.getfixturevalue("directory")
    data = payload(client)
    receipt_url = client.post("/en/safety/report/", data).url
    report = Report.objects.get(submission_key=data["key"])
    moderator, staff = reviewer()
    path, decision = action(staff, report, "claim")
    reason = "<script>window.historyLeak=true</script> Synthetic private justification"
    decision["reason"] = reason
    assert staff.post(path, decision).status_code == 302
    path = f"/en/moderation/reports/{report.pk}/"
    response = staff.get(path)
    assert response.context["history"] == []
    assert b"historyLeak" not in response.content
    response = staff.post(path, {"purpose": "Inspect the attributed private action history"})
    assert response.status_code == 200
    assert response.context["history"][0]["actor_id"] == moderator.pk
    assert response.context["history"][0]["reason"] == reason
    assert b"&lt;script&gt;" in response.content
    assert b"<script>window.historyLeak" not in response.content
    assert ReportAccess.objects.count() == 1
    assert b"historyLeak" not in staff.get(path).content
    assert b"historyLeak" not in client.get(receipt_url).content
    assert b"Case history" not in client.get(receipt_url).content


def test_keyset_history_has_no_omission_or_other_case_data(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    moderator, staff = reviewer()
    moderator.user_permissions.add(Permission.objects.get(codename="manage_report_assignment"))
    for index in range(52):
        act(
            moderator,
            report.pk,
            uuid.uuid4(),
            index + 1,
            "claim" if index % 2 == 0 else "unassign",
            f"Synthetic historical assignment action number {index}",
        )
    other = case(client)
    act(
        moderator,
        other.pk,
        uuid.uuid4(),
        1,
        "claim",
        "Different case private reason must stay excluded",
    )
    path = f"/en/moderation/reports/{report.pk}/"
    first = staff.post(path, {"purpose": "Inspect most recent fifty actions in this case"})
    assert first.status_code == 200 and len(first.context["history"]) == 50
    cursor = first.context["next_action_cursor"]
    assert cursor and b"Different case" not in first.content
    second = staff.post(
        path, {"purpose": "Inspect remaining earlier actions in this case", "action_before": cursor}
    )
    assert second.status_code == 200 and len(second.context["history"]) == 2
    assert second.context["next_action_cursor"] is None
    versions = [
        item["expected_version"]
        for response in [first, second]
        for item in response.context["history"]
    ]
    assert versions == list(range(52, 0, -1))
    assert b"Different case" not in second.content
    assert ReportAccess.objects.filter(report=report).count() == 2
    assert (
        staff.post(
            path, {"purpose": "Inspect with invalid cursor for this case", "action_before": -1}
        ).status_code
        == 400
    )
    assert ReportAccess.objects.filter(report=report).count() == 2


def test_mobile_history_older_page_is_audited_and_get_hides_it(
    live_server, request, settings, tmp_path
):
    import json
    import shutil

    import pyotp
    from playwright.sync_api import expect, sync_playwright

    settings.DEBUG = True
    client = request.getfixturevalue("directory")
    report = case(client)
    moderator, _ = reviewer()
    moderator.user_permissions.add(Permission.objects.get(codename="manage_report_assignment"))
    for index in range(52):
        act(
            moderator,
            report.pk,
            uuid.uuid4(),
            index + 1,
            "claim" if index % 2 == 0 else "unassign",
            f"Synthetic mobile history entry {index} with justification",
        )
    credentials = json.loads((tmp_path / "credentials.json").read_text())
    account = credentials["accounts"]["moderator"]
    path = f"/en/moderation/reports/{report.pk}/"
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
            page.goto(live_server.url + path)
            expect(page.get_by_role("heading", name="Case history", exact=True)).to_have_count(0)
            page.locator("[name=purpose]").fill("Inspect recent and earlier synthetic case actions")
            page.get_by_role("button", name="Record access and inspect", exact=True).click()
            expect(
                page.get_by_text("Synthetic mobile history entry 51 with justification", exact=True)
            ).to_be_visible()
            expect(
                page.get_by_text("Synthetic mobile history entry 0 with justification", exact=True)
            ).to_have_count(0)
            page.get_by_role(
                "button", name="Record access and view older actions", exact=True
            ).click()
            expect(
                page.get_by_text("Synthetic mobile history entry 0 with justification", exact=True)
            ).to_be_visible()
            expect(
                page.get_by_text("Synthetic mobile history entry 51 with justification", exact=True)
            ).to_have_count(0)
            page.goto(live_server.url + path)
            expect(page.get_by_role("heading", name="Case history", exact=True)).to_have_count(0)
            assert "Synthetic mobile history entry" not in page.content()
        finally:
            browser.close()
    assert ReportAccess.objects.filter(report=report).count() == 2
