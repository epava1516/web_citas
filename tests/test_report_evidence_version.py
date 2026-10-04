import pytest
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.safety.models import Report, ReportAccess, ReportAction

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    path = f"/en/moderation/reports/{report.pk}/"
    assert (
        staff.post(path, {"purpose": "Inspect current evidence before deciding case"}).status_code
        == 200
    )
    report.refresh_from_db()
    return report, user, staff, path


def test_case_change_invalidates_old_read_even_with_fresh_decision_form(request):
    report, user, staff, path = prepared(request)
    access = ReportAccess.objects.get(report=report, actor=user)
    assert access.case_version == report.version and access.action_before is None
    # Controlled new evidence version, not a claim of a delivered public appeal.
    Report.objects.filter(pk=report.pk).update(version=report.version + 1)
    decision_path, data = action(staff, report, "dismiss")
    assert staff.post(decision_path, data).status_code == 409
    assert not ReportAction.objects.filter(operation="dismiss").exists()
    assert (
        staff.post(path, {"purpose": "Read newly versioned evidence before deciding"}).status_code
        == 200
    )
    assert staff.post(decision_path, data).status_code == 302
    assert staff.post(decision_path, data).status_code == 302
    assert ReportAction.objects.filter(operation="dismiss").count() == 1
    assert ReportAccess.objects.filter(report=report).count() == 2


@pytest.mark.parametrize("invalid_read", ["legacy", "older_page"])
def test_legacy_or_older_page_audit_cannot_authorize_current_decision(request, invalid_read):
    report, user, staff, path = prepared(request)
    change = {"case_version": None} if invalid_read == "legacy" else {"action_before": 123}
    ReportAccess.objects.filter(report=report, actor=user).update(**change)
    decision_path, data = action(staff, report, "dismiss")
    assert staff.post(decision_path, data).status_code == 409
    assert (
        staff.post(
            path, {"purpose": "Inspect latest case evidence with an attributable audit"}
        ).status_code
        == 200
    )
    assert staff.post(decision_path, data).status_code == 302


def test_older_history_post_records_cursor_and_get_does_not_grant_read(request):
    report, user, staff, path = prepared(request)
    ReportAccess.objects.filter(report=report).delete()
    assert staff.get(path).status_code == 200
    assert not ReportAccess.objects.filter(report=report).exists()
    response = staff.post(
        path,
        {
            "purpose": "Read older action history with distinct audited cursor",
            "action_before": 123,
        },
    )
    assert response.status_code == 200
    access = ReportAccess.objects.get(report=report, actor=user)
    assert access.case_version == report.version and access.action_before == 123
    decision_path, data = action(staff, report, "dismiss")
    assert staff.post(decision_path, data).status_code == 409
