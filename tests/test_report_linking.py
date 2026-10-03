import pytest
from test_report_decisions import action
from test_report_inspection import case, reviewer
from test_reports import directory, photo_environment  # noqa: F401

from apps.core.models import Person
from apps.safety.models import ReportAccess, ReportAction

pytestmark = pytest.mark.django_db(transaction=True)


def prepared(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    user, staff = reviewer()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    assert (
        staff.post(
            f"/en/moderation/reports/{report.pk}/",
            {"purpose": "Read manual reference before associating publication"},
        ).status_code
        == 200
    )
    return report, user, staff


def test_manual_reference_link_preserves_payload_and_snapshot_then_allows_review(request):
    report, _, staff = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    original_payload = report.encrypted_payload
    path, data = action(staff, report, "link", link_listing_id=person.listing.pk)
    assert staff.post(path, data).status_code == 302
    assert staff.post(path, data).status_code == 302
    report.refresh_from_db()
    assert report.listing_id == person.listing.pk
    assert report.revision_id == person.listing.approved_revision_id
    assert report.reported_individual_id == person.individual_id
    assert report.reported_subject_id == person.subject_id
    assert report.manager_version == person.manager_version
    assert report.encrypted_payload == original_payload
    assert report.status == "reviewing" and report.version == 3
    assert ReportAction.objects.filter(operation="link").count() == 1
    other = Person.objects.get(subject__username="fixture-v1-model-a")
    path, changed = action(staff, report, "link", link_listing_id=other.listing.pk)
    assert staff.post(path, changed).status_code == 409
    path, data = action(staff, report, "restrict")
    assert staff.post(path, data).status_code == 302


def test_linking_to_own_publication_is_denied_and_rolls_back(request):
    report, moderator, staff = prepared(request)
    person = Person.objects.get(subject__username="fixture-v1-individual")
    # A newly acquired management relationship must be checked at the linking boundary.
    Person.objects.filter(pk=person.pk).update(individual=moderator)
    path, data = action(staff, report, "link", link_listing_id=person.listing.pk)
    assert staff.post(path, data).status_code == 403
    report.refresh_from_db()
    assert report.listing_id is None and report.version == 2
    assert ReportAction.objects.count() == 1


def test_link_requires_assignment_evidence_and_published_head(request):
    client = request.getfixturevalue("directory")
    report = case(client)
    _, staff = reviewer()
    person = Person.objects.get(subject__username="fixture-v1-model-b")
    path, data = action(staff, report, "link", link_listing_id=person.listing.pk)
    assert staff.post(path, data).status_code == 409
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    path, data = action(staff, report, "link", link_listing_id=person.listing.pk)
    assert staff.post(path, data).status_code == 409
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect exact reference before linking"},
    )
    assert staff.post(path, data).status_code == 409
    report.refresh_from_db()
    assert report.listing_id is None and report.version == 2
    assert ReportAction.objects.count() == 1 and ReportAccess.objects.count() == 1


def test_revoked_original_agency_editor_cannot_link_transferred_publication(request):
    from django.contrib.auth.models import Permission
    from django.test import Client

    from apps.core.models import AgencyMember, User

    client = request.getfixturevalue("directory")
    report = case(client)
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    agency = person.agency
    person.agency = None
    person.individual = person.subject
    person.assigned_editor = None
    person.manager_version += 1
    person.save()
    AgencyMember.objects.filter(agency=agency).update(active=False)
    editor = User.objects.get(username="fixture-v1-editor")
    editor.user_permissions.add(Permission.objects.get(codename="review_report"))
    staff = Client()
    staff.force_login(editor)
    session = staff.session
    session["mfa_version"] = editor.mfa_version
    session.save()
    path, data = action(staff, report, "claim")
    assert staff.post(path, data).status_code == 302
    staff.post(
        f"/en/moderation/reports/{report.pk}/",
        {"purpose": "Inspect reference before identifying target"},
    )
    path, data = action(staff, report, "link", link_listing_id=person.listing.pk)
    assert staff.post(path, data).status_code == 403
    report.refresh_from_db()
    assert report.listing_id is None and report.version == 2
    assert ReportAction.objects.count() == 1


def test_racing_links_cannot_overwrite_another_identified_publication(request):
    import uuid
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.core.exceptions import ValidationError
    from django.db import close_old_connections, connections

    from apps.core.models import User
    from apps.safety.decisions import act

    report, user, _ = prepared(request)
    people = [
        Person.objects.get(subject__username=name)
        for name in ["fixture-v1-individual", "fixture-v1-model-a"]
    ]
    ids = [person.listing.pk for person in people]
    barrier = Barrier(2)

    def link(listing_id):
        close_old_connections()
        try:
            moderator = User.objects.get(pk=user.pk)
            barrier.wait(timeout=10)
            try:
                result = act(
                    moderator,
                    report.pk,
                    uuid.uuid4(),
                    2,
                    "link",
                    "Exact reference supports synthetic publication link",
                    link_listing_id=listing_id,
                )
                return result.listing_id
            except ValidationError:
                return None
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(link, ids))
    report.refresh_from_db()
    assert outcomes.count(None) == 1
    assert report.listing_id in [value for value in outcomes if value]
    assert report.version == 3 and report.status == "reviewing"
    assert report.revision_id == report.listing.approved_revision_id
    assert ReportAction.objects.filter(operation="link").count() == 1
