"""Private state guidance must agree with current public authority."""

from datetime import timedelta

import pytest
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.core.models import Person
from apps.listings.models import Revision

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("status,labels", [
    ("draft", ("Borrador privado", "Private draft")),
    ("processing", ("Procesando fotografías", "Processing photographs")),
    ("pending", ("En revisión", "Under review")),
    ("published", ("Publicado", "Published")),
    ("paused", ("En pausa", "Paused")),
    ("expired", ("Caducado", "Expired")),
    ("withdrawn", ("Retirado", "Withdrawn")),
    ("rejected", ("Necesita correcciones", "Needs corrections")),
])
def test_own_profile_explains_publication_state(request, language, status, labels):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    client.force_login(person.individual)
    listing = person.listing
    listing.status = status
    listing.save(update_fields=["status"])
    for path in [f"/{language}/account/", f"/{language}/listing/{listing.pk}/manage/"]:
        response = client.get(path)
        assert response.status_code == 200
        summary = response.context["publication_status"]
        assert summary["label"] == labels[language == "en"]
        assert summary["hint"] and summary["visible"] is (status == "published")
        assert summary["label"] in response.content.decode()


@pytest.mark.parametrize("language", ["es", "en"])
def test_pending_changes_do_not_replace_published_profile_guidance(request, language):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    client.force_login(person.individual)
    revision = Revision.objects.create(
        listing=person.listing, manager_version=person.manager_version, status="pending",
        title="Private synthetic pending changes", description="Private unpublished text",
    )
    response = client.get(f"/{language}/account/")
    assert response.context["publication_status"]["visible"] is True
    assert response.context["own_revision"].pk == revision.pk
    assert response.context["revision_status"]["label"] == (
        "Under review" if language == "en" else "En revisión"
    )
    assert f"/{language}/draft/{revision.pk}/status/" in response.content.decode()
    review = client.get(f"/{language}/draft/{revision.pk}/status/")
    assert review.status_code == 200
    assert response.context["revision_status"]["label"] in review.content.decode()
    public = client.get(f"/{language}/listing/{person.listing.pk}/")
    assert public.status_code == 200 and revision.title not in public.content.decode()


@pytest.mark.parametrize("cause", ["expiry", "consent"])
def test_dashboard_never_claims_visibility_from_stale_published_status(request, cause):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    client.force_login(person.individual)
    listing = person.listing
    if cause == "expiry":
        listing.expires_at = timezone.now() - timedelta(seconds=1)
        listing.save(update_fields=["expires_at"])
    else:
        person.consent_revoked_at = timezone.now()
        person.save(update_fields=["consent_revoked_at"])
    response = client.get("/es/account/")
    assert response.context["own_listing"].status == "published"
    assert response.context["publication_status"]["visible"] is False
    assert b"Ver mi perfil publicado" not in response.content
    assert client.get(f"/es/listing/{listing.pk}/").status_code == 404
