"""Comparable queue-read diagnostic with real permissions and native COI oracle."""

from datetime import timedelta
from time import perf_counter
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person, User
from apps.safety.crypto import cipher
from apps.safety.models import Report
from apps.safety.views import permitted

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("count", [10, 100])
def test_report_queue_read_cost_and_native_authority(request, record_property, count):
    assert connection.vendor == "postgresql"
    request.getfixturevalue("directory")
    reviewer = User.objects.get(username="fixture-v1-moderator")
    reviewer.user_permissions.add(Permission.objects.get(codename="review_report"))
    agency = Person.objects.get(subject__username="fixture-v1-model-a").agency
    encrypted = cipher().encrypt(b'{"explanation":"Synthetic queue diagnostic private body"}').decode()
    Report.objects.bulk_create([
        Report(submission_key=uuid4(), receipt_digest="0" * 64, payload_digest="1" * 64,
               encrypted_payload=encrypted, reported_agency=agency,
               mode="general", reason="nonconsent", priority=i % 2,
               receipt_expires_at=timezone.now() + timedelta(days=1))
        for i in range(count)
    ])
    expected = [report.pk for report in Report.objects.all() if permitted(reviewer, report)]
    assert len(expected) == count
    client = Client()
    client.force_login(reviewer)
    session = client.session
    session["mfa_version"] = reviewer.mfa_version
    session.save()
    started = perf_counter()
    with CaptureQueriesContext(connection) as captured:
        response = client.get("/en/moderation/reports/")
    elapsed = perf_counter() - started
    assert response.status_code == 200
    assert [report.pk for report in response.context["reports"]] == expected
    assert response["Cache-Control"] == "private, no-store"
    assert b"Synthetic queue diagnostic private body" not in response.content
    assert encrypted.encode() not in response.content

    def primary_reads(table):
        # Count statement roots, not mentions inside joins/subqueries. Never
        # persist SQL, parameters or report bodies in the diagnostic artifact.
        return sum(
            query["sql"].startswith("SELECT")
            and query["sql"].partition("FROM ")[2].startswith('"' + table + '"')
            for query in captured.captured_queries
        )

    record_property("report_queue_read_diagnostic", dict(
        reports=count, native_allowed=len(expected), sql_calls=len(captured),
        primary_agency_reads=primary_reads("core_agency"),
        primary_membership_reads=primary_reads("core_agencymember"),
        elapsed_seconds=elapsed,
        limits="Sequential synthetic Django Client; SQL counts are diagnostic, not TCP capacity or causal CPU attribution",
    ))
