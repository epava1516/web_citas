"""Only the subject's own agency relationships enter a reviewed private copy."""

from copy import deepcopy
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from test_account_copy_races import prepared_account
from test_reports import directory, photo_environment  # noqa: F401
from test_rights_copy_compilation import review_all
from test_rights_exports import prepared

from apps.core.models import Agency, AgencyMember
from apps.safety.crypto import unseal
from apps.safety.rights_copy_data import subject_data
from apps.safety.rights_copy_inspection import inspect_page
from apps.safety.rights_copy_page_review import generate_pages, record

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("account_only", [False, True])
def test_agency_relationships_include_own_owner_and_inactive_membership_without_roster(
    request, settings, monkeypatch, account_only
):
    if account_only:
        case, actor, _, subject, _, _ = prepared_account(request, settings, monkeypatch)
    else:
        case, actor, _, _, _, person = prepared(request, settings)
        subject = person.subject
    owned, _ = Agency.objects.get_or_create(
        owner=subject, defaults={"name": "PRIVATE_OWN_AGENCY_NAME"}
    )
    foreign = Agency.objects.exclude(owner=subject).first()
    assert foreign is not None
    own_member, _ = AgencyMember.objects.get_or_create(agency=owned, user=subject)
    inactive, _ = AgencyMember.objects.get_or_create(
        agency=foreign, user=subject, defaults={"active": False}
    )
    inactive.active = False
    inactive.save(update_fields=["active"])
    AgencyMember.objects.get_or_create(agency=owned, user=actor)
    read = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect subject agency relationships",
        section="agency_relationships",
    )
    relations = read["entries"]
    assert any(
        row["agency_reference"] == str(owned.pk) and row["relationship"] == "owner"
        for row in relations
    )
    assert any(
        row["agency_reference"] == str(owned.pk) and row["relationship"] == "member"
        for row in relations
    )
    assert any(
        row["agency_reference"] == str(foreign.pk)
        and row["relationship"] == "member"
        and row["active"] is False
        for row in relations
    )
    assert all(
        set(row) <= {"agency_reference", "relationship", "active", "created_at"}
        for row in relations
    )
    assert owned.name not in str(relations) and actor.email not in str(relations)
    injected = deepcopy(relations)
    injected[0]["agency_reference"] = str(uuid4())
    with pytest.raises(ValidationError, match="immutable"):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            0,
            "Reject foreign agency reference injection",
            injected,
        )
    review_all(case, actor)
    export = generate_pages(
        actor, case.pk, case.version, uuid4(), "Deliver own agency relationship projection"
    )
    delivered = unseal(export.encrypted_payload)["account_activity"]["agency_relationships"]
    assert delivered == relations
    assert AgencyMember.objects.filter(pk=own_member.pk, active=True).exists()


def test_membership_change_invalidates_page_and_unlinked_subject_never_uses_manager(
    request, settings
):
    case, actor, _, _, _, person = prepared(request, settings)
    agency = Agency.objects.first()
    member, _ = AgencyMember.objects.get_or_create(agency=agency, user=person.subject)
    read = inspect_page(
        actor,
        case.pk,
        case.version,
        uuid4(),
        "Inspect membership before revocation",
        section="agency_relationships",
    )
    member.active = not member.active
    member.save(update_fields=["active"])
    with pytest.raises(ValidationError, match="source changed"):
        record(
            actor,
            case.pk,
            case.version,
            uuid4(),
            read["read_id"],
            0,
            "Reject obsolete agency membership decision",
            read["entries"],
        )
    # Projection-only check: an unlinked person cannot acquire the manager's account data.
    person.subject = None
    assert subject_data(person)["account_activity"]["agency_relationships"] == []


def test_relationship_pages_cover_own_memberships_once_and_get_hides_references(request, settings):
    from django.urls import reverse

    from apps.core.models import User

    case, actor, staff, _, _, person = prepared(request, settings)
    # Synthetic relationships test projection/pagination, not invitation or agency acceptance.
    agencies = []
    for index in range(21):
        owner = User.objects.create_user(
            username=f"synthetic-copy-owner-{index}", email=f"copy-owner-{index}@example.invalid"
        )
        agencies.append(
            Agency.objects.create(owner=owner, name=f"Private synthetic agency {index}")
        )
    AgencyMember.objects.bulk_create(
        [
            AgencyMember(agency=agency, user=person.subject, active=(index % 2 == 0))
            for index, agency in enumerate(agencies)
        ]
    )
    path = reverse("rights_export_prepare", kwargs={"case_id": case.pk})
    response = staff.post(
        path,
        {
            "key": uuid4(),
            "version": case.version,
            "operation": "inspect_page",
            "section": "agency_relationships",
            "purpose": "Inspect first page of own relationships",
        },
    )
    assert response.status_code == 200
    read = response.context["page_data"]
    assert len(read["entries"]) == 10 and read["has_next"]
    seen = list(read["entries"])
    while read["has_next"]:
        read = inspect_page(
            actor,
            case.pk,
            case.version,
            uuid4(),
            "Inspect remaining own relationship page",
            "agency_relationships",
            read["page"] + 1,
            read["cursor"],
        )
        seen.extend(read["entries"])
    pairs = [(item["agency_reference"], item["relationship"]) for item in seen]
    assert len(pairs) == len(set(pairs))
    assert {str(agency.pk) for agency in agencies} <= {reference for reference, _ in pairs}
    expected_count = (
        AgencyMember.objects.filter(user=person.subject).count()
        + Agency.objects.filter(owner=person.subject).count()
    )
    assert len(seen) == expected_count
    get = staff.get(path)
    assert get.status_code == 200
    assert all(str(agency.pk).encode() not in get.content for agency in agencies)
    assert "no-store" in response["Cache-Control"]
