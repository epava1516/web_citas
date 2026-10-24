from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import Client
from django.utils import timezone

from apps.catalog.models import Municipality, PostalCode, Zone
from apps.core.models import LegalAcceptance, LegalDocument, Person, PhoneClaim, User
from apps.listings.models import Listing, Rate, Revision


@pytest.fixture
def scenario(transactional_db):
    call_command("bootstrap")
    call_command("seed_catalog")
    user = User.objects.create_user(
        username="draft-owner",
        email="draft@example.invalid",
        password="Long-draft-password!847",
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
    person = Person.objects.create(individual=user, subject=user, alias="Persona demo")
    claim = PhoneClaim.objects.create(
        individual=user, phone="+34600444555", verified_at=timezone.now()
    )
    person.phone_claim = claim
    person.save()
    client = Client()
    client.force_login(user)
    return user, person, client


def details(revision, **changes):
    city = Municipality.objects.get(code="demo-south")
    return {
        "edit_version": str(revision.edit_version),
        "title": "Perfil para compartir fotografía y planes románticos",
        "description": "Me gustaría conocer a alguien para compartir fotografía y planes culturales.",
        "content_language": "es",
        "description_alternative": "I would like to meet someone who enjoys photography and cultural activities.",
        "profile_type": "woman",
        "region": city.province.region_id,
        "province": city.province_id,
        "municipality": city.pk,
        "postal_code": PostalCode.objects.get(code="29001").pk,
        "zone": Zone.objects.get(municipality=city).pk,
        "spoken_languages": ["es", "en"],
        "days": ["1", "3"],
        "time_slot": "morning",
        **changes,
    }


def contacts(revision, **changes):
    return {
        "edit_version": revision.edit_version,
        "contact_exposure_accepted": "on",
        "accept_publishing": "on",
        "legal_version": LegalDocument.objects.get(slug="publishing", language="es", active=True).version,
        "whatsapp": "on",
        "telegram": "demo_model",
        **changes,
    }


def test_wizard_persists_profile_and_contact_without_service_rates(scenario):
    user, person, client = scenario
    response = client.post(f"/es/person/{person.pk}/listing/start/")
    assert response.status_code == 302
    revision = Revision.objects.get()
    response = client.post(response.url, details(revision))
    assert response.status_code == 302, response.context["form"].errors
    revision.refresh_from_db()
    assert (
        revision.municipality.code == "demo-south" and revision.categories.get().slug == "romantic-dating"
    )
    assert revision.spoken_languages == ["es", "en"]
    response = client.post(f"/es/draft/{revision.pk}/2/", contacts(revision, phone="+34999999999"))
    assert response.status_code == 302
    revision.refresh_from_db()
    assert revision.phone == person.phone_claim.phone
    assert revision.publisher_acceptance.user_id == user.pk
    assert not Rate.objects.exists() and not revision.services.exists()
    page = client.get(f"/es/draft/{revision.pk}/4/")
    assert b"Tarifas" not in page.content and revision.title.encode() in page.content
    assert (
        Listing.objects.get().status == "draft"
        and Listing.objects.get().approved_revision_id is None
    )
    client.post(f"/es/person/{person.pk}/listing/start/")
    assert Listing.objects.count() == Revision.objects.count() == 1


@pytest.mark.parametrize(
    "concept",
    ["https://external.invalid", "www.external.invalid", "@synthetic_contact", "+34999999999"],
)
def test_tariff_cannot_publish_unverified_contact(scenario, concept):
    _, _, client = scenario
    person = scenario[1]
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    assert client.post(f"/es/draft/{revision.pk}/1/", details(revision)).status_code == 302
    revision.refresh_from_db()
    version = revision.edit_version
    response = client.post(
        f"/es/draft/{revision.pk}/2/", contacts(revision, **{"rates-0-concept": concept})
    )
    assert response.status_code == 400
    revision.refresh_from_db()
    assert revision.edit_version == version
    assert not Rate.objects.filter(revision=revision).exists()


def test_invalid_geography_service_contact_and_version(scenario):
    user, person, client = scenario
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    path = f"/es/draft/{revision.pk}/1/"
    north = Municipality.objects.get(code="demo-north")
    assert client.post(path, details(revision, municipality=north.pk)).status_code == 400
    assert (
        client.post(
            path, details(revision, services=["untrusted-service"])
        ).status_code
        == 400
    )
    assert (
        client.post(
            path, details(revision, description="Contact https://external.invalid")
        ).status_code
        == 400
    )
    assert client.post(path, details(revision, description="x" * 6001)).status_code == 400
    assert client.post(path, details(revision)).status_code == 302
    assert client.post(path, details(revision, title="Stale tab")).status_code == 409
    revision.refresh_from_db()
    assert revision.title != "Stale tab"
    contact_path = f"/es/draft/{revision.pk}/2/"
    assert (
        client.post(
            contact_path, contacts(revision, **{"rates-0-mode": "fixed", "rates-0-amount": ""})
        ).status_code
        == 400
    )
    assert client.post(contact_path, contacts(revision, legal_version="old")).status_code == 400
    person.phone_claim = None
    person.save()
    assert client.post(contact_path, contacts(revision)).status_code == 400
    assert not Rate.objects.exists()


def test_private_drafts_csrf_obsolete_manager_and_quota(scenario):
    user, person, client = scenario
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    stranger = User.objects.create_user(
        username="stranger", email="stranger@example.invalid", email_verified_at=timezone.now()
    )
    other = Client()
    other.force_login(stranger)
    for acceptance in LegalAcceptance.objects.filter(user=user):
        LegalAcceptance.objects.create(
            user=stranger, document=acceptance.document, action=acceptance.action
        )
    assert other.get(f"/es/draft/{revision.pk}/1/").status_code == 404
    assert client.get(f"/es/draft/{revision.pk}/1/")["Cache-Control"] == "private, no-store"
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(user)
    assert strict.post(f"/es/draft/{revision.pk}/1/", details(revision)).status_code == 403
    person.manager_version += 1
    person.save()
    assert client.post(f"/es/draft/{revision.pk}/1/", details(revision)).status_code == 404
    Revision.objects.create(
        listing=revision.listing, manager_version=person.manager_version, status="pending"
    )
    Revision.objects.create(
        listing=revision.listing, manager_version=person.manager_version, status="pending"
    )
    response = client.post(f"/es/person/{person.pk}/listing/start/")
    assert response.status_code == 302
    new_revision = Revision.objects.get(
        listing=revision.listing, status="draft", manager_version=person.manager_version
    )
    assert new_revision.source_revision_id != revision.pk
    assert new_revision.source_revision.manager_version == person.manager_version
    new_revision.status = "pending"
    new_revision.save(update_fields=["status"])
    assert client.post(f"/es/person/{person.pk}/listing/start/").status_code == 409


def test_concurrent_start_keeps_one_listing_and_draft(scenario):
    user, person, _ = scenario
    barrier = Barrier(2)

    def create():
        close_old_connections()
        try:
            client = Client()
            client.force_login(user)
            barrier.wait(timeout=5)
            return client.post(f"/es/person/{person.pk}/listing/start/").status_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(lambda _: create(), range(2))) == [302, 302]
    assert Listing.objects.count() == Revision.objects.count() == 1


def test_consult_amount_and_database_fixed_null_rejected(scenario):
    from django.db import IntegrityError, transaction

    _, person, client = scenario
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    assert (
        client.post(
            f"/es/draft/{revision.pk}/2/", contacts(revision, **{"rates-0-amount": "50"})
        ).status_code
        == 400
    )
    with pytest.raises(IntegrityError), transaction.atomic():
        Rate.objects.create(revision=revision, concept="Invalid", mode="fixed", amount=None)
    assert not Rate.objects.exists()
