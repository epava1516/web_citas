import pytest
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import Agency, AgencyMember, ManagerReview, User
from apps.core.verification_services import publication_ready


@pytest.mark.django_db(transaction=True)
def test_transfer_requires_current_human_review_before_readiness(request):
    person, owner, _, _, reviewer = request.getfixturevalue("pending")
    phone = person.phone_claim
    photo = person.listing.revisions.get().photos.get()
    assert owner.post(f"/es/person/{person.pk}/transfer/", {"confirm": "on"}).status_code == 302
    person.refresh_from_db()
    assert owner.get(f"/es/photos/{photo.pk}/private/").status_code == 404
    assert person.manager_review_status == "pending" and not publication_ready(person)
    path = f"/es/moderation/managers/{person.pk}/"
    data = {
        "manager_version": person.manager_version,
        "outcome": "approved",
        "reason": "Cambio sintético autorizado y revisado",
    }
    assert owner.get(path).status_code == 403
    assert reviewer.post(path, data).status_code == 400
    assert (
        owner.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "dev-1"}
        ).status_code
        == 302
    )
    assert owner.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 302
    person.refresh_from_db()
    person.phone_claim = phone
    person.save(update_fields=["phone_claim"])
    assert not publication_ready(person)
    assert reviewer.post(path, data).status_code == 302
    person.refresh_from_db()
    assert publication_ready(person) and ManagerReview.objects.count() == 1
    assert reviewer.post(path, data).status_code == 409


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("association", ["owner", "revoked_editor"])
@pytest.mark.parametrize("legacy", [False, True])
def test_previous_agency_cannot_review_its_transfer(request, association, legacy):
    person, subject_client, _, moderator, reviewer = request.getfixturevalue("pending")
    if association == "owner":
        agency = Agency.objects.create(owner=moderator, name="Agencia anterior sintética")
    else:
        agency_owner = User.objects.create_user(
            username="previous-agency-owner", email="previous-owner@example.invalid"
        )
        agency = Agency.objects.create(owner=agency_owner, name="Agencia anterior sintética")
        AgencyMember.objects.create(agency=agency, user=moderator, active=False)
    person.individual = None
    person.agency = agency
    person.save(update_fields=["individual", "agency"])
    person.representationaction_set.filter(action="grant").update(
        manager_kind="agency", manager_id=str(agency.pk)
    )
    assert (
        subject_client.post(f"/es/person/{person.pk}/transfer/", {"confirm": "on"}).status_code
        == 302
    )
    person.refresh_from_db()
    action = person.representationaction_set.get(action="transfer")
    assert action.previous_manager_kind == "agency" and action.previous_manager_id == str(agency.pk)
    if legacy:
        action.previous_manager_kind = action.previous_manager_id = ""
        action.save(update_fields=["previous_manager_kind", "previous_manager_id"])
    path = f"/es/moderation/managers/{person.pk}/"
    assert reviewer.get(path).status_code == 403
    assert (
        reviewer.post(
            path,
            {
                "manager_version": person.manager_version,
                "outcome": "failed",
                "reason": "Conflicto de interés",
            },
        ).status_code
        == 403
    )
    assert not ManagerReview.objects.exists()
