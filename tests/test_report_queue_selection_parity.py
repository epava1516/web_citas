"""Queue ordering and COI against the unchanged per-report authority oracle."""

from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.models import Permission
from django.db import connection
from django.test import Client
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Agency, AgencyMember, Person, User
from apps.safety.crypto import cipher
from apps.safety.models import Report
from apps.safety.views import permitted

pytestmark = pytest.mark.django_db(transaction=True)


def login_reviewer(user):
    user.mfa_enabled = True
    user.save(update_fields=["mfa_enabled"])
    user.user_permissions.add(Permission.objects.get(codename="review_report"))
    client = Client()
    client.force_login(user)
    session = client.session
    session["mfa_version"] = user.mfa_version
    session["account_version"] = user.session_version
    session.save()
    return client


def report(**changes):
    return Report(
        submission_key=uuid4(), receipt_digest="0" * 64, payload_digest="1" * 64,
        encrypted_payload=cipher().encrypt(b'{"explanation":"Synthetic queue private body"}').decode(),
        mode="general", reason="nonconsent", receipt_expires_at=timezone.now() + timedelta(days=1),
        **changes,
    )


def native_ids(user, statuses):
    rows = Report.objects.filter(status__in=statuses).select_related(
        "reported_agency", "listing__person__agency",
    )
    return [row.pk for row in rows if permitted(user, row)]


@pytest.mark.parametrize("role", ["moderator", "individual", "owner", "subject", "active_editor", "inactive_editor"])
def test_queue_matches_native_coi_order_and_statuses(request, record_property, role):
    assert connection.vendor == "postgresql"
    request.getfixturevalue("directory")
    individual = Person.objects.get(individual__username="fixture-v1-individual")
    represented = Person.objects.select_related("agency__owner", "subject", "assigned_editor").get(
        subject__username="fixture-v1-model-a",
    )
    users = dict(moderator=User.objects.get(username="fixture-v1-moderator"),
                 individual=individual.individual, owner=represented.agency.owner,
                 subject=represented.subject, active_editor=represented.assigned_editor,
                 inactive_editor=represented.assigned_editor)
    user = users[role]
    assert user is not None
    if role.endswith("editor"):
        assert AgencyMember.objects.filter(agency=represented.agency, user=user).update(
            active=role == "active_editor",
        ) == 1
    client = login_reviewer(user)
    individual_target = dict(listing=individual.listing, revision=individual.listing.approved_revision,
                             manager_version=individual.manager_version)
    represented_target = dict(listing=represented.listing, revision=represented.listing.approved_revision,
                              manager_version=represented.manager_version)
    cases = {
        "general": {}, "individual_listing": individual_target,
        "represented_listing": represented_target,
        "agency_snapshot": dict(reported_agency=represented.agency),
        "snapshot_and_listing": dict(**represented_target, reported_agency=represented.agency),
        "actor_self": dict(actor=user), "individual_self": dict(reported_individual=user),
        "subject_self": dict(reported_subject=user),
        "legacy_snapshot": dict(listing=represented.listing, revision=represented.listing.approved_revision),
    }
    rows, shapes = [], {}
    for index, (kind, fields) in enumerate(cases.items()):
        for status in ["received", "reviewing", "restricted", "upheld", "dismissed"]:
            row = report(**fields, status=status, priority=index % 2)
            rows.append(row)
            shapes[row.pk] = kind
    Report.objects.bulk_create(rows)
    restriction = Permission.objects.get(codename="review_restriction")
    comparisons = []
    for restrictions in [False, True]:
        if restrictions:
            user.user_permissions.add(restriction)
        else:
            user.user_permissions.remove(restriction)
        assert User.objects.get(pk=user.pk).has_perm("safety.review_restriction") is restrictions
        statuses = ["received", "reviewing"] + (["restricted", "upheld"] if restrictions else [])
        expected = native_ids(user, statuses)
        kinds = {shapes[pk] for pk in expected}
        assert "general" in kinds
        assert not kinds & {"actor_self", "individual_self", "subject_self", "legacy_snapshot"}
        if role == "individual":
            assert "individual_listing" not in kinds
        if role in {"owner", "subject", "active_editor"}:
            assert "represented_listing" not in kinds
        if role == "inactive_editor":
            assert "represented_listing" in kinds
            assert not kinds & {"agency_snapshot", "snapshot_and_listing"}
        for language in ["es", "en"]:
            response = client.get(f"/{language}/moderation/reports/")
            assert response.status_code == 200
            ids = [row.pk for row in response.context["reports"]]
            assert ids == expected and len(ids) == len(set(ids))
            assert response["Cache-Control"] == "private, no-store"
            assert b"Synthetic queue private body" not in response.content
            comparisons.append(dict(language=language, restrictions=restrictions, count=len(ids)))
    record_property("queue_coi_parity", dict(role=role, comparisons=comparisons))


def test_queue_membership_and_owner_changes_are_fresh_next_request(request, record_property):
    request.getfixturevalue("directory")
    user = User.objects.get(username="fixture-v1-moderator")
    person = Person.objects.select_related("agency").get(subject__username="fixture-v1-model-a")
    agency, previous_owner = person.agency, person.agency.owner
    client = login_reviewer(user)
    Report.objects.bulk_create([
        report(listing=person.listing, revision=person.listing.approved_revision,
               manager_version=person.manager_version),
        report(reported_agency=agency),
    ])
    observations = []

    def observe(count):
        response = client.get("/en/moderation/reports/")
        assert response.status_code == 200
        ids = [row.pk for row in response.context["reports"]]
        assert ids == native_ids(user, ["received", "reviewing"]) and len(ids) == count
        observations.append(count)

    observe(2)
    membership = AgencyMember.objects.create(agency=agency, user=user, active=False)
    observe(1)
    AgencyMember.objects.filter(pk=membership.pk).update(active=True)
    observe(0)
    membership.delete()
    observe(2)
    assert Agency.objects.filter(pk=agency.pk).update(owner=user) == 1
    observe(0)
    assert Agency.objects.filter(pk=agency.pk).update(owner=previous_owner) == 1
    observe(2)
    record_property("queue_next_request_authority", observations)
