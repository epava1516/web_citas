import re

import pyotp
import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone

from apps.core.agencies import can_manage_person
from apps.core.mfa import decrypt, recovery_digest
from apps.core.models import (
    Agency,
    AgencyInvitation,
    AgencyMember,
    LegalAcceptance,
    LegalDocument,
    Person,
    RecoveryCode,
    User,
)

PASSWORD = "A-secure-person-password!845"


@pytest.fixture
def catalog(transactional_db, settings):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")


def user_account(name):
    user = User.objects.create_user(
        username=name,
        email=f"{name}@example.invalid",
        password=PASSWORD,
        email_verified_at=timezone.now(),
    )
    for doc in LegalDocument.objects.filter(
        active=True, language="es", slug__in=["terms", "privacy"]
    ):
        LegalAcceptance.objects.create(
            user=user,
            document=doc,
            action="account_terms" if doc.slug == "terms" else "privacy_notice",
        )
    return user


def enroll(client, user):
    client.force_login(user)
    assert client.post("/es/account/mfa/enroll/", {"password": PASSWORD}).status_code == 200
    user.refresh_from_db()
    secret = decrypt(user.mfa_secret_encrypted)
    assert secret not in user.mfa_secret_encrypted
    response = client.post(
        "/es/account/mfa/enroll/", {"stage": "confirm", "code": pyotp.TOTP(secret).now()}
    )
    assert response.status_code == 200
    user.refresh_from_db()
    assert user.mfa_enabled
    codes = re.findall(rb"<code>([A-F0-9]{16})</code>", response.content)
    assert len(codes) == 10
    assert all(
        RecoveryCode.objects.filter(user=user, digest=recovery_digest(code.decode())).exists()
        for code in codes
    )
    return [code.decode() for code in codes]


def test_mfa_enrollment_replay_and_recovery(catalog):
    user = user_account("owner")
    client = Client()
    codes = enroll(client, user)
    assert client.get("/es/account/").status_code == 200
    client.post("/es/account/logout/")
    client.post("/es/account/login/", {"email": user.email, "password": PASSWORD})
    assert client.get("/es/account/").url == "/es/account/mfa/"
    used_totp = pyotp.TOTP(decrypt(user.mfa_secret_encrypted)).at(user.mfa_last_counter * 30)
    assert b"Invalid code" in client.post("/es/account/mfa/", {"code": used_totp}).content
    assert client.post("/es/account/mfa/", {"code": codes[0]}).status_code == 302
    assert client.get("/es/account/").status_code == 200
    assert RecoveryCode.objects.get(digest=recovery_digest(codes[0])).used_at
    client.post("/es/account/logout/")
    client.force_login(user)
    response = client.post("/es/account/mfa/", {"code": codes[0]})
    assert response.status_code == 200 and b"Invalid code" in response.content


def test_two_models_editor_scope_and_revocation(catalog):
    owner = user_account("owner")
    editor = user_account("editor")
    outsider = user_account("outsider")
    owner_client, editor_client, outsider_client = Client(), Client(), Client()
    enroll(owner_client, owner)
    enroll(editor_client, editor)
    outsider_client.force_login(outsider)
    response = owner_client.post("/es/agency/create/", {"name": "Agencia sintética"})
    assert response.status_code == 302
    agency = Agency.objects.get(owner=owner)
    assert (
        owner_client.post(
            f"/es/agency/{agency.pk}/people/add/", {"alias": "Modelo Alfa"}
        ).status_code
        == 302
    )
    assert (
        owner_client.post(
            f"/es/agency/{agency.pk}/people/add/", {"alias": "Modelo Beta"}
        ).status_code
        == 302
    )
    people = list(agency.people.order_by("created_at"))
    assert len(people) == 2
    assert (
        owner_client.post(f"/es/agency/{agency.pk}/invite/", {"email": editor.email}).status_code
        == 302
    )
    invitation = AgencyInvitation.objects.get()
    from django.core import mail

    invite_path = mail.outbox[-1].body.removeprefix("http://localhost:8000")
    assert outsider_client.post(invite_path).status_code == 403
    assert editor_client.get(invite_path).status_code == 200
    assert not AgencyMember.objects.exists()
    assert editor_client.post(invite_path).status_code == 302
    membership = AgencyMember.objects.get()
    assert editor_client.post(invite_path).status_code == 403
    assert (
        owner_client.post(
            f"/es/agency/{agency.pk}/people/{people[0].pk}/assign/", {"editor": editor.pk}
        ).status_code
        == 302
    )
    assert can_manage_person(editor, people[0])
    assert not can_manage_person(editor, people[1])
    page = editor_client.get(f"/es/agency/{agency.pk}/")
    assert b"Modelo Alfa" in page.content and b"Modelo Beta" not in page.content
    assert (
        editor_client.post(f"/es/agency/{agency.pk}/people/add/", {"alias": "No"}).status_code
        == 404
    )
    assert outsider_client.get(f"/es/agency/{agency.pk}/").status_code == 403
    assert (
        owner_client.post(f"/es/agency/{agency.pk}/members/{membership.pk}/revoke/").status_code
        == 302
    )
    assert not can_manage_person(editor, people[0])
    assert editor_client.get(f"/es/agency/{agency.pk}/").status_code == 403
    invitation.refresh_from_db()
    assert invitation.accepted_at


def test_agency_requires_mfa_and_cannot_assign_outside_member(catalog):
    user, other = user_account("owner"), user_account("other")
    client = Client()
    client.force_login(user)
    assert client.post("/es/agency/create/", {"name": "Agency"}).url == "/es/account/mfa/enroll/"
    assert not Agency.objects.exists()
    enroll(client, user)
    client.post("/es/agency/create/", {"name": "Agency"})
    agency = Agency.objects.get()
    person = Person.objects.create(agency=agency, alias="Synthetic")
    response = client.post(
        f"/es/agency/{agency.pk}/people/{person.pk}/assign/", {"editor": other.pk}
    )
    assert b"Select a valid choice" in response.content or b"opci" in response.content
    person.refresh_from_db()
    assert person.assigned_editor is None


@pytest.mark.django_db(transaction=True)
def test_concurrent_recovery_code_one_use(settings):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from django.db import close_old_connections, connections

    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    call_command("bootstrap")
    user = user_account("race")
    codes = enroll(Client(), user)
    barrier = Barrier(2)

    def consume():
        close_old_connections()
        try:
            client = Client()
            client.force_login(user)
            barrier.wait(timeout=5)
            return client.post("/es/account/mfa/", {"code": codes[0]}).status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: consume(), range(2))) == [200, 302]
    assert RecoveryCode.objects.filter(user=user, used_at__isnull=False).count() == 1


def test_agency_quota_counts_unapproved_current_manager_and_owner_scope(catalog, settings):
    from apps.core.agencies import person_queryset
    from apps.listings.models import Listing, Revision

    settings.AGENCY_PENDING_PERSON_LIMIT = 2
    owner = user_account("quota-owner")
    client = Client()
    enroll(client, owner)
    agency = Agency.objects.create(owner=owner, name="Cuota sintética")
    for index in range(2):
        member = user_account(f"quota-editor-{index}")
        AgencyMember.objects.create(agency=agency, user=member)
    approved_person = Person.objects.create(agency=agency, alias="Aprobada")
    listing = Listing.objects.create(person=approved_person, status="paused")
    revision = Revision.objects.create(listing=listing, manager_version=1, status="approved")
    listing.approved_revision = revision
    listing.save(update_fields=["approved_revision"])
    assert person_queryset(owner).get(pk=approved_person.pk) == approved_person
    url = f"/es/agency/{agency.pk}/people/add/"
    assert client.post(url, {"alias": "Pendiente uno"}).status_code == 302
    assert client.post(url, {"alias": "Pendiente dos"}).status_code == 302
    assert client.post(url, {"alias": "Exceso"}).status_code == 409
    assert agency.people.count() == 3
    pending = agency.people.get(alias="Pendiente uno")
    pending_listing = Listing.objects.create(person=pending)
    pending_revision = Revision.objects.create(
        listing=pending_listing, manager_version=1, status="approved"
    )
    pending_listing.approved_revision = pending_revision
    pending_listing.save(update_fields=["approved_revision"])
    assert client.post(url, {"alias": "Nuevo pendiente"}).status_code == 302
    approved_person.manager_version = 2
    approved_person.save(update_fields=["manager_version"])
    assert client.post(url, {"alias": "Gestor antiguo no libera cuota"}).status_code == 409
    assert not agency.people.filter(alias="Gestor antiguo no libera cuota").exists()
