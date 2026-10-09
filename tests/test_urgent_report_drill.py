"""Synthetic urgent escalation through actual internal queues and report decisions."""

import json

import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.utils import timezone
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.crypto import unseal
from apps.safety.models import ReportAccess, ReportAction, ReportNotice, UrgentReportAlert

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
def test_urgent_owner_revocation_escalates_to_authorized_substitute(
    request, language, record_property
):
    public = request.getfixturevalue("directory")
    report = case(public)
    primary, staff = reviewer()
    substitute = User.objects.get(username="fixture-v1-visitor")
    substitute.mfa_enabled = True
    substitute.save(update_fields=["mfa_enabled"])
    review_permission = Permission.objects.get(codename="review_report")
    substitute.user_permissions.add(review_permission)
    other = Client()
    other.force_login(substitute)
    session = other.session
    session["mfa_version"] = substitute.mfa_version
    session.save()
    alert_path = f"/{language}/moderation/reports/urgent-alerts/"
    inspect_path = f"/{language}/moderation/reports/{report.pk}/"
    chronology = [{"stage": "received", "at": report.created_at.isoformat()}]

    def mark(stage):
        chronology.append({"stage": stage, "at": timezone.now().isoformat()})

    def operate(client, operation):
        path, values = action(client, report, operation)
        path = path.replace("/en/", f"/{language}/", 1)
        return path, values, client.post(path, values)

    def followed(client):
        response = client.get(alert_path, {"attention": "follow_up"})
        assert response.status_code == 200
        assert response["Cache-Control"] == "private, no-store"
        assert b"private@example.invalid" not in response.content
        return {alert.report_id for alert in response.context["page"]}

    assert report.priority == 0
    assert staff.post(alert_path, {"report_id": report.pk}).status_code == 302
    original_ack = UrgentReportAlert.objects.get(report=report)
    mark("acknowledged")
    report.refresh_from_db()
    assert report.status == "received" and report.assigned_to_id is None
    assert not ReportAccess.objects.filter(report=report).exists()
    assert report.pk in followed(staff)
    assert operate(staff, "claim")[2].status_code == 302
    mark("primary_assigned")
    report.refresh_from_db()
    assert report.assigned_to_id == primary.pk and report.status == "reviewing"
    primary.user_permissions.remove(review_permission)
    mark("primary_revoked")
    assert staff.get(inspect_path).status_code == 403
    assert (
        staff.post(
            inspect_path, {"purpose": "Revoked primary must not inspect evidence"}
        ).status_code
        == 403
    )
    assert other.get(alert_path).status_code == 200
    before = ReportAction.objects.filter(report=report).count()
    assert operate(other, "unassign")[2].status_code == 403
    assert ReportAction.objects.filter(report=report).count() == before
    substitute.user_permissions.add(Permission.objects.get(codename="manage_report_assignment"))
    assert operate(other, "unassign")[2].status_code == 302
    mark("escalated_unassigned")
    report.refresh_from_db()
    assert report.status == "received" and report.assigned_to_id is None
    assert report.pk in followed(other)
    assert operate(other, "claim")[2].status_code == 302
    mark("substitute_assigned")
    report.refresh_from_db()
    assert report.assigned_to_id == substitute.pk
    assert operate(other, "dismiss")[2].status_code == 409
    assert not ReportAccess.objects.filter(report=report, actor=substitute).exists()
    assert (
        other.post(
            inspect_path, {"purpose": "Review synthetic urgent evidence before substitute decision"}
        ).status_code
        == 200
    )
    mark("evidence_read")
    assert ReportAccess.objects.filter(
        report=report, actor=substitute, case_version=report.version
    ).exists()
    path, values, response = operate(other, "dismiss")
    assert response.status_code == 302
    mark("resolved")
    report.refresh_from_db()
    assert report.status == "dismissed" and report.assigned_to_id == substitute.pk
    version = report.version
    assert other.post(path, values).status_code == 302
    report.refresh_from_db()
    assert report.version == version
    assert ReportAction.objects.filter(report=report).count() == 4
    assert report.pk not in followed(other)
    final_ack = UrgentReportAlert.objects.get(report=report)
    assert (final_ack.acknowledged_by_id, final_ack.acknowledged_at) == (
        primary.pk,
        original_ack.acknowledged_at,
    )
    notices = ReportNotice.objects.filter(report=report)
    assert notices.count() == 2 and set(notices.values_list("status", flat=True)) == {"queued"}
    for notice in notices:
        assert unseal(notice.encrypted_payload)["recipient"] == "private@example.invalid"
        assert values["reason"] not in unseal(notice.encrypted_payload)["body"]
    seconds = (timezone.now() - report.created_at).total_seconds()
    record_property("synthetic_deadline_seconds", 300)
    record_property("observed_resolution_seconds", seconds)
    record_property("internal_queue_chronology", json.dumps(chronology))
    assert 0 <= seconds <= 300


@pytest.mark.parametrize("revoked", ["permission", "session", "mfa", "active"])
@pytest.mark.parametrize("replay,window", [(False, "locks"), (True, "locks"), (False, "return")])
def test_report_decision_rechecks_revocation_after_scoped_locks(
    request, monkeypatch, revoked, replay, window
):
    from uuid import uuid4

    from django.core.exceptions import PermissionDenied
    from django.db.models import F

    from apps.safety import views
    from apps.safety.decisions import act

    public = request.getfixturevalue("directory")
    report = case(public)
    actor, _ = reviewer()
    key = uuid4()
    reason = "Synthetic claim requires authority current after all scoped locks"
    if replay:
        act(actor, report.pk, key, report.version, "claim", reason)
    before = ReportAction.objects.filter(report=report).count()
    original = views.permitted
    changed = False

    def revoke(user, candidate):
        nonlocal changed
        permitted = original(user, candidate)
        if not changed:
            changed = True
            if revoked == "permission":
                User.objects.get(pk=actor.pk).user_permissions.remove(
                    Permission.objects.get(codename="review_report")
                )
            elif revoked == "active":
                User.objects.filter(pk=actor.pk).update(is_active=False)
            else:
                field = "session_version" if revoked == "session" else "mfa_version"
                User.objects.filter(pk=actor.pk).update(**{field: F(field) + 1})
        return permitted

    if window == "locks":
        monkeypatch.setattr(views, "permitted", revoke)
    else:
        from apps.safety import decisions

        enqueue = decisions.enqueue_outcome

        def after_outbox(candidate, saved_action):
            result = enqueue(candidate, saved_action)
            revoke(actor, candidate)
            return result

        monkeypatch.setattr(decisions, "enqueue_outcome", after_outbox)
    with pytest.raises(PermissionDenied):
        act(actor, report.pk, key, report.version, "claim", reason)
    assert changed
    assert ReportAction.objects.filter(report=report).count() == before
    report.refresh_from_db()
    assert report.status == ("reviewing" if replay else "received")
