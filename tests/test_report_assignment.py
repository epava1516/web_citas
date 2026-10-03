import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import User
from apps.safety.models import ReportAction

pytestmark = pytest.mark.django_db(transaction=True)


def coordinator():
    user = User.objects.get(username="fixture-v1-visitor")
    user.mfa_enabled = True
    user.mfa_version = 1
    user.save(update_fields=["mfa_enabled", "mfa_version"])
    user.user_permissions.add(
        *Permission.objects.filter(codename__in=["review_report", "manage_report_assignment"])
    )
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = 1
    session.save()
    return user, client


def test_coordinator_recovers_assignment_after_reviewer_loses_permission(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    reviewer_user, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    path, data = action(staff, report, "unassign")
    assert staff.post(path, data).status_code == 403
    reviewer_user.user_permissions.clear()
    responsible, admin = coordinator()
    path, data = action(admin, report, "unassign")
    assert admin.post(path, data).status_code == 302
    assert admin.post(path, data).status_code == 302
    report.refresh_from_db()
    assert report.status == "received" and report.assigned_to_id is None and report.version == 3
    assert ReportAction.objects.filter(operation="unassign").count() == 1
    path, claim = action(admin, report, "claim")
    assert admin.post(path, claim).status_code == 302
    report.refresh_from_db()
    assert report.assigned_to_id == responsible.pk and report.version == 4
    assert admin.post(path, data).status_code == 302
    report.refresh_from_db()
    assert report.assigned_to_id == responsible.pk and report.version == 4


def test_unassignment_cannot_reopen_resolved_case(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    _, staff = reviewer()
    path, data = action(staff, report, "claim")
    staff.post(path, data)
    staff.post(
        f"/en/moderation/reports/{report.pk}/", {"purpose": "Read evidence before resolving report"}
    )
    path, data = action(staff, report, "dismiss")
    assert staff.post(path, data).status_code == 302
    _, admin = coordinator()
    path, data = action(admin, report, "unassign")
    assert admin.post(path, data).status_code == 409
    report.refresh_from_db()
    assert report.status == "dismissed" and report.version == 3
    assert not ReportAction.objects.filter(operation="unassign").exists()


def test_report_author_cannot_coordinate_own_case(request):
    request.getfixturevalue("directory")
    _, admin = coordinator()
    report = case(admin)
    _, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    path = f"/en/moderation/reports/{report.pk}/decision/"
    assert admin.post(path, {"operation": "unassign"}).status_code == 403
    report.refresh_from_db()
    assert report.status == "reviewing" and report.version == 2
    assert not ReportAction.objects.filter(operation="unassign").exists()


def test_unassignment_racing_restriction_cannot_erase_resolved_restriction(request):
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.core.exceptions import ValidationError
    from django.db import close_old_connections, connections

    from apps.core.models import Person
    from apps.safety.decisions import act
    from apps.safety.models import Restriction

    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-individual")
    report = case(client, person)
    moderator, staff = reviewer()
    responsible, _ = coordinator()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Read evidence before preventive restriction"},
    )
    barrier = Barrier(2)
    revision_id = person.listing.approved_revision_id

    def perform(operation):
        close_old_connections()
        try:
            actor = User.objects.get(pk=moderator.pk if operation == "restrict" else responsible.pk)
            barrier.wait(timeout=10)
            try:
                act(
                    actor,
                    report.pk,
                    uuid.uuid4(),
                    2,
                    operation,
                    "Synthetic reason for versioned concurrent action",
                    manager_version=person.manager_version if operation == "restrict" else None,
                    revision_id=revision_id if operation == "restrict" else None,
                )
                return operation
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(perform, ["restrict", "unassign"]))
    report.refresh_from_db()
    assert outcomes.count(None) == 1
    assert report.version == 3 and ReportAction.objects.count() == 2
    if "restrict" in outcomes:
        assert report.status == "restricted"
        assert Restriction.objects.filter(report=report, active=True).count() == 1
    else:
        assert report.status == "received" and report.assigned_to_id is None
        assert not Restriction.objects.exists()
