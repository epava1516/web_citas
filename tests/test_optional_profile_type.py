"""A profile can publish without declaring a type; absence is never inferred."""

import pytest
from test_discovery import directory  # noqa: F401
from test_drafts import details, scenario  # noqa: F401
from test_listing_moderation import decision, pending  # noqa: F401
from test_photos import photo_environment  # noqa: F401
from test_submissions import prepared  # noqa: F401

from apps.core.models import Person
from apps.listings.discovery import candidates
from apps.listings.moderation import publicly_visible
from apps.listings.public_validation import PublicationContext
from apps.listings.publication_state import refresh_all

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.mark.parametrize("mode", ["omitted", "empty"])
def test_profile_without_declared_type_saves_submits_and_publishes(request, mode):
    _, _, client, revision = request.getfixturevalue("prepared")
    data = details(revision)
    if mode == "omitted":
        data.pop("profile_type")
    else:
        data["profile_type"] = ""
    assert client.post(f"/es/draft/{revision.pk}/1/", data).status_code == 302
    revision.refresh_from_db()
    assert revision.profile_type == ""
    person, _, current, _, reviewer = request.getfixturevalue("pending")
    assert reviewer.post(
        f"/es/moderation/listings/{current.pk}/", decision(current)
    ).status_code == 302
    for language, label in [("es", "Sin indicar"), ("en", "Not specified")]:
        response = client.get(f"/{language}/listing/{person.listing.pk}/")
        assert response.status_code == 200
        assert response.context["public"]["profile_type"] == label
        assert label in response.content.decode()


def test_unspecified_type_is_not_assigned_to_a_selected_type(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    assert revision.profile_type == "woman"  # Explicit synthetic fixture declaration.
    revision.profile_type = ""
    revision.save(update_fields=["profile_type"])
    for refresh in [False, True]:
        if refresh:
            refresh_all()
        assert client.get("/es/").context["page"].paginator.count == 2
        assert client.get("/es/", {"profile": ["woman"]}).context["page"].paginator.count == 1
        assert client.get("/es/", {"profile": [""]}).context["page"].paginator.count == 1
        assert client.get("/es/", {"profile": ["woman", ""]}).context["page"].paginator.count == 2
    context = PublicationContext(candidates({}))
    contextual = {row.pk for row in context.rows if publicly_visible(row, context=context)}
    native = {row.pk for row in candidates({}) if publicly_visible(row)}
    assert contextual == native and person.listing.pk in contextual


def test_optional_does_not_allow_unknown_declared_types(request):
    client = request.getfixturevalue("directory")
    person = Person.objects.get(individual__username="fixture-v1-individual")
    revision = person.listing.approved_revision
    revision.profile_type = "invalid-type"
    revision.save(update_fields=["profile_type"])
    for language in ["es", "en"]:
        assert client.get(f"/{language}/", {"profile": [revision.profile_type]}).status_code == 400
        assert client.get(f"/{language}/listing/{person.listing.pk}/").status_code == 404
