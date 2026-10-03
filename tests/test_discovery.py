import io

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Municipality, PostalCode, Service
from apps.core.models import Person
from apps.listings.models import Revision


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
