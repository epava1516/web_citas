"""Bounded SQL paging preserves every report conflict exclusion."""

import uuid

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import AgencyMember, Person, User
from apps.safety.models import Report, UrgentReportAlert
from apps.safety.views import permitted

pytestmark = pytest.mark.django_db(transaction=True)
PATH = "/en/moderation/reports/urgent-alerts/"


def add_report(**fields):
    report = Report.objects.create(
        submission_key=uuid.uuid4(),
        receipt_digest="synthetic",
        payload_digest="synthetic",
        encrypted_payload="synthetic-not-disclosed",
        mode="informal",
        reason="other",
        receipt_expires_at=timezone.now(),
        **fields,
    )
    UrgentReportAlert.objects.create(report=report)
    return report


def test_pages_count_only_visible_reports_and_limit_sql(request):
    request.getfixturevalue("directory")
    user, staff = reviewer()
    for _ in range(57):
        add_report()
    for _ in range(11):
        add_report(actor=user)
    with CaptureQueriesContext(connection) as queries:
        first = staff.get(PATH)
    captured = list(queries.captured_queries)
    second = staff.get(PATH, {"page": 2})
    page = first.context["page"]
    assert page.paginator.count == 57
    assert len(page) == 50 and len(second.context["page"]) == 7
    first_ids = {a.pk for a in page}
    second_ids = {a.pk for a in second.context["page"]}
    assert not first_ids & second_ids
    assert len(first_ids | second_ids) == 57
    alert_selects = [
        q["sql"]
        for q in captured
        if 'FROM "safety_urgentreportalert"' in q["sql"] and "COUNT(" not in q["sql"]
    ]
    assert len(alert_selects) == 1 and "LIMIT 50" in alert_selects[0]
    assert first["Cache-Control"] == "private, no-store"
    assert b"synthetic-not-disclosed" not in first.content


def test_sql_scope_matches_permitted_for_current_and_historical_conflicts(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    targeted = case(client, person)
    add_report()
    add_report(listing=person.listing)
    add_report(revision=targeted.revision, manager_version=None)
    add_report(reported_agency=person.agency)
    users = list(
        User.objects.filter(
            username__in=[
                "fixture-v1-moderator",
                "fixture-v1-editor",
                "fixture-v1-model-a",
            ]
        )
    ) + [person.agency.owner]
    for active in [True, False]:
        AgencyMember.objects.filter(agency=person.agency).update(active=active)
        for user in users:
            user.user_permissions.add(Permission.objects.get(codename="review_report"))
            user.mfa_enabled = True
            user.save(update_fields=["mfa_enabled"])
            staff = Client()
            staff.force_login(user)
            session = staff.session
            session["mfa_version"] = user.mfa_version
            session.save()
            personal = add_report(actor=user)
            subject = add_report(reported_subject=user)
            individual = add_report(reported_individual=user)
            expected = {
                a.pk
                for a in UrgentReportAlert.objects.select_related(
                    "report__listing__person__agency", "report__reported_agency"
                )
                if permitted(user, a.report)
            }
            response = staff.get(PATH)
            assert response.status_code == 200
            page = response.context["page"]
            assert page.paginator.count == len(expected)
            assert {a.pk for a in page} == expected
            assert (
                not {personal.urgent_alert.pk, subject.urgent_alert.pk, individual.urgent_alert.pk}
                & expected
            )
