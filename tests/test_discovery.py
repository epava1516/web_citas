import io

import pytest
from directory_snapshot import seed_or_restore
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
    seed_or_restore(
        lambda: call_command(
            "seed_demo", credentials_file=str(tmp_path / "credentials.json"), stdout=io.StringIO()
        )
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
    assert not publication_ready(person)
    check.procedure = "age-v1"
    check.save(update_fields=["procedure"])
    assert publication_ready(person)
    agency_person = Person.objects.get(subject__username="fixture-v1-model-a")
    agency_person.verificationcheck_set.update(provider="future-provider")
    agency_person.phone_claim.verification_procedure = "sms-v1"
    agency_person.phone_claim.save(update_fields=["verification_procedure"])
    assert not publication_ready(agency_person)


@pytest.mark.django_db(transaction=True)
def test_geography_checks_postal_and_zone_ancestry_without_selected_city(directory):
    from apps.catalog.models import Zone

    north = Municipality.objects.get(code="demo-north")
    south = Municipality.objects.get(code="demo-south")
    postal = PostalCode.objects.get(code="29001")
    zone = Zone.objects.filter(municipality=south).first()
    assert zone is not None
    for child in [{"postal_code": [postal.pk]}, {"zone": [zone.pk]}]:
        for parent in [
            {"region": [north.province.region_id]},
            {"province": [north.province_id]},
            {"city": [north.pk]},
        ]:
            assert directory.get("/en/", child | parent).status_code == 400
        assert (
            directory.get("/en/", child | {"region": [south.province.region_id]}).status_code == 200
        )
        assert directory.get("/en/", child | {"city": [north.pk, south.pk]}).status_code == 200


@pytest.fixture
def multipage_directory(directory):
    """Valid synthetic public snapshots; this fixture does not exercise image matching."""
    import hashlib

    from django.core.files.base import ContentFile
    from PIL import Image

    from apps.core.management.commands.seed_demo import demo_image
    from apps.core.models import RepresentationAction, User, VerificationCheck
    from apps.listings.models import Listing
    from apps.mediafiles.models import Blob, Photo

    template = Person.objects.get(subject__username="fixture-v1-model-a")
    source = template.listing.approved_revision
    stamp = timezone.now()
    document = source.publisher_acceptance.document
    for index in range(25):
        subject = User.objects.create_user(
            username=f"search-page-{index}", email=f"search-page-{index}@example.invalid"
        )
        person = Person.objects.create(
            alias=f"Pagination subject {index}",
            agency=template.agency,
            subject=subject,
            phone_claim=template.phone_claim,
            consent_version=1,
            age_status="passed",
        )
        RepresentationAction.objects.create(
            person=person, subject=subject, manager_version=1, action="grant", document=document
        )
        VerificationCheck.objects.create(
            person=person, subject=subject, manager_version=1, provider="simulator", status="passed"
        )
        listing = Listing.objects.create(
            person=person,
            status="published",
            published_at=stamp,
            expires_at=stamp + timezone.timedelta(days=30),
        )
        revision = Revision.objects.create(
            listing=listing,
            manager_version=1,
            status="approved",
            title=f"Pagination portrait {index}",
            description="Synthetic pagination portfolio for professional photography and cultural events.",
            municipality=source.municipality,
            phone=source.phone,
            contact_exposure_accepted=True,
            publisher_acceptance=source.publisher_acceptance,
        )
        revision.categories.set(source.categories.all())
        revision.services.set(source.services.all())
        raw = demo_image(820000 + index)
        blob = Blob.objects.create(sha256=hashlib.sha256(raw).hexdigest(), status="ready")
        image = Image.open(io.BytesIO(raw))
        output = io.BytesIO()
        image.save(output, format="WEBP")
        blob.derivative.save(f"pagination-{index}.webp", ContentFile(output.getvalue()))
        Photo.objects.create(revision=revision, blob=blob, approved=True, comparison_complete=True)
        listing.approved_revision = revision
        listing.save(update_fields=["approved_revision"])
    return directory


@pytest.mark.django_db(transaction=True)
def test_positive_pagination_has_no_duplicates_stable_ties_and_private_counts(multipage_directory):
    client = multipage_directory
    query = {"q": "pagination", "channel": ["phone"], "services_mode": "any"}
    first = client.get("/en/", query)
    second = client.get("/en/", query | {"page": "2"})
    assert first.status_code == second.status_code == 200
    assert first.context["page"].paginator.count == 25
    ids = [item.pk for response in [first, second] for item in response.context["page"].object_list]
    assert len(ids) == len(set(ids)) == 25
    assert ids == sorted(ids)
    assert [item.pk for item in client.get("/en/", query).context["page"].object_list] == ids[:24]
    assert b"q=pagination" in first.content and b"channel=phone" in first.content
    person = Person.objects.get(listing__pk=ids[0])
    person.consent_revoked_at = timezone.now()
    person.save(update_fields=["consent_revoked_at"])
    assert client.get("/en/", query).context["page"].paginator.count == 24
    assert client.get("/en/", query | {"page": "2"}).status_code == 404
    assert str(ids[0]).encode() not in client.get("/en/", query).content


@pytest.mark.django_db(transaction=True)
def test_search_title_weight_precedes_newer_description_and_private_text(directory):
    from datetime import timedelta

    from apps.listings.models import Listing

    individual = Person.objects.get(individual__username="fixture-v1-individual").listing
    agency = Person.objects.get(subject__username="fixture-v1-model-a").listing
    Revision.objects.filter(pk=individual.approved_revision_id).update(
        title="Portrait specialist",
        description="Synthetic professional photography and cultural events.",
        description_alternative="",
    )
    Revision.objects.filter(pk=agency.approved_revision_id).update(
        title="Photography specialist",
        description="Synthetic portrait photography and cultural events.",
        description_alternative="",
    )
    Listing.objects.filter(pk=individual.pk).update(published_at=timezone.now() - timedelta(days=2))
    Listing.objects.filter(pk=agency.pk).update(published_at=timezone.now())
    response = directory.get("/en/", {"q": "portrait"})
    assert [item.pk for item in response.context["page"].object_list] == [individual.pk, agency.pk]
    Revision.objects.create(
        listing=agency,
        manager_version=1,
        title="HiddenExclusiveTerm",
        description="Private unapproved material",
    )
    assert directory.get("/en/", {"q": "HiddenExclusiveTerm"}).context["page"].paginator.count == 0


@pytest.mark.django_db(transaction=True)
def test_specific_real_checks_exclude_simulated_or_obsolete_proofs(directory, settings):
    from apps.core.models import VerificationCheck

    assert (
        directory.get("/en/", {"checked": ["age", "contact", "agency"]})
        .context["page"]
        .paginator.count
        == 0
    )
    assert directory.get("/en/", {"checked": ["complete"]}).status_code == 400
    person = Person.objects.get(individual__username="fixture-v1-individual")
    check = person.verificationcheck_set.latest("created_at")
    settings.VERIFICATION_PROVIDER = "future-provider"
    check.provider = "future-provider"
    check.save(update_fields=["provider"])
    assert directory.get("/en/", {"checked": ["age"]}).context["page"].paginator.count == 0
    check.procedure = "age-v1"
    check.save(update_fields=["procedure"])
    assert directory.get("/en/", {"checked": ["age"]}).context["page"].paginator.count == 1
    assert directory.get("/en/", {"checked": ["contact"]}).context["page"].paginator.count == 0
    assert (
        directory.get("/en/", {"checked": ["age", "agency"]}).context["page"].paginator.count == 1
    )
    assert (
        directory.get("/en/", {"checked": ["age"], "q": "absent-term"})
        .context["page"]
        .paginator.count
        == 0
    )
    VerificationCheck.objects.create(
        person=person,
        subject=person.subject,
        manager_version=person.manager_version,
        provider="simulator",
        status="passed",
    )
    assert directory.get("/en/", {"checked": ["age"]}).context["page"].paginator.count == 0


@pytest.mark.django_db(transaction=True)
def test_contact_and_agency_checks_are_specific_and_require_current_evidence(directory):
    person = Person.objects.get(subject__username="fixture-v1-model-a")
    phone = person.phone_claim
    phone.verification_procedure = "sms-v1"
    phone.save(update_fields=["verification_procedure"])
    response = directory.get("/en/", {"checked": ["contact"]})
    assert response.context["page"].paginator.count == 1
    assert (
        b"Contact control confirmed" in response.content and b"Age: simulated" in response.content
    )
    assert directory.get("/en/", {"checked": ["agency"]}).context["page"].paginator.count == 0
    person.agency.verification_procedure = "organization-v1"
    person.agency.save(update_fields=["verification_procedure"])
    assert directory.get("/en/", {"checked": ["agency"]}).context["page"].paginator.count == 1
    phone.verified_at = None
    phone.save(update_fields=["verified_at"])
    assert (
        directory.get("/en/", {"checked": ["contact", "agency"]}).context["page"].paginator.count
        == 0
    )
