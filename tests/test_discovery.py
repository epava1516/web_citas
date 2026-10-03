import io

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Municipality, PostalCode, Service
from apps.core.models import Person
from apps.listings.models import Rate, Revision


@pytest.fixture
def directory(request, tmp_path, monkeypatch):
    request.getfixturevalue("photo_environment")
    monkeypatch.setenv("DEMO_PASSWORD", "Long-directory-fixture-password!873")
    call_command(
        "seed_demo", credentials_file=str(tmp_path / "credentials.json"), stdout=io.StringIO()
    )
    return Client()


@pytest.mark.django_db(transaction=True)
def test_search_approved_text_language_and_hidden_revisions(directory):
    response = directory.get("/es/", {"q": "photography"})
    assert response.status_code == 200
    assert response.context["page"].paginator.count == 2
    assert b"fixture-model-b@example.invalid" not in response.content
    published = Person.objects.get(individual__username="fixture-v1-individual")
    Revision.objects.create(
        listing=published.listing,
        manager_version=1,
        title="Secret pending phrase",
        description="Confidential private text",
    )
    assert directory.get("/es/", {"q": "confidential"}).context["page"].paginator.count == 0
    published.consent_revoked_at = timezone.now()
    published.save(update_fields=["consent_revoked_at"])
    assert directory.get("/es/", {"q": "photography"}).context["page"].paginator.count == 1
    english = directory.get("/en/")
    assert b"Photography" in english.content and b"Synthetic profile" in english.content
    assert english["Cache-Control"] == "no-store"


@pytest.mark.django_db(transaction=True)
def test_service_any_all_geo_json_and_private_postal_filters(directory):
    photography = Service.objects.get(slug="photography")
    events = Service.objects.get(slug="model-events")
    query = {
        "service": [photography.pk, events.pk],
        "services_mode": "any",
        "language": ["en", "fr"],
    }
    assert directory.get("/es/", query).context["page"].paginator.count == 2
    query["services_mode"] = "all"
    assert directory.get("/es/", query).context["page"].paginator.count == 0
    north = Municipality.objects.get(code="demo-north")
    south = Municipality.objects.get(code="demo-south")
    assert directory.get("/es/", {"city": [north.pk]}).context["page"].paginator.count == 0
    assert (
        directory.get("/es/", {"city": [south.pk], "province": [north.province_id]}).status_code
        == 400
    )
    private = PostalCode.objects.get(code="29001")
    Revision.objects.filter(listing__status="published").update(postal_code=private)
    assert directory.get("/es/", {"postal_code": [private.pk]}).context["page"].paginator.count == 2
    private.public_safe = False
    private.save(update_fields=["public_safe"])
    assert directory.get("/es/", {"postal_code": [private.pk]}).status_code == 400
    assert directory.get("/es/", {"q": "x" * 201}).status_code == 400


@pytest.mark.django_db(transaction=True)
def test_pagination_invalid_and_out_of_range_preserve_filter_semantics(directory):
    assert directory.get("/es/", {"page": "-1"}).status_code == 400
    assert directory.get("/es/", {"page": "9999999"}).status_code == 400
    assert directory.get("/es/", {"page": "2"}).status_code == 404
    assert (
        directory.get("/es/", {"q": "absent-synthetic-term", "page": "1"})
        .context["page"]
        .paginator.count
        == 0
    )


@pytest.mark.django_db(transaction=True)
def test_public_detail_localizes_attributes_rates_and_selected_contacts(directory):
    person = Person.objects.get(individual__username="fixture-v1-individual")
    listing = person.listing
    revision = listing.approved_revision
    revision.whatsapp = True
    revision.telegram = "demo_model"
    revision.postal_code = PostalCode.objects.get(code="29001")
    revision.save()
    Rate.objects.create(
        revision=revision, concept="Photo session", mode="from", amount="75.00", duration_minutes=60
    )
    response = directory.get(f"/en/listing/{listing.pk}/")
    assert response.status_code == 200
    content = response.content.decode()
    for expected in [
        "Synthetic profile",
        'lang="en"',
        "Photography",
        "Spanish, English",
        "Monday, Wednesday",
        "Morning",
        "From",
        "75.00 EUR",
        "60 min",
        "Consult",
        "Age: simulated",
        "Contact: simulated",
        "29001",
    ]:
        assert expected in content
    assert f'href="https://wa.me/{revision.phone.lstrip("+")}"' in content
    assert 'href="https://t.me/demo_model"' in content
    assert person.individual.email not in content
    revision.whatsapp = False
    revision.telegram = ""
    revision.save()
    revision.postal_code.public_safe = False
    revision.postal_code.save(update_fields=["public_safe"])
    assert directory.get(f"/en/listing/{listing.pk}/").status_code == 404
    revision.postal_code = None
    revision.description_alternative = ""
    revision.save()
    response = directory.get(f"/en/listing/{listing.pk}/")
    assert response.status_code == 200
    content = response.content.decode()
    assert 'lang="es"' in content
    assert "29001" not in content and "wa.me/" not in content and "t.me/" not in content


@pytest.mark.django_db(transaction=True)
def test_simulation_provenance_survives_provider_switch_and_blocks_production(directory, settings):
    from apps.core.verification_services import publication_ready

    person = Person.objects.get(individual__username="fixture-v1-individual")
    listing = person.listing
    photo = listing.approved_revision.photos.get()
    settings.VERIFICATION_PROVIDER = "future-provider"
    content = directory.get(f"/en/listing/{listing.pk}/").content
    assert b"Age: simulated" in content and b"Contact: simulated" in content
    settings.PRODUCTION = True
    assert not publication_ready(person)
    assert directory.get(f"/en/listing/{listing.pk}/").status_code == 404
    assert directory.get(f"/en/listing/{listing.pk}/photo/{photo.pk}/").status_code == 404
    assert directory.get("/en/").context["page"].paginator.count == 0
    # Each simulated proof remains insufficient, even after changing another proof's metadata.
    check = person.verificationcheck_set.latest("created_at")
    check.provider = "future-provider"
    check.save(update_fields=["provider"])
    assert not publication_ready(person)
    person.phone_claim.verification_procedure = "sms-v1"
    person.phone_claim.save(update_fields=["verification_procedure"])
    assert publication_ready(person)
    agency_person = Person.objects.get(subject__username="fixture-v1-model-a")
    agency_person.verificationcheck_set.update(provider="future-provider")
    agency_person.phone_claim.verification_procedure = "sms-v1"
    agency_person.phone_claim.save(update_fields=["verification_procedure"])
    assert not publication_ready(agency_person)
