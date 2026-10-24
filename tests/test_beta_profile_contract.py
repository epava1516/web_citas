"""Romantic profile contract, preserved history and public authority boundaries."""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
from test_discovery import directory  # noqa: F401
from test_drafts import contacts, details, scenario  # noqa: F401
from test_photos import photo_environment  # noqa: F401

from apps.catalog.models import Category
from apps.core.models import LegalDocument, Person
from apps.listings.models import Listing, Rate, Revision
from apps.listings.moderation import publicly_visible
from apps.listings.profile_contract import CURRENT_CONTRACT, LEGACY_CONTRACT
from apps.listings.public_validation import PublicationContext
from apps.listings.publication_state import mark_all, refresh_all
from apps.listings.revisions import create_draft

pytestmark = pytest.mark.django_db(transaction=True)


def test_migration_preserves_old_content_and_requires_new_romantic_revision():
    executor = MigrationExecutor(connection)
    latest = executor.loader.graph.leaf_nodes()
    old_target = [node for node in latest if node[0] != "listings"] + [
        ("listings", "0022_restore_conservative_publication_invalidation")
    ]
    try:
        executor.migrate(old_target)
        old = executor.loader.project_state(old_target).apps
        user = old.get_model("core", "User").objects.create(
            username="old-profile", email="old-profile@example.invalid"
        )
        person = old.get_model("core", "Person").objects.create(
            individual_id=user.pk, subject_id=user.pk, alias="Synthetic old profile"
        )
        listing = old.get_model("listings", "Listing").objects.create(
            person_id=person.pk, status="published", expires_at=timezone.now() + timedelta(days=5)
        )
        revision = old.get_model("listings", "Revision").objects.create(
            listing_id=listing.pk, manager_version=person.manager_version,
            title="Historical professional title", status="approved",
        )
        category = old.get_model("catalog", "Category").objects.create(
            slug="modeling", name_es="Histórico", name_en="Historical"
        )
        revision.categories.add(category)
        rate = old.get_model("listings", "Rate").objects.create(
            revision_id=revision.pk, concept="Historical rate", mode="fixed", amount=Decimal("20")
        )
        listing.approved_revision_id = revision.pk
        listing.save()
        executor = MigrationExecutor(connection)
        executor.migrate(latest)
        current = Revision.objects.get(pk=revision.pk)
        assert current.show_trans_label is False
        assert current.profile_type == "woman"
        assert current.content_contract == LEGACY_CONTRACT
        assert current.title == "Historical professional title"
        assert current.categories.get().pk == category.pk
        assert not Category.objects.get(pk=category.pk).active
        assert Rate.objects.get(pk=rate.pk).amount == Decimal("20")
        owner = Person.objects.get(pk=person.pk)
        target = Listing.objects.get(pk=listing.pk)
        assert not publicly_visible(target)
        with transaction.atomic():
            draft = create_draft(target, owner)
        assert draft.show_trans_label is False
        assert draft.profile_type == ""
        assert draft.content_contract == CURRENT_CONTRACT
        assert draft.source_revision_id is None and draft.title == ""
        assert draft.categories.get().slug == "romantic-dating"
        assert not draft.rates.exists() and not draft.photos.exists()
        current.refresh_from_db()
        assert current.title == "Historical professional title"
        # Reversing the schema preserves records and does not reactivate the catalogue.
        executor = MigrationExecutor(connection)
        executor.migrate(old_target)
        old = executor.loader.project_state(old_target).apps
        assert old.get_model("listings", "Rate").objects.get(pk=rate.pk).amount == Decimal("20")
        assert not old.get_model("catalog", "Category").objects.get(pk=category.pk).active
        assert old.get_model("listings", "Revision").objects.get(pk=revision.pk).profile_type == "woman"
        assert old.get_model("listings", "Revision").objects.get(pk=draft.pk).profile_type == ""
    finally:
        MigrationExecutor(connection).migrate(latest)


@pytest.mark.parametrize("language", ["es", "en"])
def test_panel_reaches_existing_profile_and_omits_professional_fields(request, language):
    bundle = request.getfixturevalue("scenario")
    user, person, client = bundle
    dashboard = client.get(f"/{language}/account/")
    assert dashboard.status_code == 200
    assert dashboard.context["own_profile"].pk == person.pk
    start = client.post(f"/{language}/person/{person.pk}/listing/start/")
    assert start.status_code == 302
    revision = Revision.objects.get(listing__person=person)
    page = client.get(start.url)
    for name in ["categories", "services", "travel_areas", "reception", "travel"]:
        assert f'name="{name}"'.encode() not in page.content
    assert client.post(start.url, details(revision)).status_code == 302
    revision.refresh_from_db()
    contact_path = f"/{language}/draft/{revision.pk}/2/"
    assert b"rates-TOTAL_FORMS" not in client.get(contact_path).content
    assert client.post(contact_path, contacts(revision)).status_code == 302
    dashboard = client.get(f"/{language}/account/")
    assert dashboard.context["own_draft"].pk == revision.pk
    assert Person.objects.filter(individual=user).count() == 1
    assert Listing.objects.filter(person=person).count() == 1
    assert not Rate.objects.exists()


@pytest.mark.parametrize("field", ["categories", "services", "travel", "rates-0-amount"])
def test_professional_post_fields_rejected_without_mutation(request, field):
    bundle = request.getfixturevalue("scenario")
    _, person, client = bundle
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    payload = details(revision) | {field: "untrusted"}
    assert client.post(f"/es/draft/{revision.pk}/1/", payload).status_code == 400
    revision.refresh_from_db()
    assert revision.title == "" and revision.edit_version == 1
    assert not revision.services.exists() and not revision.rates.exists()


@pytest.mark.parametrize("corruption", ["contract", "rate", "category", "travel"])
def test_native_and_stored_publication_reject_incompatible_profile(request, corruption):
    public_client = request.getfixturevalue("directory")
    listing = Listing.objects.filter(status="published").select_related("approved_revision").first()
    assert publicly_visible(listing)
    revision = listing.approved_revision
    if corruption == "contract":
        Revision.objects.filter(pk=revision.pk).update(content_contract=LEGACY_CONTRACT)
    elif corruption == "rate":
        Rate.objects.create(revision=revision, concept="Not a profile field", mode="consult")
    elif corruption == "category":
        revision.categories.clear()
    else:
        Revision.objects.filter(pk=revision.pk).update(travel=True)
    listing.refresh_from_db()
    assert not publicly_visible(listing)
    context = PublicationContext(Listing.objects.filter(pk=listing.pk))
    assert not publicly_visible(context.rows[0], context=context)
    mark_all()
    refresh_all()
    for language in ["es", "en"]:
        page = public_client.get(f"/{language}/")
        assert page.status_code == 200
        assert listing.pk not in [item.pk for item in page.context["page"].object_list]
        assert public_client.get(f"/{language}/listing/{listing.pk}/").status_code == 404
        photo = revision.photos.first()
        assert public_client.get(f"/{language}/listing/{listing.pk}/photo/{photo.pk}/").status_code == 404


@pytest.mark.parametrize("field", ["category", "service", "services_mode", "travel", "reception"])
def test_old_search_parameters_fail_explicitly_instead_of_widening(request, field):
    public_client = request.getfixturevalue("directory")
    response = public_client.get("/es/", {field: "old-value"})
    assert response.status_code == 400
    assert response.context["page"].paginator.count == 0


def test_new_publishing_terms_preserve_previously_accepted_text(request):
    bundle = request.getfixturevalue("scenario")
    from apps.core.models import LegalAcceptance

    user, _, _ = bundle
    previous = LegalDocument.objects.create(
        slug="publishing", language="es", version="old-synthetic", title="Old",
        body="Historical accepted body", active=False, published_at=timezone.now(),
    )
    accepted = LegalAcceptance.objects.create(user=user, document=previous, action="publish")
    call_command("bootstrap")
    previous.refresh_from_db()
    assert previous.body == "Historical accepted body"
    assert LegalAcceptance.objects.get(pk=accepted.pk).document_id == previous.pk
    current = LegalDocument.objects.get(slug="publishing", language="es", active=True)
    assert current.version == "dev-romantic-1"
    assert "citas románticas" in current.body


def test_legacy_edit_cannot_reclassify_saved_history(request):
    bundle = request.getfixturevalue("scenario")
    _, person, client = bundle
    client.post(f"/es/person/{person.pk}/listing/start/")
    revision = Revision.objects.get()
    Revision.objects.filter(pk=revision.pk).update(content_contract=LEGACY_CONTRACT)
    old_url = f"/es/draft/{revision.pk}/1/"
    assert client.get(old_url).status_code == 409
    assert client.post(old_url, details(revision)).status_code == 409
    revision.refresh_from_db()
    assert revision.content_contract == LEGACY_CONTRACT
    assert client.post(f"/es/person/{person.pk}/listing/start/").status_code == 302
    assert Listing.objects.count() == 1
    assert Revision.objects.filter(content_contract=CURRENT_CONTRACT).count() == 1


def test_profile_guard_never_accepts_unknown_contract(request):
    request.getfixturevalue("directory")
    from apps.listings.profile_contract import validate_profile_contract

    revision = Listing.objects.filter(status="published").first().approved_revision
    revision.content_contract = "unrecognized"
    with pytest.raises(ValidationError):
        validate_profile_contract(revision)
