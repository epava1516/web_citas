import uuid

import pytest
from django.core import mail, signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from apps.core.models import (
    Agency,
    LegalAcceptance,
    LegalDocument,
    Person,
    PhoneClaim,
    RepresentationAction,
    User,
    VerificationEvent,
)
from apps.core.verification_services import (
    publication_ready,
    receive_event,
    simulate_event,
    start_age_check,
)


@pytest.fixture
def ready_accounts(transactional_db, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")


def account(name, agency=False):
    user = User.objects.create_user(
        username=name,
        email=f"{name}@example.invalid",
        password="Long-test-password!873",
        email_verified_at=timezone.now(),
        role="agency" if agency else "visitor",
        mfa_enabled=agency,
        mfa_version=1 if agency else 0,
    )
    for document in LegalDocument.objects.filter(
        active=True, language="es", slug__in=["terms", "privacy"]
    ):
        LegalAcceptance.objects.create(
            user=user,
            document=document,
            action="account_terms" if document.slug == "terms" else "privacy_notice",
        )
    client = Client()
    client.force_login(user)
    if agency:
        session = client.session
        session["mfa_version"] = user.mfa_version
        session.save()
    return user, client


def phone(client, person, number):
    response = client.post(f"/es/person/{person.pk}/phone/", {"phone": number})
    assert response.status_code == 302
    code = mail.outbox[-1].body
    return client.post(response.url, {"code": code})


def test_individual_prerequisites_persistence_phone_replay(ready_accounts):
    user, client = account("individual")
    assert client.post("/es/person/create/", {"alias": "Persona sintética"}).status_code == 302
    person = Person.objects.get()
    assert person.subject_id == user.pk
    assert not publication_ready(person)
    assert (
        client.post(
            f"/es/person/{person.pk}/consent/", {"authorize": "on", "version": "dev-1"}
        ).status_code
        == 302
    )
    person.refresh_from_db()
    assert not publication_ready(person)
    assert client.post(f"/es/person/{person.pk}/age/", {"outcome": "pending"}).status_code == 302
    person.refresh_from_db()
    assert not publication_ready(person)
    client.post(f"/es/person/{person.pk}/age/", {"outcome": "failed"})
    person.refresh_from_db()
    assert person.age_status == "failed" and not publication_ready(person)
    client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"})
    assert phone(client, person, "600 111 222").status_code == 302
    person.refresh_from_db()
    assert person.phone_claim.phone == "+34600111222"
    assert publication_ready(person)
    assert (
        b"Requisitos locales completos"
        in client.get(f"/es/person/{person.pk}/verification/").content
    )
    assert client.post("/es/person/create/", {"alias": "Duplicate"}).status_code == 302
    assert Person.objects.count() == 1
    challenge = person.phonechallenge_set.get()
    assert (
        client.post(
            f"/es/phone/{challenge.pk}/confirm/", {"code": mail.outbox[-1].body}
        ).status_code
        == 400
    )
    assert client.post(f"/es/person/{person.pk}/revoke/").status_code == 302
    person.refresh_from_db()
    assert not publication_ready(person)
    assert RepresentationAction.objects.filter(person=person, action="revoke").count() == 1


def test_agency_direct_consent_shared_phone_and_transfer(ready_accounts):
    owner, owner_client = account("agency-owner", agency=True)
    target_owner, target_client = account("other-agency", agency=True)
    subject, subject_client = account("represented")
    stranger, stranger_client = account("stranger")
    agency = Agency.objects.create(owner=owner, name="First")
    target = Agency.objects.create(owner=target_owner, name="Second")
    person = Person.objects.create(agency=agency, alias="Model A")
    other = Person.objects.create(agency=agency, alias="Model B")
    assert (
        owner_client.post(
            f"/es/person/{person.pk}/consent/invite/", {"email": subject.email}
        ).status_code
        == 302
    )
    invitation_path = mail.outbox[-1].body.removeprefix("http://localhost:8000")
    assert (
        stranger_client.post(invitation_path, {"authorize": "on", "version": "dev-1"}).status_code
        == 403
    )
    assert subject_client.get(invitation_path).status_code == 200
    person.refresh_from_db()
    assert person.subject_id is None
    assert (
        subject_client.post(invitation_path, {"authorize": "on", "version": "old"}).status_code
        == 200
    )
    assert (
        subject_client.post(invitation_path, {"authorize": "on", "version": "dev-1"}).status_code
        == 302
    )
    assert (
        subject_client.post(invitation_path, {"authorize": "on", "version": "dev-1"}).status_code
        == 403
    )
    assert (
        owner_client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 404
    )
    assert stranger_client.get(f"/es/person/{person.pk}/verification/").status_code == 403
    subject_client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"})
    assert phone(owner_client, person, "+34 600111333").status_code == 302
    assert phone(owner_client, other, "600111333").status_code == 302
    assert PhoneClaim.objects.count() == 1
    third = Person.objects.create(agency=target, alias="Third")
    assert phone(target_client, third, "600111333").status_code == 409
    person.refresh_from_db()
    assert publication_ready(person)
    assert (
        subject_client.post(
            f"/es/person/{person.pk}/transfer/", {"target_agency": str(target.pk), "confirm": "on"}
        ).status_code
        == 302
    )
    person.refresh_from_db()
    assert person.agency_id == target.pk and person.phone_claim_id is None
    assert not publication_ready(person)
    assert owner_client.get(f"/es/person/{person.pk}/verification/").status_code == 403
    assert target_client.get(f"/es/person/{person.pk}/verification/").status_code == 200
    assert Person.objects.filter(subject=subject).count() == 1


def test_events_signed_idempotent_obsolete_and_production_disabled(ready_accounts, settings):
    user, client = account("subject")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic")
    check = start_age_check(person, user)
    payload = simulate_event(check, "passed", uuid.uuid4())
    assert receive_event(payload).status == "passed"
    assert receive_event(payload).status == "passed"
    assert VerificationEvent.objects.count() == 1
    with pytest.raises(signing.BadSignature):
        receive_event(payload + "tampered")
    old = start_age_check(person, user)
    client.post(f"/es/person/{person.pk}/revoke/")
    with pytest.raises(ValidationError):
        receive_event(simulate_event(old, "passed"))
    settings.PRODUCTION = True
    with pytest.raises(PermissionDenied):
        receive_event(payload)
    assert client.post(f"/es/person/{person.pk}/age/", {"outcome": "passed"}).status_code == 503
    assert client.post(f"/es/person/{person.pk}/phone/", {"phone": "600111222"}).status_code == 503


def test_phone_resend_invalidates_previous_and_unauthorized_actor(ready_accounts):
    user, client = account("phone-owner")
    outsider, stranger = account("phone-outsider")
    person = Person.objects.create(individual=user, subject=user, alias="Synthetic")
    first = client.post(f"/es/person/{person.pk}/phone/", {"phone": "600123456"})
    code = mail.outbox[-1].body
    second = client.post(f"/es/person/{person.pk}/phone/", {"phone": "600123456"})
    assert client.post(first.url, {"code": code}).status_code == 400
    assert stranger.post(second.url, {"code": mail.outbox[-1].body}).status_code == 404
    assert client.post(second.url, {"code": mail.outbox[-1].body}).status_code == 302


def test_concurrent_phone_cannot_be_claimed_by_two_individuals(ready_accounts):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    prepared = []
    for name in ["phone-race-a", "phone-race-b"]:
        user, client = account(name)
        person = Person.objects.create(individual=user, subject=user, alias=name)
        response = client.post(f"/es/person/{person.pk}/phone/", {"phone": "600888999"})
        prepared.append((client, response.url, mail.outbox[-1].body))
    barrier = Barrier(2)

    def consume(item):
        close_old_connections()
        try:
            client, path, code = item
            barrier.wait(timeout=5)
            return client.post(path, {"code": code}).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(consume, prepared)) == [302, 409]
    assert PhoneClaim.objects.count() == 1
    assert Person.objects.filter(phone_claim__isnull=False).count() == 1
