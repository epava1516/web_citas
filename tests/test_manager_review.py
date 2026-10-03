from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import close_old_connections, connections
from django.test import Client
from test_drafts import scenario  # noqa: F401
from test_listing_moderation import pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import Agency, AgencyMember, ManagerReview, Person, User
from apps.core.verification_services import publication_ready


@pytest.mark.django_db(transaction=True)
def test_transfer_requires_current_human_review_before_readiness(request):
    person, owner, _, _, reviewer = request.getfixturevalue("pending")
    phone = person.phone_claim
    photo = person.listing.revisions.get().photos.get()
    assert (
        owner.post(
            f"/es/person/{person.pk}/transfer/",
            {"confirm": "on", "manager_version": person.manager_version},
        ).status_code
        == 302
    )
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
        subject_client.post(
            f"/es/person/{person.pk}/transfer/",
            {"confirm": "on", "manager_version": person.manager_version},
        ).status_code
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


@pytest.mark.django_db(transaction=True)
def test_transfer_double_submit_does_not_reset_new_authorization(request):
    person, owner, _, _, _ = request.getfixturevalue("pending")
    data = {"confirm": "on", "manager_version": person.manager_version}
    path = f"/es/person/{person.pk}/transfer/"
    assert owner.post(path, data).status_code == 302
    person.refresh_from_db()
    assert (
        owner.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "dev-1"}
        ).status_code
        == 302
    )
    assert owner.post(path, data).status_code == 302
    person.refresh_from_db()
    assert person.manager_version == data["manager_version"] + 1
    assert person.consent_version == person.manager_version and not person.consent_revoked_at
    assert person.representationaction_set.filter(action="transfer").count() == 1
    assert owner.post(path, {"confirm": "on"}).status_code == 400
    agency = Agency.objects.create(
        owner=User.objects.create_user(
            username="different-target", email="different-target@example.invalid"
        ),
        name="Otra agencia sintética",
    )
    assert owner.post(path, {**data, "target_agency": str(agency.pk)}).status_code == 409


@pytest.mark.django_db(transaction=True)
def test_concurrent_transfer_retries_create_one_event(request):
    person, _, _, _, _ = request.getfixturevalue("pending")
    subject = person.subject
    barrier = Barrier(2)
    data = {"confirm": "on", "manager_version": person.manager_version}

    def transfer():
        close_old_connections()
        try:
            client = Client()
            client.force_login(subject)
            barrier.wait(timeout=5)
            return client.post(f"/es/person/{person.pk}/transfer/", data).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(lambda _: transfer(), range(2))) == [302, 302]
    person.refresh_from_db()
    assert person.manager_version == data["manager_version"] + 1
    assert person.representationaction_set.filter(action="transfer").count() == 1


@pytest.mark.django_db(transaction=True)
def test_transfer_to_full_agency_preserves_management_and_retry(request, settings):
    person, subject_client, _, _, _ = request.getfixturevalue("pending")
    settings.AGENCY_PENDING_PERSON_LIMIT = 1
    agency = Agency.objects.create(
        owner=User.objects.create_user(username="full-agency", email="full@example.invalid"),
        name="Destino limitado",
    )
    existing = Person.objects.create(agency=agency, alias="Pendiente previa")
    path = f"/es/person/{person.pk}/transfer/"
    data = {
        "confirm": "on",
        "manager_version": person.manager_version,
        "target_agency": str(agency.pk),
    }
    old_phone = person.phone_claim_id
    assert subject_client.post(path, data).status_code == 409
    person.refresh_from_db()
    assert person.agency_id is None and person.manager_version == 1
    assert person.phone_claim_id == old_phone and not person.consent_revoked_at
    assert not person.representationaction_set.filter(action="transfer").exists()
    existing.delete()
    assert subject_client.post(path, data).status_code == 302
    assert subject_client.post(path, data).status_code == 302
    person.refresh_from_db()
    assert person.agency_id == agency.pk and person.manager_version == 2
    assert person.representationaction_set.filter(action="transfer").count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_transfers_share_agency_quota(request, settings):
    person, _, _, _, _ = request.getfixturevalue("pending")
    settings.AGENCY_PENDING_PERSON_LIMIT = 1
    agency = Agency.objects.create(
        owner=User.objects.create_user(
            username="quota-target", email="quota-target@example.invalid"
        ),
        name="Destino concurrente",
    )
    subject = User.objects.create_user(
        username="second-subject",
        email="second@example.invalid",
        email_verified_at=person.subject.email_verified_at,
    )
    from apps.core.models import LegalAcceptance

    for acceptance in LegalAcceptance.objects.filter(user=person.subject):
        LegalAcceptance.objects.create(
            user=subject, document=acceptance.document, action=acceptance.action
        )
    second = Person.objects.create(individual=subject, subject=subject, alias="Segunda persona")
    inputs = [(person.pk, person.subject), (second.pk, subject)]
    barrier = Barrier(2)

    def transfer(item):
        close_old_connections()
        try:
            client = Client()
            client.force_login(item[1])
            barrier.wait(timeout=5)
            return client.post(
                f"/es/person/{item[0]}/transfer/",
                {"confirm": "on", "manager_version": 1, "target_agency": str(agency.pk)},
            ).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(transfer, inputs))
    assert sorted(outcomes) == [302, 409]
    assert agency.people.count() == 1
